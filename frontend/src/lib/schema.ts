import yaml from 'js-yaml';
import type { Edge, Node } from '@xyflow/react';
import type { SchemaClass, SchemaEnum, SchemaModel, Slot } from '../types';

const primitiveRanges = new Set(['string', 'integer', 'float', 'boolean', 'anyURI']);

export function emptySchema(): SchemaModel {
  return {
    id: 'https://w3id.org/construct-dcat/profile',
    name: 'construct_dcat_profile',
    title: 'Construct-DCAT Application Profile',
    prefixes: {
      dcat: 'http://www.w3.org/ns/dcat#',
      dcterms: 'http://purl.org/dc/terms/',
      skos: 'http://www.w3.org/2004/02/skos/core#',
      prov: 'http://www.w3.org/ns/prov#',
      foaf: 'http://xmlns.com/foaf/0.1/',
      aas: 'https://admin-shell.io/aas/3/0/',
      bot: 'https://w3id.org/bot#',
      ifc: 'https://standards.buildingsmart.org/IFC/DEV/IFC4/ADD2_TC1/OWL#',
      cx: 'https://w3id.org/cx#',
      xsd: 'http://www.w3.org/2001/XMLSchema#',
    },
    imports: ['linkml:types'],
    default_prefix: 'cx',
    default_range: 'string',
    types: {
      anyURI: {
        uri: 'xsd:anyURI',
        base: 'str',
      },
    },
    classes: {},
    slots: {},
    enums: {},
  };
}

export function normalizeSchema(input: SchemaModel): SchemaModel {
  const schema = { ...emptySchema(), ...input };
  return {
    ...schema,
    classes: schema.classes ?? {},
    slots: schema.slots ?? {},
    enums: schema.enums ?? {},
  };
}

export function enumValues(value: SchemaModel['enums'][string] | undefined): string[] {
  if (!value) return [];
  if (Array.isArray(value.permissible_values)) return value.permissible_values;
  return Object.keys(value.permissible_values ?? {});
}

function uniqueName(base: string, existing: Set<string>) {
  if (!existing.has(base)) return base;
  let index = 2;
  while (existing.has(`${base}${index}`)) index += 1;
  return `${base}${index}`;
}

function appendUnique(values: string[], value: string) {
  if (!values.includes(value)) values.push(value);
}

function mergePrefixes(base: Record<string, string> = {}, incoming: Record<string, string> = {}) {
  const prefixes = { ...base };

  Object.entries(incoming).forEach(([prefix, namespace]) => {
    if (!prefixes[prefix] || prefixes[prefix] === namespace) {
      prefixes[prefix] = namespace;
      return;
    }

    let index = 2;
    while (prefixes[`${prefix}${index}`]) index += 1;
    prefixes[`${prefix}${index}`] = namespace;
  });

  return prefixes;
}

function uriLookup<T extends { class_uri?: string; slot_uri?: string }>(
  items: Record<string, T>,
  uriKey: 'class_uri' | 'slot_uri',
) {
  return Object.fromEntries(
    Object.entries(items)
      .filter(([, value]) => value[uriKey])
      .map(([name, value]) => [value[uriKey], name]),
  );
}

function mergedEnum(existing: SchemaEnum | undefined, incoming: SchemaEnum): SchemaEnum {
  const values = [...enumValues(existing), ...enumValues(incoming)];
  return {
    ...existing,
    ...incoming,
    permissible_values: Object.fromEntries([...new Set(values)].map((value) => [value, null])),
  };
}

function remapSlot(slot: Slot, classNameMap: Record<string, string>, enumNameMap: Record<string, string>): Slot {
  return {
    ...slot,
    range: classNameMap[slot.range] ?? enumNameMap[slot.range] ?? slot.range,
  };
}

function mergeSlot(existing: Slot | undefined, incoming: Slot): Slot {
  if (!existing) return incoming;

  return {
    ...incoming,
    ...existing,
    description: existing.description ?? incoming.description,
    slot_uri: existing.slot_uri ?? incoming.slot_uri,
    range: existing.range && existing.range !== 'string' ? existing.range : incoming.range,
    required: existing.required || incoming.required || undefined,
    multivalued: existing.multivalued || incoming.multivalued || undefined,
  };
}

function remapClass(classDef: SchemaClass, classNameMap: Record<string, string>, slotNameMap: Record<string, string>) {
  return {
    ...classDef,
    is_a: classDef.is_a ? classNameMap[classDef.is_a] ?? classDef.is_a : undefined,
    slots: (classDef.slots ?? []).map((slotName) => slotNameMap[slotName] ?? slotName),
  };
}

function mergeClass(existing: SchemaClass | undefined, incoming: SchemaClass): SchemaClass {
  if (!existing) return incoming;

  const slots = [...(existing.slots ?? [])];
  (incoming.slots ?? []).forEach((slotName) => appendUnique(slots, slotName));

  return {
    ...incoming,
    ...existing,
    description: existing.description ?? incoming.description,
    class_uri: existing.class_uri ?? incoming.class_uri,
    is_a: existing.is_a ?? incoming.is_a,
    slots,
  };
}

export function mergeSchemas(baseInput: SchemaModel, incomingInput: SchemaModel): SchemaModel {
  const base = normalizeSchema(baseInput);
  const incoming = normalizeSchema(incomingInput);
  const classNames = new Set(Object.keys(base.classes));
  const slotNames = new Set(Object.keys(base.slots));
  const enumNames = new Set(Object.keys(base.enums));
  const classUriNames = uriLookup(base.classes, 'class_uri');
  const slotUriNames = uriLookup(base.slots, 'slot_uri');

  const classNameMap: Record<string, string> = {};
  const slotNameMap: Record<string, string> = {};
  const enumNameMap: Record<string, string> = {};

  Object.entries(incoming.classes).forEach(([name, classDef]) => {
    const existingByUri = classDef.class_uri ? classUriNames[classDef.class_uri] : undefined;
    const nextName = existingByUri ?? uniqueName(name, classNames);
    classNameMap[name] = nextName;
    classNames.add(nextName);
  });

  Object.entries(incoming.enums).forEach(([name]) => {
    const nextName = uniqueName(name, enumNames);
    enumNameMap[name] = nextName;
    enumNames.add(nextName);
  });

  Object.entries(incoming.slots).forEach(([name, slot]) => {
    const existingByUri = slot.slot_uri ? slotUriNames[slot.slot_uri] : undefined;
    const nextName = existingByUri ?? uniqueName(name, slotNames);
    slotNameMap[name] = nextName;
    slotNames.add(nextName);
  });

  const merged: SchemaModel = {
    ...base,
    prefixes: mergePrefixes(base.prefixes, incoming.prefixes),
    imports: [...new Set([...(base.imports ?? []), ...(incoming.imports ?? [])])],
    types: { ...(base.types ?? {}), ...(incoming.types ?? {}) },
    classes: structuredClone(base.classes),
    slots: structuredClone(base.slots),
    enums: structuredClone(base.enums),
  };

  Object.entries(incoming.enums).forEach(([name, enumDef]) => {
    const nextName = enumNameMap[name];
    merged.enums[nextName] = mergedEnum(merged.enums[nextName], enumDef);
  });

  Object.entries(incoming.slots).forEach(([name, slot]) => {
    const nextName = slotNameMap[name];
    const nextSlot = remapSlot(slot, classNameMap, enumNameMap);
    merged.slots[nextName] = mergeSlot(merged.slots[nextName], nextSlot);
  });

  Object.entries(incoming.classes).forEach(([name, classDef]) => {
    const nextName = classNameMap[name];
    const nextClass = remapClass(classDef, classNameMap, slotNameMap);
    merged.classes[nextName] = mergeClass(merged.classes[nextName], nextClass);
  });

  return merged;
}

export function serializeOntologySchema(schema: SchemaModel): string {
  const cleanEnums = Object.fromEntries(
    Object.entries(schema.enums ?? {}).map(([name, enumDef]) => [
      name,
      {
        permissible_values: Object.fromEntries(enumValues(enumDef).map((value) => [value, null])),
      },
    ]),
  );

  const doc: Record<string, unknown> = {
    id: schema.id,
    name: schema.name,
    title: schema.title,
    description: schema.description,
    prefixes: schema.prefixes,
    imports: schema.imports,
    default_prefix: schema.default_prefix,
    default_range: schema.default_range,
    annotations: schema.annotations,
    classes: schema.classes,
    slots: schema.slots,
    enums: cleanEnums,
  };
  if (schema.types) {
    doc.types = schema.types;
  }

  return yaml.dump(doc, {
    lineWidth: 100,
    noRefs: true,
    sortKeys: false,
  });
}

export function schemaToRdfTurtle(schemaInput: SchemaModel): string {
  const schema = normalizeSchema(schemaInput);
  const lines = prefixLines(schema, ['rdf', 'rdfs', 'owl', 'xsd']);

  Object.entries(schema.classes).forEach(([className, classDef]) => {
    const subject = classResource(className, classDef, schema);
    lines.push(`${subject} a owl:Class .`);
    if (classDef.is_a && schema.classes[classDef.is_a]) {
      lines.push(`${subject} rdfs:subClassOf ${classResource(classDef.is_a, schema.classes[classDef.is_a], schema)} .`);
    }
  });

  Object.entries(schema.slots).forEach(([slotName, slotDef]) => {
    const subject = slotResource(slotName, slotDef, schema);
    lines.push(`${subject} a rdf:Property .`);

    Object.entries(schema.classes).forEach(([className, classDef]) => {
      if (inheritedSlots(className, schema).includes(slotName)) {
        lines.push(`${subject} rdfs:domain ${classResource(className, classDef, schema)} .`);
      }
    });

    lines.push(`${subject} rdfs:range ${rangeResource(slotDef.range ?? 'string', schema)} .`);
  });

  return `${lines.join('\n')}\n`;
}

export function schemaToShaclTurtle(schemaInput: SchemaModel): string {
  const schema = normalizeSchema(schemaInput);
  const lines = prefixLines(schema, ['rdf', 'rdfs', 'sh', 'xsd']);

  Object.entries(schema.classes).forEach(([className, classDef]) => {
    const target = classResource(className, classDef, schema);
    const shape = resourceWithSuffix(target, 'Shape');
    lines.push(`${shape} a sh:NodeShape ;`);
    lines.push(`  sh:targetClass ${target} .`);

    inheritedSlots(className, schema).forEach((slotName) => {
      const slotDef = schema.slots[slotName];
      if (!slotDef) return;

      const constraints = [`    sh:path ${slotResource(slotName, slotDef, schema)}`];
      if (slotDef.required) constraints.push('    sh:minCount 1');
      if (!slotDef.multivalued) constraints.push('    sh:maxCount 1');

      const range = slotDef.range ?? 'string';
      if (schema.classes[range]) {
        constraints.push(`    sh:class ${classResource(range, schema.classes[range], schema)}`);
      } else if (schema.enums[range]) {
        constraints.push(`    sh:in (${enumValues(schema.enums[range]).map(turtleLiteral).join(' ')})`);
      } else {
        constraints.push(`    sh:datatype ${datatypeResource(range) ?? 'xsd:string'}`);
      }

      lines.push(`${shape} sh:property [`);
      lines.push(constraints.map((constraint, index) => (index === constraints.length - 1 ? constraint : `${constraint} ;`)).join('\n'));
      lines.push('  ] .');
    });
  });

  return `${lines.join('\n')}\n`;
}

function prefixLines(schema: SchemaModel, requiredPrefixes: string[]) {
  const prefixes: Record<string, string> = {
    rdf: 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    rdfs: 'http://www.w3.org/2000/01/rdf-schema#',
    owl: 'http://www.w3.org/2002/07/owl#',
    sh: 'http://www.w3.org/ns/shacl#',
    xsd: 'http://www.w3.org/2001/XMLSchema#',
    ...(schema.prefixes ?? {}),
  };

  requiredPrefixes.forEach((prefix) => {
    if (!prefixes[prefix]) {
      prefixes[prefix] = emptySchema().prefixes?.[prefix] ?? '';
    }
  });

  return Object.entries(prefixes)
    .filter(([, uri]) => uri)
    .map(([prefix, uri]) => `@prefix ${prefix}: <${uri}> .`)
    .concat('');
}

function classResource(className: string, classDef: SchemaClass, schema: SchemaModel) {
  return resourceFor(classDef.class_uri, className, schema);
}

function slotResource(slotName: string, slotDef: Slot, schema: SchemaModel) {
  return resourceFor(slotDef.slot_uri, slotName, schema);
}

function resourceFor(uri: string | undefined, fallbackName: string, schema: SchemaModel) {
  if (uri) return formatResource(uri);
  const defaultPrefix = schema.default_prefix && schema.prefixes?.[schema.default_prefix] ? schema.default_prefix : 'ex';
  return `${defaultPrefix}:${fallbackName}`;
}

function rangeResource(range: string, schema: SchemaModel) {
  if (schema.classes[range]) return classResource(range, schema.classes[range], schema);
  return datatypeResource(range) ?? 'rdfs:Literal';
}

function datatypeResource(range: string) {
  return {
    string: 'xsd:string',
    integer: 'xsd:integer',
    float: 'xsd:float',
    boolean: 'xsd:boolean',
    anyURI: 'xsd:anyURI',
  }[range];
}

function formatResource(value: string) {
  if (value.startsWith('http://') || value.startsWith('https://')) return `<${value}>`;
  return value;
}

function resourceWithSuffix(value: string, suffix: string) {
  if (value.startsWith('<') && value.endsWith('>')) {
    return `${value.slice(0, -1)}${suffix}>`;
  }
  return `${value}${suffix}`;
}

function inheritedSlots(className: string, schema: SchemaModel, seen = new Set<string>()): string[] {
  if (seen.has(className)) return [];
  seen.add(className);

  const classDef = schema.classes[className];
  if (!classDef) return [];

  const parentSlots = classDef.is_a && schema.classes[classDef.is_a] ? inheritedSlots(classDef.is_a, schema, seen) : [];
  return [...parentSlots, ...(classDef.slots ?? [])];
}

function turtleLiteral(value: string) {
  return JSON.stringify(value);
}

export function schemaToFlow(schema: SchemaModel, positions: Record<string, { x: number; y: number }>) {
  const classNames = Object.keys(schema.classes);
  const nodes: Node[] = classNames.map((className, index) => ({
    id: className,
    type: 'classNode',
    draggable: true,
    selectable: true,
    position: positions[className] ?? {
      x: 80 + (index % 3) * 320,
      y: 80 + Math.floor(index / 3) * 260,
    },
    data: {
      label: className,
      classDef: schema.classes[className],
      slots: schema.classes[className].slots ?? [],
      slotDefs: schema.slots,
    },
  }));

  const edges: Edge[] = [];
  classNames.forEach((className) => {
    const classDef = schema.classes[className];
    if (classDef.is_a && schema.classes[classDef.is_a]) {
      edges.push({
        id: `${className}-inherits-${classDef.is_a}`,
        source: className,
        target: classDef.is_a,
        type: 'smoothstep',
        label: 'is_a',
        animated: true,
        style: { stroke: '#7c3aed' },
      });
    }

    (classDef.slots ?? []).forEach((slotName) => {
      const range = schema.slots[slotName]?.range;
      if (range && schema.classes[range] && !primitiveRanges.has(range)) {
        edges.push({
          id: `${className}-slot-${slotName}-${range}`,
          source: className,
          target: range,
          type: 'smoothstep',
          label: slotName,
          style: { stroke: '#0f766e' },
        });
      }
    });
  });

  return { nodes, edges };
}
