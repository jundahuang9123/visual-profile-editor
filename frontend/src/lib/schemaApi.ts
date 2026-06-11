import yaml from 'js-yaml';
import { emptySchema, normalizeSchema, schemaToRdfTurtle, schemaToShaclTurtle } from './schema';
import type { SchemaModel } from '../types';
import type { ExportKind } from '../components/Toolbar';

const STORAGE_KEY = 'constructDcatProfileEditor.schema';

type NativeExportPayload = {
  action: 'exportText';
  filename: string;
  type: string;
  text: string;
};

declare global {
  interface Window {
    GeneralOntologyEditor?: {
      exportText?: (filename: string, type: string, text: string) => void;
    };
    webkit?: {
      messageHandlers?: {
        generalOntologyEditor?: {
          postMessage: (payload: NativeExportPayload) => void;
        };
      };
    };
  }
}

type LoadResult = {
  schema: SchemaModel;
  message: string;
};

type SaveResult = {
  message: string;
};

export type ProfileWorkspace = {
  directory: string;
  schema_path: string;
  default_directory: string;
  seed_path: string;
};

export type ProfileWorkspaceDirectory = {
  name: string;
  path: string;
};

export type ProfileWorkspaceBrowse = {
  directory: string;
  parent_directory: string | null;
  entries: ProfileWorkspaceDirectory[];
  home_directory: string;
  default_directory: string;
  repo_directory: string;
};

export type ProfileWorkspacePick = {
  directory: string | null;
  cancelled: boolean;
  method: string;
};

type WorkspaceUpdateResult = {
  workspace: ProfileWorkspace;
  schema: SchemaModel;
};

export function downloadText(text: string, filename: string, type: string) {
  if (exportWithNativePicker(text, filename, type)) {
    return;
  }

  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function exportWithNativePicker(text: string, filename: string, type: string) {
  try {
    const androidExporter = window.GeneralOntologyEditor?.exportText;
    if (androidExporter) {
      androidExporter(filename, type, text);
      return true;
    }

    const iosHandler = window.webkit?.messageHandlers?.generalOntologyEditor;
    if (iosHandler) {
      iosHandler.postMessage({ action: 'exportText', filename, type, text });
      return true;
    }
  } catch (error) {
    console.warn('Native export is unavailable; falling back to browser download.', error);
  }

  return false;
}

export async function loadSchemaModel(): Promise<LoadResult> {
  if (!isBundledRuntime()) {
    try {
      const res = await fetch('/api/profile/model');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return {
        schema: normalizeSchema((await res.json()) as SchemaModel),
        message: 'Loaded',
      };
    } catch (error) {
      const local = loadLocalSchema();
      if (local) {
        return {
          schema: local,
          message: `Server unavailable; loaded device copy (${errorMessage(error)}).`,
        };
      }
      return {
        schema: emptySchema(),
        message: `Server unavailable; started a local schema (${errorMessage(error)}).`,
      };
    }
  }

  const local = loadLocalSchema();
  return {
    schema: local ?? emptySchema(),
    message: local ? 'Loaded local device copy' : 'Started bundled local editor',
  };
}

export async function saveSchemaYaml(yamlText: string): Promise<SaveResult> {
  if (!isBundledRuntime()) {
    try {
      const res = await fetch('/api/profile/linkml', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml: yamlText }),
      });
      if (!res.ok) throw new Error(await res.text());
      const payload = (await res.json()) as Partial<ProfileWorkspace>;
      saveLocalSchema(parseLinkmlSchema(yamlText));
      return { message: payload.schema_path ? `Saved to ${payload.schema_path}` : 'Saved to workspace profile.yaml' };
    } catch (error) {
      saveLocalSchema(parseLinkmlSchema(yamlText));
      return { message: `Server save failed; saved on this device (${errorMessage(error)}).` };
    }
  }

  saveLocalSchema(parseLinkmlSchema(yamlText));
  return { message: 'Saved on this device' };
}

export async function importSchemaFile(file: File): Promise<SchemaModel> {
  if (!isBundledRuntime()) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/profile/import', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      return normalizeSchema((await res.json()) as SchemaModel);
    } catch (error) {
      if (!isLinkmlFile(file.name)) {
        throw new Error(`Server import failed: ${errorMessage(error)}`);
      }
    }
  }

  if (!isLinkmlFile(file.name)) {
    throw new Error('Bundled mode can import LinkML YAML/JSON. RDF, OWL, and SHACL import still need the backend server.');
  }

  const text = await file.text();
  return parseLinkmlSchema(text);
}

export async function exportSchema(schema: SchemaModel, kind: ExportKind) {
  if (!isBundledRuntime()) {
    const endpoint = kind === 'package' ? '/profile/export/package' : `/profile/export/${kind}`;
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(await res.text());
    if (kind === 'package') {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'construct-dcat-profile.zip';
      link.click();
      URL.revokeObjectURL(url);
      return;
    }
    const text = await res.text();
    const filename = kind === 'rdf' ? 'profile.ttl' : kind === 'shacl' ? 'profile.shacl.ttl' : kind === 'jsonschema' ? 'profile.schema.json' : 'profile.yaml';
    const type = kind === 'jsonschema' ? 'application/schema+json' : kind === 'linkml' ? 'application/yaml' : 'text/turtle';
    downloadText(text, filename, type);
    return;
  }

  const text = kind === 'rdf' ? schemaToRdfTurtle(schema) : kind === 'shacl' ? schemaToShaclTurtle(schema) : yaml.dump(schema);
  downloadText(text, kind === 'rdf' ? 'profile.ttl' : kind === 'shacl' ? 'profile.shacl.ttl' : 'profile.yaml', 'text/plain');
}

export type ProfileTemplate = {
  id: string;
  title: string;
  description: string;
};

export async function loadProfileTemplates(): Promise<ProfileTemplate[]> {
  const res = await fetch('/api/profile/templates');
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ProfileTemplate[];
}

export async function loadProfileTemplate(templateId: string): Promise<SchemaModel> {
  const res = await fetch(`/api/profile/templates/${templateId}/load`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return normalizeSchema((await res.json()) as SchemaModel);
}

export async function loadProfileWorkspace(): Promise<ProfileWorkspace> {
  const res = await fetch('/api/profile/workspace');
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ProfileWorkspace;
}

export async function browseProfileWorkspace(directory?: string): Promise<ProfileWorkspaceBrowse> {
  const params = new URLSearchParams();
  if (directory?.trim()) params.set('directory', directory.trim());
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`/api/profile/workspace/browse${suffix}`);
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ProfileWorkspaceBrowse;
}

export async function pickProfileWorkspaceDirectory(directory?: string): Promise<ProfileWorkspacePick> {
  const res = await fetch('/api/profile/workspace/pick', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ directory: directory?.trim() || undefined }),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as ProfileWorkspacePick;
}

export async function setProfileWorkspace(directory: string): Promise<WorkspaceUpdateResult> {
  const res = await fetch('/api/profile/workspace', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ directory }),
  });
  if (!res.ok) throw new Error(await res.text());
  const result = (await res.json()) as WorkspaceUpdateResult;
  return {
    workspace: result.workspace,
    schema: normalizeSchema(result.schema),
  };
}

export async function validateProfile(schema: SchemaModel) {
  const res = await fetch('/api/profile/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(schema),
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as {
    valid: boolean;
    errors: Array<Record<string, string>>;
    warnings: Array<Record<string, string>>;
    suggestions: Array<Record<string, string>>;
  };
}

export async function loadPreview(kind: 'shacl' | 'rdf' | 'jsonschema' | 'linkml') {
  const res = await fetch(`/profile/export/${kind}`);
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}

function isBundledRuntime() {
  return (
    window.location.protocol === 'file:' ||
    window.location.protocol === 'goe:' ||
    window.location.hostname === 'general-ontology-editor.local' ||
    window.location.hostname === 'visual-profile-editor.local'
  );
}

function loadLocalSchema() {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;

  try {
    return normalizeSchema(JSON.parse(raw) as SchemaModel);
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function saveLocalSchema(schema: SchemaModel) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeSchema(schema)));
}

function parseLinkmlSchema(text: string) {
  const parsed = yaml.load(text);
  if (!isSchemaMapping(parsed)) {
    throw new Error('Schema file must be a LinkML YAML/JSON mapping with classes and slots.');
  }

  return normalizeSchema(parsed);
}

function isSchemaMapping(value: unknown): value is SchemaModel {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return isObjectRecord(record.classes) && isObjectRecord(record.slots);
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function isLinkmlFile(name: string) {
  return /\.(ya?ml|json)$/i.test(name);
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'unknown error';
}
