import yaml from 'js-yaml';
import type { Edge, Node } from '@xyflow/react';
import type { SchemaModel } from '../types';

const primitiveRanges = new Set(['string', 'integer', 'float', 'boolean', 'anyURI']);

export function emptySchema(): SchemaModel {
  return {
    id: 'https://example.org/linkml/construct-dcat',
    name: 'construct_dcat',
    title: 'Construct-DCAT extension',
    prefixes: {
      cx: 'https://example.org/construct-dcat/',
      dcat: 'http://www.w3.org/ns/dcat#',
    },
    imports: ['dcat_ap_base'],
    default_prefix: 'cx',
    default_range: 'string',
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

export function serializeConstructSchema(schema: SchemaModel): string {
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
    prefixes: schema.prefixes,
    imports: schema.imports,
    default_prefix: schema.default_prefix,
    default_range: schema.default_range,
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

export function schemaToFlow(schema: SchemaModel, positions: Record<string, { x: number; y: number }>) {
  const classNames = Object.keys(schema.classes);
  const nodes: Node[] = classNames.map((className, index) => ({
    id: className,
    type: 'classNode',
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
