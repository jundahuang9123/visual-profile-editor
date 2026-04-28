import { Trash2 } from 'lucide-react';
import { enumValues } from '../lib/schema';
import { useEditorStore } from '../store';

const primitives = ['string', 'anyURI', 'integer', 'float', 'boolean'];

export function Inspector() {
  const schema = useEditorStore((state) => state.schema);
  const selected = useEditorStore((state) => state.selected);
  const setSelected = useEditorStore((state) => state.setSelected);
  const updateClass = useEditorStore((state) => state.updateClass);
  const deleteClass = useEditorStore((state) => state.deleteClass);
  const addSlot = useEditorStore((state) => state.addSlot);
  const updateSlot = useEditorStore((state) => state.updateSlot);
  const removeSlotFromClass = useEditorStore((state) => state.removeSlotFromClass);
  const updateEnum = useEditorStore((state) => state.updateEnum);
  const deleteEnum = useEditorStore((state) => state.deleteEnum);

  const classNames = Object.keys(schema.classes);
  const enumNames = Object.keys(schema.enums);
  const ranges = [...primitives, ...classNames, ...enumNames];

  if (!selected) {
    return (
      <aside className="inspector">
        <h2>Inspector</h2>
        <p className="muted">Select a class, property, or enum to edit it.</p>
        <div className="list">
          {classNames.map((name) => (
            <button key={name} onClick={() => setSelected({ kind: 'class', id: name })}>
              {name}
            </button>
          ))}
        </div>
      </aside>
    );
  }

  if (selected.kind === 'class') {
    const classDef = schema.classes[selected.id];
    if (!classDef) return null;
    return (
      <aside className="inspector">
        <h2>Class</h2>
        <label>
          Name
          <input
            value={selected.id}
            onChange={(event) =>
              updateClass(selected.id, {
                name: event.target.value,
                description: classDef.description,
                is_a: classDef.is_a,
              })
            }
          />
        </label>
        <label>
          Description
          <textarea
            className="small-textarea"
            value={classDef.description ?? ''}
            onChange={(event) =>
              updateClass(selected.id, {
                name: selected.id,
                description: event.target.value,
                is_a: classDef.is_a,
              })
            }
          />
        </label>
        <label>
          Inherits from
          <select
            value={classDef.is_a ?? ''}
            onChange={(event) =>
              updateClass(selected.id, {
                name: selected.id,
                description: classDef.description,
                is_a: event.target.value,
              })
            }
          >
            <option value="">None</option>
            {classNames
              .filter((name) => name !== selected.id)
              .map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
          </select>
        </label>
        <div className="section-title">
          <span>Properties</span>
          <button onClick={() => addSlot(selected.id)}>Add</button>
        </div>
        <div className="slot-list">
          {(classDef.slots ?? []).map((slotName) => (
            <div className="slot-row" key={slotName}>
              <button onClick={() => setSelected({ kind: 'slot', id: slotName, classId: selected.id })}>
                {slotName}
              </button>
              <button className="icon-button" onClick={() => removeSlotFromClass(selected.id, slotName)}>
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <button className="danger" onClick={() => deleteClass(selected.id)}>
          Delete class
        </button>
      </aside>
    );
  }

  if (selected.kind === 'slot') {
    const slot = schema.slots[selected.id];
    if (!slot) return null;
    return (
      <aside className="inspector">
        <h2>Property</h2>
        <label>
          Name
          <input
            value={selected.id}
            onChange={(event) =>
              updateSlot(selected.id, {
                name: event.target.value,
                range: slot.range,
                required: Boolean(slot.required),
                multivalued: Boolean(slot.multivalued),
              })
            }
          />
        </label>
        <label>
          Range
          <select
            value={slot.range}
            onChange={(event) =>
              updateSlot(selected.id, {
                name: selected.id,
                range: event.target.value,
                required: Boolean(slot.required),
                multivalued: Boolean(slot.multivalued),
              })
            }
          >
            {ranges.map((range) => (
              <option key={range} value={range}>
                {range}
              </option>
            ))}
          </select>
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            checked={Boolean(slot.required)}
            onChange={(event) =>
              updateSlot(selected.id, {
                name: selected.id,
                range: slot.range,
                required: event.target.checked,
                multivalued: Boolean(slot.multivalued),
              })
            }
          />
          Required
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            checked={Boolean(slot.multivalued)}
            onChange={(event) =>
              updateSlot(selected.id, {
                name: selected.id,
                range: slot.range,
                required: Boolean(slot.required),
                multivalued: event.target.checked,
              })
            }
          />
          Multivalued
        </label>
      </aside>
    );
  }

  const enumDef = schema.enums[selected.id];
  if (!enumDef) return null;
  return (
    <aside className="inspector">
      <h2>Enum</h2>
      <label>
        Name
        <input
          value={selected.id}
          onChange={(event) => updateEnum(selected.id, event.target.value, enumValues(enumDef))}
        />
      </label>
      <label>
        Values
        <textarea
          className="small-textarea tall"
          value={enumValues(enumDef).join('\n')}
          onChange={(event) => updateEnum(selected.id, selected.id, event.target.value.split('\n'))}
        />
      </label>
      <button className="danger" onClick={() => deleteEnum(selected.id)}>
        Delete enum
      </button>
    </aside>
  );
}
