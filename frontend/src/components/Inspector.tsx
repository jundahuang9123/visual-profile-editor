import { Trash2 } from 'lucide-react';
import { annotationValue, requirementLevel, setAnnotation, termKind } from '../lib/profile';
import { enumValues } from '../lib/schema';
import { useEditorStore } from '../store';

const primitives = ['string', 'anyURI', 'integer', 'float', 'boolean'];

export function Inspector() {
  const schema = useEditorStore((state) => state.schema);
  const selected = useEditorStore((state) => state.selected);
  const setSelected = useEditorStore((state) => state.setSelected);
  const updateSchemaMetadata = useEditorStore((state) => state.updateSchemaMetadata);
  const updateClass = useEditorStore((state) => state.updateClass);
  const patchClass = useEditorStore((state) => state.patchClass);
  const createProfileFromClass = useEditorStore((state) => state.createProfileFromClass);
  const deleteClass = useEditorStore((state) => state.deleteClass);
  const addSlot = useEditorStore((state) => state.addSlot);
  const updateSlot = useEditorStore((state) => state.updateSlot);
  const patchSlot = useEditorStore((state) => state.patchSlot);
  const createProfileFromSlot = useEditorStore((state) => state.createProfileFromSlot);
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
        <p className="muted">Select profile metadata, a class profile, property profile, or enum to edit it.</p>
        <div className="section-title">
          <span>Schema</span>
        </div>
        <div className="list">
          <button onClick={() => setSelected({ kind: 'schema', id: 'schema' })}>
            {schema.title || schema.name || 'Profile schema'}
          </button>
        </div>
        <div className="section-title">
          <span>Classes</span>
        </div>
        <div className="list">
          {classNames.map((name) => (
            <button key={name} onClick={() => setSelected({ kind: 'class', id: name })}>
              {name}
              <span className={`term-badge term-badge--${termKind(schema.classes[name], 'class_uri')}`}>
                {termKind(schema.classes[name], 'class_uri').toUpperCase()}
              </span>
            </button>
          ))}
        </div>
        <div className="section-title">
          <span>Enums</span>
        </div>
        <div className="list">
          {enumNames.length === 0 ? (
            <p className="muted">No enums yet.</p>
          ) : (
            enumNames.map((name) => (
              <button key={name} onClick={() => setSelected({ kind: 'enum', id: name })}>
                {name}
              </button>
            ))
          )}
        </div>
      </aside>
    );
  }

  if (selected.kind === 'schema') {
    return (
      <aside className="inspector">
        <h2>Schema</h2>
        <label>
          Description
          <textarea
            className="small-textarea"
            value={schema.description ?? ''}
            onChange={(event) => updateSchemaMetadata({ description: event.target.value })}
          />
        </label>
        <label>
          Title
          <input
            value={schema.title ?? ''}
            onChange={(event) => updateSchemaMetadata({ title: event.target.value })}
          />
        </label>
        <label>
          Name
          <input
            value={schema.name ?? ''}
            onChange={(event) => updateSchemaMetadata({ name: event.target.value })}
          />
        </label>
        <label>
          ID
          <input
            value={schema.id ?? ''}
            onChange={(event) => updateSchemaMetadata({ id: event.target.value })}
          />
        </label>
        <label>
          Default prefix
          <select
            value={schema.default_prefix ?? ''}
            onChange={(event) => updateSchemaMetadata({ default_prefix: event.target.value })}
          >
            <option value="">None</option>
            {Object.keys(schema.prefixes ?? {}).map((prefix) => (
              <option key={prefix} value={prefix}>
                {prefix}
              </option>
            ))}
          </select>
        </label>
        <label>
          Default range
          <select
            value={schema.default_range ?? 'string'}
            onChange={(event) => updateSchemaMetadata({ default_range: event.target.value })}
          >
            {ranges.map((range) => (
              <option key={range} value={range}>
                {range}
              </option>
            ))}
          </select>
        </label>
        <label>
          Prefixes
          <textarea
            className="small-textarea tall"
            value={formatPrefixes(schema.prefixes)}
            onChange={(event) => updateSchemaMetadata({ prefixes: parsePrefixes(event.target.value) })}
          />
        </label>
        <label>
          Imports
          <textarea
            className="small-textarea"
            value={(schema.imports ?? []).join('\n')}
            onChange={(event) => updateSchemaMetadata({ imports: event.target.value.split('\n').map((item) => item.trim()).filter(Boolean) })}
          />
        </label>
      </aside>
    );
  }

  if (selected.kind === 'class') {
    const classDef = schema.classes[selected.id];
    if (!classDef) return null;
    const kind = termKind(classDef, 'class_uri');
    const readOnly = kind === 'base';
    const level = requirementLevel(classDef);
    return (
      <aside className="inspector">
        <div className="inspector-heading">
          <h2>Class / Class Profile</h2>
          <span className={`term-badge term-badge--${kind}`}>{kind.toUpperCase()}</span>
          {level ? <span className={`term-badge term-badge--${level}`}>{level.toUpperCase()}</span> : null}
        </div>
        {readOnly ? <p className="muted">Base vocabulary terms are read-only. Create a profile layer to constrain this class.</p> : null}
        <label>
          Name
          <input
            disabled={readOnly}
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
          Term URI
          <input
            disabled={readOnly}
            value={classDef.class_uri ?? ''}
            onChange={(event) => patchClass(selected.id, { class_uri: event.target.value || undefined })}
          />
        </label>
        <label>
          Profile of
          <input
            disabled={readOnly}
            value={annotationValue(classDef, 'profile_of') ?? ''}
            onChange={(event) => patchClass(selected.id, setAnnotation(classDef, 'profile_of', event.target.value))}
          />
        </label>
        <label>
          Source vocabulary
          <input
            disabled={readOnly}
            value={annotationValue(classDef, 'source_vocabulary') ?? ''}
            onChange={(event) => patchClass(selected.id, setAnnotation(classDef, 'source_vocabulary', event.target.value))}
          />
        </label>
        <label>
          Requirement level
          <select
            disabled={readOnly}
            value={level ?? 'optional'}
            onChange={(event) => patchClass(selected.id, setAnnotation(classDef, 'requirement_level', event.target.value))}
          >
            <option value="mandatory">Mandatory</option>
            <option value="recommended">Recommended</option>
            <option value="optional">Optional</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </label>
        <label>
          Description
          <textarea
            className="small-textarea"
            disabled={readOnly}
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
            disabled={readOnly}
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
        <label>
          Usage note
          <textarea
            className="small-textarea"
            disabled={readOnly}
            value={annotationValue(classDef, 'usage_note') ?? ''}
            onChange={(event) => patchClass(selected.id, setAnnotation(classDef, 'usage_note', event.target.value))}
          />
        </label>
        <div className="section-title">
          <span>Properties / Property Profiles</span>
          <button disabled={readOnly} onClick={() => addSlot(selected.id)}>Add</button>
        </div>
        <div className="slot-list">
          {(classDef.slots ?? []).map((slotName) => (
            <div className="slot-row" key={slotName}>
              <button
                className={schema.slots[slotName]?.required ? 'property-button--required' : undefined}
                onClick={() => setSelected({ kind: 'slot', id: slotName, classId: selected.id })}
              >
                {slotName}
              </button>
              <button className="icon-button" disabled={readOnly} onClick={() => removeSlotFromClass(selected.id, slotName)}>
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        {readOnly ? (
          <button className="primary" onClick={() => createProfileFromClass(selected.id)}>
            Create profile of this class
          </button>
        ) : null}
        <button className="danger" disabled={readOnly} onClick={() => deleteClass(selected.id)}>
          Delete class
        </button>
      </aside>
    );
  }

  if (selected.kind === 'slot') {
    const slot = schema.slots[selected.id];
    if (!slot) return null;
    const kind = termKind(slot, 'slot_uri');
    const readOnly = kind === 'base';
    const level = requirementLevel(slot);
    return (
      <aside className="inspector">
        <div className="inspector-heading">
          <h2>Property / Property Profile</h2>
          <span className={`term-badge term-badge--${kind}`}>{kind.toUpperCase()}</span>
          {level ? <span className={`term-badge term-badge--${level}`}>{level.toUpperCase()}</span> : null}
        </div>
        {readOnly ? <p className="muted">Base properties are read-only. Create a property profile to constrain this term.</p> : null}
        <label>
          Name
          <input
            disabled={readOnly}
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
          Term URI
          <input
            disabled={readOnly}
            value={slot.slot_uri ?? ''}
            onChange={(event) => patchSlot(selected.id, { slot_uri: event.target.value || undefined })}
          />
        </label>
        <label>
          Profile of
          <input
            disabled={readOnly}
            value={annotationValue(slot, 'profile_of') ?? ''}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'profile_of', event.target.value))}
          />
        </label>
        <label>
          Source vocabulary
          <input
            disabled={readOnly}
            value={annotationValue(slot, 'source_vocabulary') ?? ''}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'source_vocabulary', event.target.value))}
          />
        </label>
        <label>
          Requirement level
          <select
            disabled={readOnly}
            value={level ?? 'optional'}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'requirement_level', event.target.value))}
          >
            <option value="mandatory">Mandatory</option>
            <option value="recommended">Recommended</option>
            <option value="optional">Optional</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </label>
        <label>
          Range
          <select
            disabled={readOnly}
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
            disabled={readOnly}
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
            disabled={readOnly}
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
        <label>
          Usage note
          <textarea
            className="small-textarea"
            disabled={readOnly}
            value={annotationValue(slot, 'usage_note') ?? ''}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'usage_note', event.target.value))}
          />
        </label>
        <label>
          Example value
          <input
            disabled={readOnly}
            value={annotationValue(slot, 'example_value') ?? ''}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'example_value', event.target.value))}
          />
        </label>
        <label>
          Validation severity
          <select
            disabled={readOnly}
            value={annotationValue(slot, 'severity') ?? 'Violation'}
            onChange={(event) => patchSlot(selected.id, setAnnotation(slot, 'severity', event.target.value))}
          >
            <option value="Violation">Violation</option>
            <option value="Warning">Warning</option>
            <option value="Info">Info</option>
          </select>
        </label>
        {readOnly ? (
          <button className="primary" onClick={() => createProfileFromSlot(selected.id)}>
            Create profile of this property
          </button>
        ) : null}
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

function formatPrefixes(prefixes: Record<string, string> | undefined) {
  return Object.entries(prefixes ?? {})
    .map(([prefix, uri]) => `${prefix}: ${uri}`)
    .join('\n');
}

function parsePrefixes(text: string) {
  return Object.fromEntries(
    text
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const separator = line.indexOf(':');
        if (separator < 1) return null;
        const prefix = line.slice(0, separator).trim();
        const uri = line.slice(separator + 1).trim();
        return prefix && uri ? [prefix, uri] : null;
      })
      .filter((entry): entry is [string, string] => Boolean(entry)),
  );
}
