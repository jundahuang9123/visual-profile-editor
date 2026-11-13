// Typed client of the workbench API (mirrors backend/profile_extensioner/contracts.py).

export type Obligation = 'mandatory' | 'recommended' | 'optional' | 'unknown';
export type DecisionStatus = 'proposed' | 'auto_accepted' | 'needs_review' | 'accepted' | 'rejected' | 'superseded';
export type ChangeKind = 'reuse_property' | 'refine_property' | 'mint_property' | 'reuse_class' | 'mint_class' | 'usage_note';
export type StageState = 'pending' | 'running' | 'done' | 'stale' | 'failed' | 'skipped';

export type LintIssue = { code: string; severity: 'error' | 'warning' | 'info'; message: string; suggestion?: string | null };
export type Atom = {
  id: string; statement: string; subject: string; modality: 'must' | 'should' | 'may' | 'unspecified';
  source_reference?: { document: string; locator?: string | null } | null;
  counterfactual_of?: string | null; expected_change?: string | null; active: boolean; hints: string[];
};
export type Facets = {
  obligation: Obligation; min_count: number | null; max_count: number | null; range_class: string | null;
  range_datatype: string | null; node_kind: string | null; controlled_vocabulary: string[]; pattern?: string | null;
};
export type Provenance = {
  author_type: 'llm' | 'rule' | 'human'; author: string; model?: string | null; prompt_version?: string | null;
  call_ids: string[]; repair_round: number; votes_total: number; votes_agreeing: number; created_at: string;
};
export type Assessment = {
  atom_id: string; disposition: 'needs_change' | 'covered_by_base' | 'out_of_scope' | 'unclear'; reason: string;
  reading: string; information_needed: string; resource_class: string | null;
  covered_by: { target_class: string; path: string | null }[]; lint: LintIssue[]; confidence: number; provenance: Provenance;
};
export type Candidate = {
  iri: string; curie: string; kind: 'class' | 'property'; label: string; definition: string; score: number; rank: number;
  in_base_on_class: boolean; base_facets: Facets | null; why: string;
};
export type CheckResult = { check: string; passed: boolean; severity: 'error' | 'warning' | 'info'; message: string };
export type Change = {
  id: string; kind: ChangeKind; target_class: string; path: string | null; label: string; definition: string;
  usage_note: string; facets: Facets; severity: string | null;
  covers: { atom_id: string; reason: string; evidence_quote: string; coverage: 'full' | 'partial' }[];
  facet_justifications: { facet: string; base_value: string | null; new_value: string | null; status: string | null; atom_ids: string[]; reason: string }[];
  mint: { reason_no_reuse: string; rejected_candidates: { iri: string; reason: string }[] } | null;
  alternatives: { iri: string; reason: string }[];
  rationale: string; confidence: number; engine_notes: string[]; merged_from: string[]; supersedes: string | null;
  provenance: Provenance; verification: CheckResult[];
  decision: { status: DecisionStatus; decided_by: string; note: string; decided_at: string };
};
export type ConformanceReport = {
  base_profile_id: string; verdict: string; summary: string; delta_counts: Record<string, number>; witness_turtle: string;
  checks: { id: string; title: string; passed: boolean; severity: string; message: string; source: string;
    items: { target_class?: string | null; path?: string | null; change_id?: string | null; facet?: string | null;
      base_value?: string | null; new_value?: string | null; status?: string | null; message: string }[] }[];
};
export type LLMSettings = {
  provider: 'mock' | 'anthropic' | 'openai-compatible'; model: string | null; base_url: string | null;
  effort: string; temperature: number | null; max_output_tokens: number; timeout_seconds: number; step_models: Record<string, string>;
};
export type PipelineConfig = {
  retrieval: boolean; top_k: number; verify: boolean; repair_rounds: number; attribution_check: boolean; votes: number;
  auto_accept: boolean; auto_accept_min_confidence: number; require_human_signoff: boolean; use_hints: boolean;
  exclude_namespaces: string[]; max_parallel_calls: number;
};
export type Project = {
  id: string; name: string; description: string; base_profile_id: string; profile_title: string;
  profile_namespace: string; profile_prefix: string; created_at: string; updated_at: string;
  config: PipelineConfig; llm: LLMSettings; stage_states: Record<string, StageState>;
  signoff: { by: string; note: string; at: string; change_set_hash: string } | null;
};
export type Snapshot = {
  project: Project; atoms: Atom[]; assessments: Assessment[]; candidates: Record<string, Candidate[]>;
  changes: Change[]; conflicts: { id: string; change_ids: string[]; atom_ids: string[]; description: string }[];
  coverage: Record<string, string>; artifacts: { name: string; title: string; media_type: string; content: string }[];
  conformance: ConformanceReport | null; metrics: Record<string, any>; running: string | null;
  verbalised: Record<string, string>; prefixes: Record<string, string>;
};
export type Entry = { seq: number; stage: string; kind: string; subject_type: string; subject_id: string; author: string; summary: string; created_at: string };
export type Call = { id: string; stage: string; purpose: string; subject_id: string; provider: string; model: string; prompt_version: string;
  system_prompt: string; user_prompt: string; response_text: string; input_tokens: number; output_tokens: number; duration_ms: number;
  cached: boolean; status: string; error: string; created_at: string };
export type BaseElement = { target_class: string; path: string; label: string; definition: string; facets: Facets };
export type BaseProfile = { info: { id: string; title: string }; classes: { iri: string; label: string; obligation: string }[]; elements: BaseElement[] };
export type ProviderStatus = { provider: string; label: string; needs_key: boolean; key_source: string; default_model: string | null; note: string };

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method, headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = await response.text();
    try { detail = JSON.parse(detail).detail ?? detail; } catch { /* plain text */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return (await response.json()) as T;
}

export const api = {
  projects: () => call<Project[]>('GET', '/projects'),
  examples: () => call<string[]>('GET', '/examples'),
  baseProfiles: () => call<{ id: string; title: string; class_count: number; element_count: number }[]>('GET', '/base-profiles'),
  baseProfile: (id: string) => call<BaseProfile>('GET', `/base-profiles/${id}`),
  createProject: (body: Record<string, unknown>) => call<Project>('POST', '/projects', body),
  deleteProject: (id: string) => call('DELETE', `/projects/${id}`),
  snapshot: (id: string) => call<Snapshot>('GET', `/projects/${id}`),
  updateProject: (id: string, body: Partial<{ config: PipelineConfig; llm: LLMSettings; profile_title: string }>) =>
    call<Project>('PATCH', `/projects/${id}`, body),
  replaceAtoms: (id: string, text: string) => call<Atom[]>('PUT', `/projects/${id}/atoms`, { text }),
  runAsync: (id: string, body: { from_stage?: string; only?: string; atom_ids?: string[] }) => call('POST', `/projects/${id}/run-async`, body),
  entries: (id: string, after = 0) => call<Entry[]>('GET', `/projects/${id}/entries?after=${after}`),
  calls: (id: string, subject?: string) => call<Call[]>('GET', `/projects/${id}/calls${subject ? `?subject_id=${encodeURIComponent(subject)}` : ''}`),
  decide: (id: string, changeId: string, status: string, by: string, note: string) =>
    call<Change>('POST', `/projects/${id}/changes/${changeId}/decision`, { status, by, note }),
  edit: (id: string, changeId: string, change: Change, by: string, note: string) =>
    call<Change>('PUT', `/projects/${id}/changes/${changeId}`, { change, by, note }),
  override: (id: string, atomId: string, disposition: string, reason: string, by: string) =>
    call('POST', `/projects/${id}/atoms/${atomId}/assessment`, { disposition, reason, by }),
  signoff: (id: string, by: string, note: string) => call('POST', `/projects/${id}/signoff`, { by, note }),
  providers: () => call<ProviderStatus[]>('GET', '/llm/providers'),
  setKey: (provider: string, apiKey: string) => call<ProviderStatus[]>('POST', '/llm/key', { provider, api_key: apiKey }),
  models: (settings: LLMSettings) => call<string[]>('POST', '/llm/models', settings),
  terms: (id: string, q: string) => call<any[]>('GET', `/terms?project_id=${id}&q=${encodeURIComponent(q)}`),
};

export function compact(iri: string | null | undefined, prefixes: Record<string, string>): string {
  if (!iri) return '';
  let best: [string, string] | null = null;
  for (const [prefix, ns] of Object.entries(prefixes)) {
    if (iri.startsWith(ns) && (!best || ns.length > best[1].length)) best = [prefix, ns];
  }
  return best ? `${best[0]}:${iri.slice(best[1].length)}` : iri;
}

export const STAGES = ['intake', 'retrieve', 'propose', 'verify', 'repair', 'consolidate', 'compile', 'conformance', 'review'] as const;
