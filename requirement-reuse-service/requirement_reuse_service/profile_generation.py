"""RQ2: requirements-driven DCAT-AP profile generation.

Pipeline (each stage reviewable, nothing merged silently):

    Approved RQ1 RequirementSet
            -> ProfileChangeSet           (generate_profile_changes)
            -> LinkML profile draft       (generate_profile_draft)
            -> SHACL shapes               (generate_shacl_from_changes)
            -> RQ2 export package         (build_rq2_package)
            -> visual editor merge        (explicit user action in the UI)

RQ2 consumes approved RQ1 requirements only; it never re-runs extraction and
never mutates the active profile. Every generated profile element carries
provenance back to requirement ids and evidence unit ids.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import (
    CandidateRequirement,
    GenerateProfileChangesRequest,
    GenerateProfileDraftRequest,
    ProfileChange,
    ProfileChangeSet,
    ProfileGenerationResponse,
    ProvenanceMappingEntry,
    RQ2ExportRequest,
    RQ2Package,
)
from .term_registry import (
    BASE_CLASSES,
    EXTENSION_PREFIX,
    NAMESPACES,
    compact,
    domain_compatible,
    expand,
    is_extension_term,
    is_known_term,
    normalize_resource_type,
    range_for,
    slot_name_for,
    sort_terms_by_priority,
    term_info,
    vocabulary_label,
)

ACTION_TO_CHANGE_TYPE = {
    'reuse_existing_term': 'reuse_property',
    'specialize_existing_term': 'specialize_property',
    'create_extension': 'create_extension_property',
    'add_constraint': 'add_constraint',
    'add_usage_note': 'add_usage_note',
}

OBLIGATION_RANK = {'mandatory': 3, 'recommended': 2, 'optional': 1, 'unknown': 0}

VALUE_KIND_TO_RANGE = {
    'literal': 'string',
    'uri': 'anyURI',
    'controlled_concept': 'SkosConcept',
    'class_reference': 'anyURI',
    'date': 'datetime',
    'agent': 'FoafAgent',
    'distribution': 'DcatDistribution',
    'unknown': 'string',
}

URI_RANGES = {'anyURI', 'SkosConcept', 'FoafAgent', 'DcatDistribution', 'SemanticAnchor', 'ConstructionAsset'}

SHACL_SEVERITY = {'mandatory': 'sh:Violation', 'recommended': 'sh:Warning', 'optional': 'sh:Info', 'unknown': 'sh:Warning'}

DEFAULT_MULTIVALUED_TERMS = {
    'dcat:keyword',
    'dcat:theme',
    'dcat:distribution',
    'cx:semanticAnchor',
    'cx:hasAASSubmodel',
    'cx:hasIFCEntity',
    'cx:usesOntology',
    'cx:describesAssetType',
}


def generate_profile_changes(request: GenerateProfileChangesRequest) -> ProfileChangeSet:
    """Convert reviewed requirements into a reviewable ProfileChangeSet."""
    from .service import stable_id

    source_set_id = request.requirement_set.id if request.requirement_set else None
    requirements = list(request.requirement_set.requirements) if request.requirement_set else list(request.requirements)

    warnings: list[str] = []
    if request.approved_only:
        selected = [requirement for requirement in requirements if requirement.status == 'approved']
        skipped = len(requirements) - len(selected)
        if skipped:
            warnings.append(f'{skipped} requirement(s) were not approved and were excluded from profile generation.')
    else:
        selected = [requirement for requirement in requirements if requirement.status not in {'rejected', 'merged'}]
        warnings.append('approved_only=false: unreviewed candidate requirements were included.')

    if not selected:
        warnings.append('No approved requirements available; the change set is empty.')

    unverified = [
        requirement.id
        for requirement in selected
        if requirement.provenance is not None and requirement.provenance.evidence_verified is False
    ]
    if unverified:
        warnings.append(f'{len(unverified)} approved requirement(s) lack verified evidence: {", ".join(unverified[:6])}')
    without_actions = [requirement.id for requirement in selected if not requirement.candidate_metadata_actions]
    if without_actions:
        warnings.append(f'{len(without_actions)} approved requirement(s) have no candidate metadata actions: {", ".join(without_actions[:6])}')

    changes: list[ProfileChange] = []
    # Dedupe key: (resource, slot_name) -> existing change (duplicate requirements share one slot).
    slot_index: dict[tuple[str, str], ProfileChange] = {}

    for requirement in selected:
        for action in requirement.candidate_metadata_actions:
            if action.action == 'no_action':
                continue
            resource = normalize_resource_type(action.target_class) or normalize_resource_type(
                requirement.normalized_intent.resource_type
            )
            if resource not in BASE_CLASSES:
                warnings.append(
                    f"Requirement {requirement.id}: target class '{action.target_class or requirement.normalized_intent.resource_type}' "
                    'is not a profilable DCAT class (Dataset/Distribution/Catalog/DataService); skipped.'
                )
                continue
            change = build_change(requirement, action, resource, request.profile_prefix, stable_id)
            if change is None:
                continue
            key = (resource, change.slot_name or change.id)
            existing = slot_index.get(key)
            if existing is not None:
                merge_duplicate_change(existing, change)
                continue
            slot_index[key] = change
            changes.append(change)

    needs_review = [change for change in changes if change.review_status == 'needs_review']
    change_set = ProfileChangeSet(
        id=stable_id('chg', source_set_id or 'inline', *(change.id for change in changes[:8])),
        source_requirement_set_id=source_set_id,
        created_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        profile_base=request.base_profile,
        profile_namespace=request.profile_namespace,
        profile_prefix=request.profile_prefix,
        changes=changes,
        warnings=warnings,
        summary_metrics={
            'source_requirement_count': len(requirements),
            'approved_requirement_count': sum(1 for requirement in requirements if requirement.status == 'approved'),
            'change_count': len(changes),
            'needs_review_change_count': len(needs_review),
            'changes_by_type': count_by(changes, lambda change: change.change_type),
            'changes_by_target_class': count_by(changes, lambda change: change.target_class),
        },
    )
    return change_set


def build_change(
    requirement: CandidateRequirement,
    action,
    resource: str,
    profile_prefix: str,
    stable_id,
) -> ProfileChange | None:
    prefixed_class, _, _ = BASE_CLASSES[resource]
    change_type = ACTION_TO_CHANGE_TYPE.get(action.action)
    if change_type is None:
        return None
    if requirement.requirement_scope == 'controlled_vocabulary' and change_type in {'reuse_property', 'specialize_property'}:
        change_type = 'add_controlled_vocabulary'

    hint = action.constraint_hint
    obligation = (hint.obligation if hint else None) or requirement.normalized_intent.obligation_hint
    value_kind = (hint.value_kind if hint and hint.value_kind != 'unknown' else None) or requirement.normalized_intent.value_kind

    candidate_terms = sort_terms_by_priority(action.candidate_terms)
    change_warnings: list[str] = []
    review_status = 'candidate'
    term: str | None = None

    if action.action == 'create_extension':
        term = next((candidate for candidate in candidate_terms if is_extension_term(candidate)), None)
        if term is None:
            bad = next((candidate for candidate in candidate_terms if candidate.strip()), None)
            if bad is not None:
                change_warnings.append(
                    f"Extension proposal uses '{bad}' without the '{EXTENSION_PREFIX}:' prefix; needs review."
                )
            term = f'{profile_prefix}:{derive_slot_name(requirement)}'
            review_status = 'needs_review'
    else:
        term = next((candidate for candidate in candidate_terms if is_known_term(candidate)), None)
        if term is None:
            term = next((candidate for candidate in candidate_terms if candidate.strip()), None)
            if term is None:
                change_warnings.append('No candidate term provided; needs review before generation.')
                term = f'{profile_prefix}:{derive_slot_name(requirement)}'
            else:
                change_warnings.append(f"Candidate term '{term}' is not in the local vocabulary catalogue; needs review.")
            review_status = 'needs_review'
        elif not domain_compatible(term, resource):
            info = term_info(term) or {}
            change_warnings.append(
                f"Term '{term}' has domain {', '.join(info.get('domain') or [])} but targets {prefixed_class}; needs review."
            )
            review_status = 'needs_review'

    slot_name = slot_name_for(term)
    known = is_known_term(term)
    slot_range = range_for(term) if known else VALUE_KIND_TO_RANGE.get(value_kind, 'string')
    cardinality = hint.cardinality if hint else None
    multivalued = parse_multivalued(cardinality, term)
    if hint and hint.datatype_or_class:
        slot_range = hint.datatype_or_class

    return ProfileChange(
        id=stable_id('pchg', requirement.id, action.action, resource, term),
        requirement_id=requirement.id,
        change_type=change_type,  # type: ignore[arg-type]
        target_class=prefixed_class,
        term_uri=expand(term),
        slot_name=slot_name,
        range=slot_range,
        required=obligation == 'mandatory',
        multivalued=multivalued,
        obligation_level=obligation if obligation in OBLIGATION_RANK else 'unknown',  # type: ignore[arg-type]
        rationale=action.rationale or requirement.normalized_statement or '',
        source_vocabulary=vocabulary_label(term),
        evidence_ids=[unit.evidence_unit_id for unit in requirement.source_evidence],
        source_requirement_ids=[requirement.id],
        review_status=review_status,  # type: ignore[arg-type]
        warnings=change_warnings,
    )


def merge_duplicate_change(existing: ProfileChange, incoming: ProfileChange) -> None:
    """Fold a duplicate slot proposal into the existing change (no duplicate slots)."""
    for requirement_id in incoming.source_requirement_ids:
        if requirement_id not in existing.source_requirement_ids:
            existing.source_requirement_ids.append(requirement_id)
    for evidence_id in incoming.evidence_ids:
        if evidence_id not in existing.evidence_ids:
            existing.evidence_ids.append(evidence_id)
    if OBLIGATION_RANK.get(incoming.obligation_level, 0) > OBLIGATION_RANK.get(existing.obligation_level, 0):
        existing.obligation_level = incoming.obligation_level
        existing.required = incoming.required
    existing.warnings.extend(warning for warning in incoming.warnings if warning not in existing.warnings)
    if incoming.review_status == 'needs_review' and existing.review_status == 'candidate':
        existing.review_status = 'needs_review'


def select_changes(change_set: ProfileChangeSet, accepted_only: bool) -> tuple[list[ProfileChange], list[str]]:
    notes: list[str] = []
    accepted = [change for change in change_set.changes if change.review_status == 'accepted']
    if accepted_only:
        included = accepted
        if not accepted:
            notes.append(
                'accepted_only=true but no profile changes are accepted; generated an empty draft and SHACL. '
                'Accept at least one ProfileChange before generating artifacts.'
            )
        candidate_count = sum(1 for change in change_set.changes if change.review_status == 'candidate')
        if candidate_count:
            notes.append(f'{candidate_count} unreviewed candidate change(s) were excluded because accepted_only=true.')
    else:
        included = [change for change in change_set.changes if change.review_status in {'accepted', 'candidate'}]
    excluded_review = [change.id for change in change_set.changes if change.review_status == 'needs_review' and change not in included]
    if excluded_review:
        notes.append(f'{len(excluded_review)} change(s) marked needs_review were excluded: {", ".join(excluded_review[:6])}')
    rejected = sum(1 for change in change_set.changes if change.review_status == 'rejected')
    if rejected:
        notes.append(f'{rejected} rejected change(s) were excluded.')
    return included, notes


def generate_profile_draft(request: GenerateProfileDraftRequest) -> ProfileGenerationResponse:
    """Generate a LinkML profile draft + SHACL from a (reviewed) ProfileChangeSet."""
    change_set = request.profile_change_set
    included, notes = select_changes(change_set, request.accepted_only)
    prefix = change_set.profile_prefix

    classes: dict[str, Any] = {}
    slots: dict[str, Any] = {}
    base_schema_slots = set((request.base_schema or {}).get('slots', {}).keys())
    base_schema_classes = set((request.base_schema or {}).get('classes', {}).keys())

    by_resource: dict[str, list[ProfileChange]] = {}
    for change in included:
        resource = normalize_resource_type(change.target_class)
        if resource is None or resource not in BASE_CLASSES:
            notes.append(f'Change {change.id}: unsupported target class {change.target_class}; skipped.')
            continue
        by_resource.setdefault(resource, []).append(change)

    for resource, resource_changes in by_resource.items():
        prefixed_class, base_linkml, profile_class = BASE_CLASSES[resource]
        if base_linkml not in base_schema_classes and request.base_schema is not None:
            notes.append(
                f"Base class '{base_linkml}' is not present in the supplied base schema; "
                f'the generated {profile_class} will reference it as is_a anyway.'
            )
        class_slots: list[str] = []
        requirement_ids: list[str] = []
        for change in resource_changes:
            slot_name = change.slot_name or slot_name_for(change.term_uri or 'slot')
            if change.change_type == 'add_usage_note':
                # Documentation-only: annotate the class, no slot.
                requirement_ids.extend(change.source_requirement_ids)
                continue
            if slot_name not in class_slots:
                class_slots.append(slot_name)
            requirement_ids.extend(change.source_requirement_ids)
            if slot_name in base_schema_slots:
                notes.append(f"Slot '{slot_name}' already exists in the base schema; the editor merge will combine definitions.")
            if slot_name not in slots:
                slots[slot_name] = build_slot_definition(change, prefix)
            else:
                merge_slot_definition(slots[slot_name], change)

        classes[profile_class] = {
            'title': profile_class_title(resource),
            'is_a': base_linkml,
            'class_uri': f'{prefix}:Construction{resource}',
            'slots': class_slots,
            'annotations': {
                'term_kind': {'value': 'profile'},
                'profile_of': {'value': prefixed_class},
                'profile_base': {'value': change_set.profile_base},
                'generated_from_requirements': {'value': ', '.join(dict.fromkeys(requirement_ids))},
            },
        }

    profile_draft = {
        'id': 'https://w3id.org/construct-dcat/profile/generated-from-requirements',
        'name': 'generated_requirement_profile',
        'title': f'Generated {change_set.profile_base} Profile Extension Draft',
        'description': (
            'Reviewable profile draft generated from approved, evidence-traceable requirements '
            f'(profile change set {change_set.id}). Merge into the visual editor only after review.'
        ),
        'prefixes': {
            'linkml': 'https://w3id.org/linkml/',
            **{key: value for key, value in NAMESPACES.items()},
        },
        'imports': ['linkml:types'],
        'default_prefix': prefix,
        'default_range': 'string',
        'classes': classes,
        'slots': slots,
        'enums': {},
    }
    shacl = generate_shacl_from_changes(change_set, included) if included else ''
    if not included:
        notes.append('No changes were included; the generated draft is empty.')
    return ProfileGenerationResponse(
        profile_change_set=change_set,
        profile_draft=profile_draft,
        shacl=shacl,
        validation_notes=['Review generated artifacts before merging them into the active profile.', *notes],
    )


def build_slot_definition(change: ProfileChange, prefix: str) -> dict[str, Any]:
    term = compact_term(change)
    definition: dict[str, Any] = {
        'title': slot_title(change),
        'slot_uri': term,
        'range': change.range or 'string',
        'annotations': {
            'term_kind': {'value': 'extension' if change.change_type == 'create_extension_property' else 'profile'},
            'source_vocabulary': {'value': change.source_vocabulary or 'unknown'},
            'obligation_level': {'value': change.obligation_level},
            'rationale': {'value': change.rationale[:300]},
            'source_requirement_ids': {'value': ', '.join(change.source_requirement_ids)},
            'source_evidence_ids': {'value': ', '.join(change.evidence_ids[:12])},
            'generated_from_change': {'value': change.id},
        },
    }
    if change.required:
        definition['required'] = True
    if change.multivalued:
        definition['multivalued'] = True
    if change.change_type == 'specialize_property':
        definition['annotations']['specializes'] = {'value': term}
    return definition


def merge_slot_definition(definition: dict[str, Any], change: ProfileChange) -> None:
    annotations = definition.setdefault('annotations', {})
    existing_ids = annotations.get('source_requirement_ids', {}).get('value', '')
    merged = list(dict.fromkeys([*filter(None, existing_ids.split(', ')), *change.source_requirement_ids]))
    annotations['source_requirement_ids'] = {'value': ', '.join(merged)}
    if change.required:
        definition['required'] = True
        annotations['obligation_level'] = {'value': 'mandatory'}


def generate_shacl_from_changes(change_set: ProfileChangeSet, included: list[ProfileChange] | None = None) -> str:
    """Generate class-specific SHACL node shapes from the same change set."""
    if included is None:
        included, _ = select_changes(change_set, accepted_only=True)

    prefix = change_set.profile_prefix
    lines = [
        f'# Generated from profile change set {change_set.id} ({change_set.profile_base} base).',
        '# Each property shape traces back to requirement ids via sh:description.',
        f'@prefix {prefix}: <{change_set.profile_namespace}> .',
        '@prefix dcat: <http://www.w3.org/ns/dcat#> .',
        '@prefix dcterms: <http://purl.org/dc/terms/> .',
        '@prefix skos: <http://www.w3.org/2004/02/skos/core#> .',
        '@prefix prov: <http://www.w3.org/ns/prov#> .',
        '@prefix foaf: <http://xmlns.com/foaf/0.1/> .',
        '@prefix sh: <http://www.w3.org/ns/shacl#> .',
        '',
    ]

    by_resource: dict[str, list[ProfileChange]] = {}
    for change in included:
        resource = normalize_resource_type(change.target_class)
        if resource in BASE_CLASSES:
            by_resource.setdefault(resource, []).append(change)

    for resource, resource_changes in by_resource.items():
        prefixed_class, _, profile_class = BASE_CLASSES[resource]
        property_shapes: list[str] = []
        for change in resource_changes:
            if change.change_type == 'add_usage_note':
                continue
            path = compact_term(change)
            severity = SHACL_SEVERITY.get(change.obligation_level, 'sh:Warning')
            constraints = [f'        sh:path {path} ;']
            if change.obligation_level == 'mandatory':
                constraints.append('        sh:minCount 1 ;')
            if (change.range or '') in URI_RANGES:
                constraints.append('        sh:nodeKind sh:IRI ;')
            constraints.append(f'        sh:severity {severity} ;')
            message = shacl_message(change)
            constraints.append(f'        sh:message "{escape_turtle(message)}" ;')
            constraints.append(
                f'        sh:description "Generated from requirement(s) {", ".join(change.source_requirement_ids)} '
                f'(change {change.id})." ;'
            )
            property_shapes.append('    sh:property [\n' + '\n'.join(constraints) + '\n    ] ;')

        if not property_shapes:
            continue
        lines.append(f'{prefix}:{profile_class}Shape')
        lines.append('    a sh:NodeShape ;')
        lines.append(f'    sh:targetClass {prefixed_class} ;')
        lines.append('\n'.join(property_shapes).rstrip(';').rstrip() + ' .')
        lines.append('')

    return '\n'.join(lines)


def build_rq2_package(request: RQ2ExportRequest) -> RQ2Package:
    generation = generate_profile_draft(
        GenerateProfileDraftRequest(
            profile_change_set=request.profile_change_set,
            base_schema=request.base_schema,
            accepted_only=request.accepted_only,
        )
    )
    included, _ = select_changes(request.profile_change_set, request.accepted_only)
    provenance = [
        ProvenanceMappingEntry(
            requirement_id=requirement_id,
            profile_element=compact_term(change),
            change_id=change.id,
            evidence_unit_ids=change.evidence_ids,
        )
        for change in included
        for requirement_id in change.source_requirement_ids
    ]
    approved_count = request.approved_requirement_count
    if approved_count is None:
        approved_count = int(request.profile_change_set.summary_metrics.get('approved_requirement_count', 0))
    return RQ2Package(
        generated_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        base_profile=request.profile_change_set.profile_base,
        source_requirement_set_id=request.source_requirement_set_id or request.profile_change_set.source_requirement_set_id,
        approved_requirement_count=approved_count,
        profile_change_set=request.profile_change_set,
        profile_draft_linkml=generation.profile_draft,
        shacl=generation.shacl,
        provenance_mapping=provenance,
        warnings=list(request.profile_change_set.warnings),
        validation_notes=generation.validation_notes,
    )


# --- helpers ---------------------------------------------------------------


def derive_slot_name(requirement: CandidateRequirement) -> str:
    words = [word for word in ''.join(
        char if char.isalnum() or char.isspace() else ' ' for char in requirement.normalized_intent.metadata_need
    ).split() if word]
    if not words:
        return 'profileSlot'
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])[:40]


def compact_term(change: ProfileChange) -> str:
    if change.term_uri:
        from .term_registry import compact

        return compact(change.term_uri)
    return f'cx:{change.slot_name or "slot"}'


def parse_multivalued(cardinality: str | None, term: str) -> bool:
    if cardinality:
        normalized = cardinality.strip().lower().replace(' ', '')
        if normalized in {'*', 'n', 'many', 'multiple', 'unbounded'}:
            return True
        if '..' in normalized:
            upper = normalized.split('..', 1)[1]
            if upper in {'*', 'n', 'many', 'multiple', 'unbounded'}:
                return True
            if upper.isdigit():
                return int(upper) > 1
        return normalized.endswith('n')
    return compact(term) in DEFAULT_MULTIVALUED_TERMS


def profile_class_title(resource: str) -> str:
    return f'Construction {resource} Profile'


def slot_title(change: ProfileChange) -> str:
    name = change.slot_name or 'slot'
    spaced = ''.join(f' {char.lower()}' if char.isupper() else char for char in name).strip()
    return spaced[:1].upper() + spaced[1:]


def shacl_message(change: ProfileChange) -> str:
    level = change.obligation_level.capitalize() if change.obligation_level != 'unknown' else 'Review'
    summary = change.rationale.split('.')[0][:140] if change.rationale else f'provide {change.slot_name}'
    return f'{level}: {summary}.'


def escape_turtle(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


def count_by(changes: list[ProfileChange], key) -> dict[str, int]:
    counts: dict[str, int] = {}
    for change in changes:
        counts[key(change)] = counts.get(key(change), 0) + 1
    return counts
