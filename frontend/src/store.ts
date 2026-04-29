import { create } from 'zustand';
import type { Connection, Edge, Node, NodeChange } from '@xyflow/react';
import { applyNodeChanges } from '@xyflow/react';
import type { SchemaModel, SelectedItem } from './types';
import { emptySchema, normalizeSchema, schemaToFlow, serializeConstructSchema } from './lib/schema';

type EditorState = {
  schema: SchemaModel;
  positions: Record<string, { x: number; y: number }>;
  selected: SelectedItem;
  loadSchema: (schema: SchemaModel) => void;
  setSelected: (selected: SelectedItem) => void;
  getFlow: () => { nodes: Node[]; edges: Edge[] };
  onNodesChange: (changes: NodeChange[]) => void;
  connectClasses: (connection: Connection) => void;
  addClass: () => void;
  updateClass: (oldName: string, updates: { name: string; description?: string; is_a?: string }) => void;
  deleteClass: (name: string) => void;
  addSlot: (className: string) => void;
  updateSlot: (oldName: string, updates: { name: string; range: string; required: boolean; multivalued: boolean }) => void;
  removeSlotFromClass: (className: string, slotName: string) => void;
  addEnum: () => void;
  updateEnum: (oldName: string, name: string, values: string[]) => void;
  deleteEnum: (name: string) => void;
  yaml: () => string;
};

function uniqueName(base: string, existing: string[]) {
  if (!existing.includes(base)) return base;
  let index = 2;
  while (existing.includes(`${base}${index}`)) index += 1;
  return `${base}${index}`;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  schema: emptySchema(),
  positions: {},
  selected: null,

  loadSchema: (schema) => set({ schema: normalizeSchema(schema), positions: {}, selected: null }),
  setSelected: (selected) => set({ selected }),
  getFlow: () => schemaToFlow(get().schema, get().positions),

  onNodesChange: (changes) => {
    const current = get().getFlow().nodes;
    const next = applyNodeChanges(changes, current);
    const positions = { ...get().positions };
    next.forEach((node) => {
      positions[node.id] = node.position;
    });
    set({ positions });
  },

  connectClasses: (connection) => {
    if (!connection.source || !connection.target || connection.source === connection.target) return;
    const schema = structuredClone(get().schema);
    const source = schema.classes[connection.source];
    if (!source) return;
    source.is_a = connection.target;
    set({ schema, selected: { kind: 'class', id: connection.source } });
  },

  addClass: () => {
    const schema = structuredClone(get().schema);
    const name = uniqueName('ConstructClass', Object.keys(schema.classes));
    schema.classes[name] = { slots: [] };
    set({
      schema,
      positions: { ...get().positions, [name]: { x: 120, y: 120 } },
      selected: { kind: 'class', id: name },
    });
  },

  updateClass: (oldName, updates) => {
    const schema = structuredClone(get().schema);
    const requestedName = updates.name.trim() || oldName;
    const nextName =
      requestedName === oldName
        ? oldName
        : uniqueName(
            requestedName,
            Object.keys(schema.classes).filter((name) => name !== oldName),
          );
    const classDef = schema.classes[oldName];
    if (!classDef) return;

    classDef.description = updates.description || undefined;
    classDef.is_a = updates.is_a || undefined;

    if (nextName !== oldName) {
      schema.classes[nextName] = classDef;
      delete schema.classes[oldName];
      Object.values(schema.classes).forEach((item) => {
        if (item.is_a === oldName) item.is_a = nextName;
      });
      Object.values(schema.slots).forEach((slot) => {
        if (slot.range === oldName) slot.range = nextName;
      });
      const positions = { ...get().positions, [nextName]: get().positions[oldName] ?? { x: 120, y: 120 } };
      delete positions[oldName];
      set({ schema, positions, selected: { kind: 'class', id: nextName } });
      return;
    }

    set({ schema });
  },

  deleteClass: (name) => {
    const schema = structuredClone(get().schema);
    delete schema.classes[name];
    Object.values(schema.classes).forEach((item) => {
      if (item.is_a === name) delete item.is_a;
    });
    Object.values(schema.slots).forEach((slot) => {
      if (slot.range === name) slot.range = 'string';
    });
    const positions = { ...get().positions };
    delete positions[name];
    set({ schema, positions, selected: null });
  },

  addSlot: (className) => {
    const schema = structuredClone(get().schema);
    const slotName = uniqueName('new_property', Object.keys(schema.slots));
    schema.slots[slotName] = { range: 'string' };
    schema.classes[className].slots = [...(schema.classes[className].slots ?? []), slotName];
    set({ schema, selected: { kind: 'slot', id: slotName, classId: className } });
  },

  updateSlot: (oldName, updates) => {
    const schema = structuredClone(get().schema);
    const requestedName = updates.name.trim() || oldName;
    const nextName =
      requestedName === oldName
        ? oldName
        : uniqueName(
            requestedName,
            Object.keys(schema.slots).filter((name) => name !== oldName),
          );
    const slot = schema.slots[oldName];
    if (!slot) return;
    slot.range = updates.range || 'string';
    slot.required = updates.required || undefined;
    slot.multivalued = updates.multivalued || undefined;

    if (nextName !== oldName) {
      schema.slots[nextName] = slot;
      delete schema.slots[oldName];
      Object.values(schema.classes).forEach((classDef) => {
        classDef.slots = (classDef.slots ?? []).map((slotName) => (slotName === oldName ? nextName : slotName));
      });
      set({ schema, selected: { kind: 'slot', id: nextName } });
      return;
    }

    set({ schema });
  },

  removeSlotFromClass: (className, slotName) => {
    const schema = structuredClone(get().schema);
    const classDef = schema.classes[className];
    if (!classDef) return;
    classDef.slots = (classDef.slots ?? []).filter((item) => item !== slotName);
    const stillUsed = Object.values(schema.classes).some((item) => (item.slots ?? []).includes(slotName));
    if (!stillUsed) delete schema.slots[slotName];
    set({ schema, selected: { kind: 'class', id: className } });
  },

  addEnum: () => {
    const schema = structuredClone(get().schema);
    const name = uniqueName('NewEnum', Object.keys(schema.enums));
    schema.enums[name] = { permissible_values: [] };
    set({ schema, selected: { kind: 'enum', id: name } });
  },

  updateEnum: (oldName, name, values) => {
    const schema = structuredClone(get().schema);
    const requestedName = name.trim() || oldName;
    const nextName =
      requestedName === oldName
        ? oldName
        : uniqueName(
            requestedName,
            Object.keys(schema.enums).filter((enumName) => enumName !== oldName),
          );
    const enumDef = { permissible_values: values.filter(Boolean) };
    schema.enums[nextName] = enumDef;
    if (nextName !== oldName) {
      delete schema.enums[oldName];
      Object.values(schema.slots).forEach((slot) => {
        if (slot.range === oldName) slot.range = nextName;
      });
    }
    set({ schema, selected: { kind: 'enum', id: nextName } });
  },

  deleteEnum: (name) => {
    const schema = structuredClone(get().schema);
    delete schema.enums[name];
    Object.values(schema.slots).forEach((slot) => {
      if (slot.range === name) slot.range = 'string';
    });
    set({ schema, selected: null });
  },

  yaml: () => serializeConstructSchema(get().schema),
}));
