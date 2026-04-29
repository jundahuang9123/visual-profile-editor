import { useEffect, useMemo, useState } from 'react';
import { Pencil, Plus, Trash2, X } from 'lucide-react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { Slot } from '../types';
import { useEditorStore } from '../store';

type ClassNodeData = {
  label: string;
  slots: string[];
  slotDefs: Record<string, Slot>;
};

type InlineSlotEditorProps = {
  className: string;
  slotName: string;
  slot: Slot | undefined;
  ranges: string[];
};

function InlineSlotEditor({ className, slotName, slot, ranges }: InlineSlotEditorProps) {
  const updateSlot = useEditorStore((state) => state.updateSlot);
  const removeSlotFromClass = useEditorStore((state) => state.removeSlotFromClass);
  const [name, setName] = useState(slotName);

  useEffect(() => {
    setName(slotName);
  }, [slotName]);

  const range = slot?.range ?? 'string';
  const required = Boolean(slot?.required);
  const multivalued = Boolean(slot?.multivalued);

  function commitName() {
    const nextName = name.trim();
    if (!nextName) {
      setName(slotName);
      return;
    }
    if (nextName !== slotName) {
      updateSlot(slotName, { name: nextName, range, required, multivalued });
    }
  }

  return (
    <div className="class-node__slot-editor nodrag nowheel" onDoubleClick={(event) => event.stopPropagation()}>
      <input
        aria-label="Property name"
        value={name}
        onBlur={commitName}
        onChange={(event) => setName(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.currentTarget.blur();
          }
          if (event.key === 'Escape') {
            setName(slotName);
            event.currentTarget.blur();
          }
        }}
      />
      <select
        aria-label="Property range"
        value={range}
        onChange={(event) =>
          updateSlot(slotName, {
            name: slotName,
            range: event.target.value,
            required,
            multivalued,
          })
        }
      >
        {ranges.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <label className="class-node__flag">
        <input
          type="checkbox"
          checked={required}
          onChange={(event) =>
            updateSlot(slotName, {
              name: slotName,
              range,
              required: event.target.checked,
              multivalued,
            })
          }
        />
        Req
      </label>
      <label className="class-node__flag">
        <input
          type="checkbox"
          checked={multivalued}
          onChange={(event) =>
            updateSlot(slotName, {
              name: slotName,
              range,
              required,
              multivalued: event.target.checked,
            })
          }
        />
        Multi
      </label>
      <button
        className="class-node__icon-button"
        title="Delete property"
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          removeSlotFromClass(className, slotName);
        }}
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}

export function ClassNode({ data, selected }: NodeProps) {
  const nodeData = data as ClassNodeData;
  const schema = useEditorStore((state) => state.schema);
  const addSlot = useEditorStore((state) => state.addSlot);
  const setSelected = useEditorStore((state) => state.setSelected);
  const [editing, setEditing] = useState(false);

  const rangeOptions = useMemo(() => {
    const primitives = ['string', 'anyURI', 'integer', 'float', 'boolean'];
    return [...primitives, ...Object.keys(schema.classes), ...Object.keys(schema.enums)];
  }, [schema.classes, schema.enums]);

  function toggleEditing() {
    setEditing((value) => !value);
    setSelected({ kind: 'class', id: nodeData.label });
  }

  return (
    <div
      className={`class-node ${selected ? 'selected' : ''} ${editing ? 'editing' : ''}`}
      onDoubleClick={toggleEditing}
    >
      <Handle type="target" position={Position.Top} />
      <div className="class-node__title">
        <span>{nodeData.label}</span>
        <button
          className="class-node__edit-toggle nodrag"
          title={editing ? 'Close diagram editor' : 'Edit class in diagram'}
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            toggleEditing();
          }}
        >
          {editing ? <X size={14} /> : <Pencil size={14} />}
        </button>
      </div>
      <div className="class-node__slots">
        {nodeData.slots.length === 0 ? (
          <div className="class-node__empty">No properties</div>
        ) : editing ? (
          nodeData.slots.map((slotName) => (
            <InlineSlotEditor
              className={nodeData.label}
              key={slotName}
              ranges={rangeOptions}
              slot={nodeData.slotDefs[slotName]}
              slotName={slotName}
            />
          ))
        ) : (
          nodeData.slots.map((slotName) => {
            const slot = nodeData.slotDefs[slotName];
            return (
              <div className="class-node__slot" key={slotName}>
                <span>{slotName}</span>
                <small>
                  {slot?.range ?? 'string'}
                  {slot?.required ? ' !' : ''}
                  {slot?.multivalued ? ' *' : ''}
                </small>
              </div>
            );
          })
        )}
        {editing ? (
          <button
            className="class-node__add-property nodrag"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              addSlot(nodeData.label);
            }}
          >
            <Plus size={14} />
            Add property
          </button>
        ) : null}
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
