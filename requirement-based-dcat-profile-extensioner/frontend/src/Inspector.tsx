import { useEffect, useState } from 'react';
import { CheckCircle2, Pencil, XCircle, CircleHelp } from 'lucide-react';
import { api, compact, type Call, type Change, type Snapshot } from './api';

export type Selection = { type: 'atom'; id: string } | { type: 'change'; id: string } | null;

function Pill({ value }: { value: string }) {
  return <span className={`pill pill--${value}`}>{value.replace(/_/g, ' ')}</span>;
}

function CallList({ projectId, subject }: { projectId: string; subject: string }) {
  const [calls, setCalls] = useState<Call[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  useEffect(() => { api.calls(projectId, subject).then(setCalls).catch(() => setCalls([])); }, [projectId, subject]);
  if (!calls.length) return null;
  return (
    <section>
      <h4>Model calls</h4>
      {calls.map((c) => (
        <div key={c.id} className="call">
          <button type="button" className="link" onClick={() => setOpen(open === c.id ? null : c.id)}>
            {c.purpose} · {c.model} · {c.prompt_version} · {c.status}{c.cached ? ' (cached)' : ''} · {c.input_tokens}/{c.output_tokens} tok
          </button>
          {open === c.id && (
            <div className="call__body">
              <h5>System prompt</h5><pre>{c.system_prompt}</pre>
              <h5>User prompt</h5><pre>{c.user_prompt}</pre>
              <h5>Answer</h5><pre>{c.response_text || c.error}</pre>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}

function ChangeEditor({ change, onSave, onCancel }: { change: Change; onSave: (c: Change, note: string) => void; onCancel: () => void }) {
  const [draft, setDraft] = useState<Change>(structuredClone(change));
  const [note, setNote] = useState('');
  const f = draft.facets;
  const setF = (patch: Partial<Change['facets']>) => setDraft({ ...draft, facets: { ...f, ...patch } });
  const num = (v: string) => (v === '' ? null : Number(v));
  return (
    <div className="editor">
      <label>Obligation
        <select value={f.obligation} onChange={(e) => setF({ obligation: e.target.value as Change['facets']['obligation'] })}>
          {['mandatory', 'recommended', 'optional'].map((o) => <option key={o}>{o}</option>)}
        </select>
      </label>
      <label>Min <input type="number" value={f.min_count ?? ''} onChange={(e) => setF({ min_count: num(e.target.value) })} /></label>
      <label>Max <input type="number" value={f.max_count ?? ''} onChange={(e) => setF({ max_count: num(e.target.value) })} /></label>
      <label>Range class (IRI) <input value={f.range_class ?? ''} onChange={(e) => setF({ range_class: e.target.value || null })} /></label>
      <label>Datatype (IRI) <input value={f.range_datatype ?? ''} onChange={(e) => setF({ range_datatype: e.target.value || null })} /></label>
      {draft.kind.startsWith('mint') && (<>
        <label>Label <input value={draft.label} onChange={(e) => setDraft({ ...draft, label: e.target.value })} /></label>
        <label>Definition <textarea value={draft.definition} onChange={(e) => setDraft({ ...draft, definition: e.target.value })} /></label>
      </>)}
      <label>Usage note <textarea value={draft.usage_note} onChange={(e) => setDraft({ ...draft, usage_note: e.target.value })} /></label>
      <label>Why you edit (logged) <input value={note} onChange={(e) => setNote(e.target.value)} /></label>
      <div className="row">
        <button type="button" className="primary" onClick={() => onSave(draft, note)}>Save as accepted version</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

export function Inspector({ snapshot, selection, select, reviewer, refresh, notify }: {
  snapshot: Snapshot; selection: Selection; select: (s: Selection) => void; reviewer: string;
  refresh: () => void; notify: (m: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [note, setNote] = useState('');
  useEffect(() => { setEditing(false); setNote(''); }, [selection]);
  const p = snapshot.prefixes;
  const pid = snapshot.project.id;

  if (!selection) {
    const m = snapshot.metrics;
    return (
      <aside className="inspector">
        <h3>Profile</h3>
        <p className="muted">{snapshot.project.profile_title} extends <b>{snapshot.project.base_profile_id}</b>. New terms in <code>{snapshot.project.profile_prefix}:</code> {snapshot.project.profile_namespace}</p>
        <dl className="metrics">
          <div><dt>Atoms</dt><dd>{m.atoms ?? 0}</dd></div>
          <div><dt>Changes in profile</dt><dd>{m.changes_included ?? 0}</dd></div>
          <div><dt>Decided by model</dt><dd>{m.auto_accepted ?? 0}</dd></div>
          <div><dt>Decided by you</dt><dd>{m.accepted_by_human ?? 0}</dd></div>
          <div><dt>Waiting for you</dt><dd>{m.needs_review ?? 0}</dd></div>
          <div><dt>Extension rate</dt><dd>{Math.round((m.extension_rate ?? 0) * 100)}%</dd></div>
          <div><dt>Model calls</dt><dd>{m.llm_calls ?? 0}</dd></div>
          <div><dt>Tokens in/out</dt><dd>{m.input_tokens ?? 0}/{m.output_tokens ?? 0}</dd></div>
        </dl>
        <h4>Coverage</h4>
        <ul className="plain">{Object.entries(m.coverage ?? {}).map(([k, v]) => <li key={k}><Pill value={k} /> {String(v)}</li>)}</ul>
        <p className="muted">Select an atom on the left or an element on the canvas to see its full trace.</p>
      </aside>
    );
  }

  if (selection.type === 'atom') {
    const atom = snapshot.atoms.find((a) => a.id === selection.id);
    if (!atom) return <aside className="inspector" />;
    const assessment = snapshot.assessments.find((a) => a.atom_id === atom.id);
    const changes = snapshot.changes.filter((c) => c.covers.some((l) => l.atom_id === atom.id) && c.decision.status !== 'superseded');
    const candidates = snapshot.candidates[atom.id] ?? [];
    return (
      <aside className="inspector">
        <div className="inspector__head"><h3>{atom.id}</h3><Pill value={snapshot.coverage[atom.id] ?? 'unaddressed'} /></div>
        <blockquote>{atom.statement}</blockquote>
        <p className="muted">subject: {atom.subject} · modality: <b>{atom.modality}</b>
          {atom.source_reference ? ` · source: ${atom.source_reference.document}${atom.source_reference.locator ? `, ${atom.source_reference.locator}` : ''}` : ''}</p>
        {atom.counterfactual_of && <p className="note">Counterfactual of {atom.counterfactual_of}: {atom.expected_change}</p>}
        {assessment?.lint.length ? (<section><h4>Atom checks</h4><ul className="issues">
          {assessment.lint.map((i) => <li key={i.code} className={`issue issue--${i.severity}`}><b>{i.code}</b> {i.message}</li>)}</ul></section>) : null}
        {assessment && (
          <section>
            <h4>Decision on this atom <Pill value={assessment.disposition} /></h4>
            {assessment.reading && <p><i>Read as:</i> {assessment.reading}</p>}
            <p>{assessment.reason}</p>
            {assessment.covered_by.length > 0 && <p>Covered by base: {assessment.covered_by.map((r) => compact(r.path, p)).join(', ')}</p>}
            <p className="muted">by {assessment.provenance.author}{assessment.provenance.votes_total > 1 ? ` · ${assessment.provenance.votes_agreeing}/${assessment.provenance.votes_total} votes agree` : ''}</p>
            <div className="row">
              {(['needs_change', 'covered_by_base', 'out_of_scope'] as const).filter((d) => d !== assessment.disposition).map((d) => (
                <button key={d} type="button" onClick={async () => {
                  const reason = window.prompt(`Why is ${atom.id} ${d.replace(/_/g, ' ')}?`);
                  if (!reason) return;
                  await api.override(pid, atom.id, d, reason, reviewer); notify(`${atom.id}: set to ${d}`); refresh();
                }}>Set {d.replace(/_/g, ' ')}</button>))}
            </div>
          </section>
        )}
        <section><h4>Changes covering it</h4>
          {changes.length ? changes.map((c) => (
            <button key={c.id} type="button" className="trace-link" onClick={() => select({ type: 'change', id: c.id })}>
              <Pill value={c.decision.status} /> {snapshot.verbalised[c.id]}
            </button>)) : <p className="muted">None.</p>}
        </section>
        <section><h4>Retrieved candidate terms</h4>
          <ol className="candidates">{candidates.map((c) => (
            <li key={c.iri} title={c.why}><code>{c.curie}</code> {c.label} <span className="muted">{c.score.toFixed(1)}</span>
              {c.in_base_on_class && <span className="badge badge--base">in base {c.base_facets?.obligation}</span>}</li>))}
          </ol>
        </section>
        <CallList projectId={pid} subject={atom.id} />
      </aside>
    );
  }

  const change = snapshot.changes.find((c) => c.id === selection.id);
  if (!change) return <aside className="inspector" />;
  const failed = change.verification.filter((r) => !r.passed);
  const decide = async (status: string) => {
    await api.decide(pid, change.id, status, reviewer, note);
    notify(`${change.id}: ${status}`); refresh();
  };
  return (
    <aside className="inspector">
      <div className="inspector__head"><h3>{change.kind.replace(/_/g, ' ')}</h3><Pill value={change.decision.status} /></div>
      <p className="verbal">{snapshot.verbalised[change.id]}</p>
      <p className="muted">Decision by {change.decision.decided_by}{change.decision.note ? `: ${change.decision.note}` : ''}</p>
      {change.decision.status !== 'superseded' && !editing && (
        <section className="actions">
          <input placeholder="Note for the log (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="row">
            <button type="button" className="primary" onClick={() => decide('accepted')}><CheckCircle2 size={15} /> Accept</button>
            <button type="button" onClick={() => decide('rejected')}><XCircle size={15} /> Reject</button>
            <button type="button" onClick={() => decide('needs_review')}><CircleHelp size={15} /> Undecided</button>
            {change.path && <button type="button" onClick={() => setEditing(true)}><Pencil size={15} /> Edit</button>}
          </div>
        </section>
      )}
      {editing && <ChangeEditor change={change} onCancel={() => setEditing(false)} onSave={async (edited, why) => {
        const saved = await api.edit(pid, change.id, edited, reviewer, why); notify('Edited version saved and verified');
        refresh(); select({ type: 'change', id: saved.id });
      }} />}
      <section><h4>Why: requirements it covers</h4>
        {change.covers.map((l) => (
          <div key={l.atom_id} className="cover">
            <button type="button" className="link" onClick={() => select({ type: 'atom', id: l.atom_id })}>{l.atom_id}</button> <Pill value={l.coverage} />
            <p>{l.reason}</p>{l.evidence_quote && <blockquote>“{l.evidence_quote.replace(/^["“”\s]+|["“”\s]+$/g, '')}”</blockquote>}
          </div>))}
      </section>
      {change.facet_justifications.length > 0 && (
        <section><h4>Constraints set or tightened</h4>
          <table className="facets"><thead><tr><th>Facet</th><th>Base</th><th>Now</th><th>vs base</th><th>Reason</th></tr></thead>
            <tbody>{change.facet_justifications.filter((j) => !(j.facet === 'min_count' && j.new_value === '0' && !j.base_value)).map((j) => (
              <tr key={j.facet}><td>{j.facet}</td><td>{compact(j.base_value, p) || '–'}</td><td>{compact(j.new_value, p)}</td>
                <td>{j.status && <Pill value={j.status} />}</td><td>{j.reason}</td></tr>))}</tbody></table>
        </section>)}
      {change.mint && (<section><h4>Why a new term</h4><p>{change.mint.reason_no_reuse}</p>
        <ul className="plain">{change.mint.rejected_candidates.map((r) => <li key={r.iri}><code>{compact(r.iri, p)}</code>: {r.reason}</li>)}</ul></section>)}
      {change.alternatives.length > 0 && (<section><h4>Alternatives considered</h4>
        <ul className="plain">{change.alternatives.map((r) => <li key={r.iri}><code>{compact(r.iri, p)}</code>: {r.reason}</li>)}</ul></section>)}
      <section><h4>Checks</h4>
        <ul className="issues">{change.verification.map((r, i) => (
          <li key={i} className={`issue issue--${r.passed ? 'ok' : r.severity}`}><b>{r.check}</b> {r.message || (r.passed ? 'passed' : '')}</li>))}</ul>
        {failed.length === 0 && <p className="muted">All checks passed.</p>}
      </section>
      <section><h4>Provenance</h4>
        <p className="muted">{change.provenance.author} · {change.provenance.prompt_version ?? ''} · confidence {change.confidence.toFixed(2)}
          {change.provenance.repair_round ? ` · repair round ${change.provenance.repair_round}` : ''}
          {change.provenance.votes_total > 1 ? ` · ${change.provenance.votes_agreeing}/${change.provenance.votes_total} votes` : ''}</p>
        {change.rationale && <p>{change.rationale}</p>}
        {change.engine_notes.length > 0 && <ul className="plain">{change.engine_notes.map((n, i) => <li key={i} className="muted">{n}</li>)}</ul>}
        {change.supersedes && <p className="muted">Replaces {change.supersedes}</p>}
      </section>
      <CallList projectId={pid} subject={change.id} />
      {change.covers[0] && <CallList projectId={pid} subject={change.covers[0].atom_id} />}
    </aside>
  );
}
