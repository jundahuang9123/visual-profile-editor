import { memo, useMemo, useState } from 'react';
import { Background, Controls, Handle, MarkerType, MiniMap, Position, ReactFlow, type Edge, type Node, type NodeProps } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { compact, type BaseProfile, type Change, type Snapshot } from './api';

type Row = { key: string; label: string; detail: string; kind: string; status?: string; changeId?: string; atoms?: string[] };
type ClassData = { title: string; curie: string; layer: 'base' | 'profile' | 'extension'; rows: Row[]; baseRows: Row[];
  selected: string | null; onSelect: (changeId: string) => void; expanded: boolean; onToggle: () => void };

const KIND_LABEL: Record<string, string> = {
  reuse_property: 'reuse', refine_property: 'refine', mint_property: 'new', reuse_class: 'reuse', mint_class: 'new', usage_note: 'note',
};

function card(f: Change['facets']) {
  return `${f.min_count ?? 0}..${f.max_count ?? 'n'}`;
}

const ClassNode = memo(function ClassNode({ data }: NodeProps<Node<ClassData>>) {
  return (
    <div className={`class-node class-node--${data.layer}`}>
      <Handle type="target" position={Position.Left} />
      <div className="class-node__title">
        <strong>{data.title}</strong>
        <span className={`badge badge--${data.layer}`}>{data.layer}</span>
      </div>
      <div className="class-node__curie">{data.curie}</div>
      {data.rows.map((row) => (
        <button
          key={row.key}
          type="button"
          className={`class-row class-row--${row.kind} ${row.status ? `class-row--${row.status}` : ''} ${data.selected === row.changeId ? 'is-selected' : ''}`}
          onClick={(event) => { event.stopPropagation(); if (row.changeId) data.onSelect(row.changeId); }}
          title={row.atoms?.length ? `covers ${row.atoms.join(', ')}` : undefined}
        >
          <span className="class-row__kind">{KIND_LABEL[row.kind] ?? row.kind}</span>
          <span className="class-row__label">{row.label}</span>
          <span className="class-row__detail">{row.detail}</span>
          {row.atoms?.length ? <span className="class-row__atoms">{row.atoms.length}</span> : null}
        </button>
      ))}
      {data.baseRows.length ? (
        <button type="button" className="class-node__base-toggle" onClick={(e) => { e.stopPropagation(); data.onToggle(); }}>
          {data.expanded ? 'Hide' : 'Show'} {data.baseRows.length} inherited base properties
        </button>
      ) : null}
      {data.expanded && data.baseRows.map((row) => (
        <div key={row.key} className="class-row class-row--base"><span className="class-row__kind">base</span>
          <span className="class-row__label">{row.label}</span><span className="class-row__detail">{row.detail}</span></div>
      ))}
      <Handle type="source" position={Position.Right} />
    </div>
  );
});

const nodeTypes = { classNode: ClassNode };

export function ProfileCanvas({ snapshot, base, selected, onSelect, showRejected }: {
  snapshot: Snapshot; base: BaseProfile | null; selected: string | null; onSelect: (id: string) => void; showRejected: boolean;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const p = snapshot.prefixes;
  const { nodes, edges } = useMemo(() => {
    const live = snapshot.changes.filter((c) => c.decision.status !== 'superseded' && (showRejected || c.decision.status !== 'rejected'));
    const classes: string[] = [];
    for (const change of live) if (!classes.includes(change.target_class)) classes.push(change.target_class);
    const nodes: Node<ClassData>[] = classes.map((cls, index) => {
      const mine = live.filter((c) => c.target_class === cls);
      const minted = mine.some((c) => c.kind === 'mint_class');
      const baseClass = base?.classes.find((b) => b.iri === cls);
      const touched = new Set(mine.map((c) => c.path).filter(Boolean));
      const rows: Row[] = mine.filter((c) => c.path).map((c) => ({
        key: c.id, changeId: c.id, kind: c.kind, status: c.decision.status, atoms: c.covers.map((l) => l.atom_id),
        label: compact(c.path, p), detail: `${c.facets.obligation} ${card(c.facets)}`,
      }));
      const classChange = mine.find((c) => c.kind === 'mint_class' || c.kind === 'reuse_class');
      if (classChange) rows.unshift({ key: classChange.id, changeId: classChange.id, kind: classChange.kind, status: classChange.decision.status,
        atoms: classChange.covers.map((l) => l.atom_id), label: classChange.kind === 'mint_class' ? 'new class' : 'class added', detail: '' });
      const baseRows: Row[] = (base?.elements ?? []).filter((e) => e.target_class === cls && !touched.has(e.path)).map((e) => ({
        key: e.path, kind: 'base', label: compact(e.path, p), detail: `${e.facets.obligation} ${card(e.facets)}`,
      }));
      return {
        id: cls, type: 'classNode', position: { x: (index % 3) * 380, y: Math.floor(index / 3) * 360 },
        data: {
          title: baseClass?.label || compact(cls, p), curie: compact(cls, p), layer: minted ? 'extension' : baseClass ? 'profile' : 'extension',
          rows, baseRows, selected, onSelect, expanded: !!expanded[cls], onToggle: () => setExpanded((e) => ({ ...e, [cls]: !e[cls] })),
        },
      };
    });
    const edges: Edge[] = [];
    for (const change of live) {
      const range = change.facets.range_class;
      if (change.path && range && classes.includes(range)) {
        edges.push({ id: `${change.id}-range`, source: change.target_class, target: range, label: compact(change.path, p),
          type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, className: 'edge-range' });
      }
    }
    return { nodes, edges };
  }, [snapshot, base, selected, onSelect, expanded, showRejected, p]);

  if (!nodes.length) return <p className="empty">No profile changes yet. Run the pipeline to let the model propose an extension.</p>;
  return (
    <div className="canvas">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView nodesDraggable proOptions={{ hideAttribution: true }}>
        <Background color="#d4dbe8" gap={18} />
        <Controls />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  );
}
