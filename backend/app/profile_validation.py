from __future__ import annotations

from typing import Any

PRIMITIVE_RANGES = {'string', 'integer', 'float', 'boolean', 'anyURI'}


def validate_profile(schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[dict[str, str]] = []

    prefixes = schema.get('prefixes') or {}
    classes = schema.get('classes') or {}
    slots = schema.get('slots') or {}
    enums = schema.get('enums') or {}

    for class_name, class_def in classes.items():
        kind = annotation_value(class_def, 'term_kind') or infer_kind(class_def, 'class_uri')
        class_uri = class_def.get('class_uri')
        profile_of = annotation_value(class_def, 'profile_of')

        if not class_uri and not profile_of:
            errors.append(issue('error', 'MISSING_CLASS_URI', f'{class_name} needs class_uri or profile_of.', f'classes.{class_name}'))

        check_curie(class_uri, prefixes, errors, f'classes.{class_name}.class_uri')
        check_curie(profile_of, prefixes, errors, f'classes.{class_name}.annotations.profile_of')

        parent = class_def.get('is_a')
        if parent and parent not in classes:
            errors.append(issue('error', 'UNDEFINED_PARENT', f'{class_name} inherits from undefined class {parent}.', f'classes.{class_name}.is_a'))

        for slot_name in class_def.get('slots', []) or []:
            if slot_name not in slots:
                errors.append(issue('error', 'UNDEFINED_SLOT', f'{class_name} references undefined property {slot_name}.', f'classes.{class_name}.slots'))

        if kind == 'extension':
            if class_uri and not str(class_uri).startswith('cx:') and not str(class_uri).startswith('https://w3id.org/cx#'):
                warnings.append(issue('warning', 'EXTENSION_OUTSIDE_CX', f'{class_name} is an extension outside the cx namespace.', f'classes.{class_name}.class_uri'))
            extension_documentation_checks(class_name, class_def, warnings, suggestions, 'classes')

        if kind == 'profile' and not profile_of:
            warnings.append(issue('warning', 'PROFILE_WITHOUT_BASE', f'{class_name} is a profile term without profile_of.', f'classes.{class_name}'))

    for slot_name, slot_def in slots.items():
        kind = annotation_value(slot_def, 'term_kind') or infer_kind(slot_def, 'slot_uri')
        slot_uri = slot_def.get('slot_uri')
        profile_of = annotation_value(slot_def, 'profile_of')
        slot_range = slot_def.get('range', 'string')

        if not slot_uri and not profile_of:
            errors.append(issue('error', 'MISSING_PROPERTY_URI', f'{slot_name} needs slot_uri or profile_of.', f'slots.{slot_name}'))

        check_curie(slot_uri, prefixes, errors, f'slots.{slot_name}.slot_uri')
        check_curie(profile_of, prefixes, errors, f'slots.{slot_name}.annotations.profile_of')

        if slot_range not in PRIMITIVE_RANGES and slot_range not in classes and slot_range not in enums:
            errors.append(issue('error', 'UNDEFINED_RANGE', f'{slot_name} has undefined range {slot_range}.', f'slots.{slot_name}.range'))

        if requirement_level(slot_def) == 'mandatory' and not slot_def.get('required') and annotation_value(slot_def, 'min_count') in (None, '', '0'):
            warnings.append(issue('warning', 'MANDATORY_WITHOUT_MIN_COUNT', f'{slot_name} is mandatory but has no required/minCount constraint.', f'slots.{slot_name}'))

        if not slot_def.get('multivalued', False) and annotation_value(slot_def, 'max_count') in (None, ''):
            suggestions.append(issue('suggestion', 'IMPLICIT_MAX_COUNT', f'{slot_name} is single-valued; generated SHACL will use maxCount 1.', f'slots.{slot_name}'))

        if kind == 'extension':
            if slot_uri and not str(slot_uri).startswith('cx:') and not str(slot_uri).startswith('https://w3id.org/cx#'):
                warnings.append(issue('warning', 'EXTENSION_OUTSIDE_CX', f'{slot_name} is an extension outside the cx namespace.', f'slots.{slot_name}.slot_uri'))
            extension_documentation_checks(slot_name, slot_def, warnings, suggestions, 'slots')

        if kind == 'profile' and not profile_of:
            warnings.append(issue('warning', 'PROFILE_WITHOUT_BASE', f'{slot_name} is a property profile without profile_of.', f'slots.{slot_name}'))

        if 'semanticAnchor'.lower() in slot_name.lower() and not annotation_value(slot_def, 'recommended_vocabulary'):
            warnings.append(issue('warning', 'SEMANTIC_ANCHOR_WITHOUT_VOCABULARY', f'{slot_name} should name recommended anchor vocabularies.', f'slots.{slot_name}.annotations'))

    return {
        'valid': not errors,
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions,
    }


def check_curie(value: Any, prefixes: dict[str, Any], errors: list[dict[str, str]], path: str) -> None:
    if not isinstance(value, str) or not value or value.startswith(('http://', 'https://')):
        return
    if ':' not in value:
        return
    prefix = value.split(':', 1)[0]
    if prefix not in prefixes:
        errors.append(issue('error', 'UNKNOWN_PREFIX', f'Prefix {prefix} is used but not declared.', path, f'Add {prefix} to profile prefixes.'))


def extension_documentation_checks(
    name: str,
    definition: dict[str, Any],
    warnings: list[dict[str, str]],
    suggestions: list[dict[str, str]],
    section: str,
) -> None:
    if not definition.get('title'):
        suggestions.append(issue('suggestion', 'MISSING_TITLE', f'{name} should have a human-readable title.', f'{section}.{name}.title'))
    if not definition.get('description'):
        suggestions.append(issue('suggestion', 'MISSING_DESCRIPTION', f'{name} should describe the extension term.', f'{section}.{name}.description'))
    if not annotation_value(definition, 'usage_note'):
        warnings.append(issue('warning', 'MISSING_USAGE_NOTE', f'{name} should include a usage note.', f'{section}.{name}.annotations.usage_note'))


def annotation_value(definition: dict[str, Any], key: str) -> Any:
    annotations = definition.get('annotations') or {}
    value = annotations.get(key)
    if isinstance(value, dict):
        return value.get('value')
    return value


def requirement_level(definition: dict[str, Any]) -> str:
    return str(annotation_value(definition, 'requirement_level') or '').lower()


def infer_kind(definition: dict[str, Any], uri_key: str) -> str:
    uri = str(definition.get(uri_key) or '')
    if uri.startswith('cx:') or uri.startswith('https://w3id.org/cx#'):
        return 'extension'
    return 'base'


def issue(severity: str, code: str, message: str, path: str, suggested_fix: str = '') -> dict[str, str]:
    item = {
        'severity': severity,
        'code': code,
        'message': message,
        'path': path,
    }
    if suggested_fix:
        item['suggested_fix'] = suggested_fix
    return item
