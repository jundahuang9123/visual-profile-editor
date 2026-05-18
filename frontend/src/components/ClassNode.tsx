import { useEffect, useMemo, useState } from 'react';
import { Minimize2, Pencil, Plus, Trash2, X } from 'lucide-react';
import { Handle, Position, useUpdateNodeInternals, type NodeProps } from '@xyflow/react';
import type { SchemaClass, Slot } from '../types';
import { useEditorStore } from '../store';
import { requirementLevel, termKind } from '../lib/profile';

type ClassNodeData = {
  label: string;
  classDef?: SchemaClass;
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
  const readOnly = termKind(slot, 'slot_uri') === 'base';

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
        className={required ? 'class-node__property-name--required' : undefined}
        disabled={readOnly}
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
        disabled={readOnly}
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
            disabled={readOnly}
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
            disabled={readOnly}
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
        disabled={readOnly}
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
  const minimized = useEditorStore((state) => Boolean(state.minimizedClasses[nodeData.label]));
  const addSlot = useEditorStore((state) => state.addSlot);
  const setSelected = useEditorStore((state) => state.setSelected);
  const toggleClassMinimized = useEditorStore((state) => state.toggleClassMinimized);
  const updateNodeInternals = useUpdateNodeInternals();
  const [editing, setEditing] = useState(false);
  const classKind = termKind(nodeData.classDef, 'class_uri');
  const classRequirement = requirementLevel(nodeData.classDef);
  const isBaseClass = classKind === 'base';

  useEffect(() => {
    if (minimized) setEditing(false);
    updateNodeInternals(nodeData.label);
  }, [minimized, nodeData.label, updateNodeInternals]);

  const rangeOptions = useMemo(() => {
    const primitives = ['string', 'anyURI', 'integer', 'float', 'boolean'];
    return [...primitives, ...Object.keys(schema.classes), ...Object.keys(schema.enums)];
  }, [schema.classes, schema.enums]);

  function toggleEditing() {
    if (isBaseClass) return;
    setEditing((value) => !value);
    setSelected({ kind: 'class', id: nodeData.label });
  }

  if (minimized) {
    return (
      <div
        className={`class-node class-node--minimized ${selected ? 'selected' : ''}`}
        onDoubleClick={(event) => {
          event.stopPropagation();
          toggleClassMinimized(nodeData.label);
        }}
        title="Double-click to expand"
      >
        <Handle type="target" position={Position.Top} />
        <span className="class-node__bubble-label">{nodeData.label}</span>
        <Handle type="source" position={Position.Bottom} />
      </div>
    );
  }

  return (
    <div
      className={`class-node ${selected ? 'selected' : ''} ${editing ? 'editing' : ''}`}
      onDoubleClick={toggleEditing}
    >
      <Handle type="target" position={Position.Top} />
      <div className="class-node__title">
        <span>{nodeData.label}</span>
        <span className={`term-badge term-badge--${classKind}`}>{classKind.toUpperCase()}</span>
        {classRequirement ? <span className={`term-badge term-badge--${classRequirement}`}>{classRequirement.toUpperCase()}</span> : null}
        <div className="class-node__title-actions">
          <button
            className="class-node__edit-toggle nodrag"
            title="Minimize class"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              toggleClassMinimized(nodeData.label);
            }}
          >
            <Minimize2 size={14} />
          </button>
          <button
            className="class-node__edit-toggle nodrag"
            disabled={isBaseClass}
            title={isBaseClass ? 'Base vocabulary terms are read-only' : editing ? 'Close diagram editor' : 'Edit class in diagram'}
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              toggleEditing();
            }}
          >
            {editing ? <X size={14} /> : <Pencil size={14} />}
          </button>
        </div>
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
            const required = Boolean(slot?.required);
            const slotKind = termKind(slot, 'slot_uri');
            const slotRequirement = requirementLevel(slot);
            return (
              <div className={`class-node__slot ${required ? 'class-node__slot--required' : ''}`} key={slotName}>
                <span>{slotName}</span>
                <small>
                  {slot?.range ?? 'string'}
                  {slot?.required ? ' !' : ''}
                  {slot?.multivalued ? ' *' : ''}
                </small>
                <span className={`term-badge term-badge--${slotKind}`}>{slotKind.toUpperCase()}</span>
                {slotRequirement ? <span className={`term-badge term-badge--${slotRequirement}`}>{slotRequirement.toUpperCase()}</span> : null}
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
