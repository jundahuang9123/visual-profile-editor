import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Connection,
  type NodeMouseHandler,
} from '@xyflow/react';
import Editor from '@monaco-editor/react';
import '@xyflow/react/dist/style.css';
import { ClassNode } from './components/ClassNode';
import { Inspector } from './components/Inspector';
import { ProfileStartScreen } from './components/ProfileStartScreen';
import { ProfileValidationPanel, type ValidationResult } from './components/ProfileValidationPanel';
import { RequirementWorkbench } from './components/RequirementWorkbench';
import { Toolbar, type ExportKind } from './components/Toolbar';
import {
  exportSchema as exportSchemaFile,
  importSchemaFile,
  loadPreview,
  loadProfileWorkspace,
  loadProfileTemplate,
  loadProfileTemplates,
  loadSchemaModel,
  saveSchemaYaml,
  setProfileWorkspace,
  validateProfile,
  type ProfileWorkspace,
  type ProfileTemplate,
} from './lib/schemaApi';
import { schemaToFlow } from './lib/schema';
import { useEditorStore } from './store';
import type { SchemaModel } from './types';
import './styles.css';

const nodeTypes = { classNode: ClassNode };

type ImportMode = 'override' | 'merge';

const MIN_YAML_WIDTH = 260;
const MAX_YAML_WIDTH = 640;

type EditorCanvasProps = {
  onPreviewTabChange: (tab: PreviewTab) => void;
  previewLoading: boolean;
  previewTab: PreviewTab;
  previewText: string;
  yamlVisible: boolean;
};

type PreviewTab = 'linkml' | 'shacl' | 'jsonschema' | 'rdf';
type WorkbenchTab = 'profile' | 'requirements' | 'reuse' | 'validation' | 'export';

function EditorCanvas({ onPreviewTabChange, previewLoading, previewTab, previewText, yamlVisible }: EditorCanvasProps) {
  const workspaceRef = useRef<HTMLDivElement>(null);
  const schema = useEditorStore((state) => state.schema);
  const positions = useEditorStore((state) => state.positions);
  const selected = useEditorStore((state) => state.selected);
  const setSelected = useEditorStore((state) => state.setSelected);
  const onNodesChange = useEditorStore((state) => state.onNodesChange);
  const connectClasses = useEditorStore((state) => state.connectClasses);
  const yaml = useEditorStore((state) => state.yaml());
  const flow = useMemo(() => schemaToFlow(schema, positions), [schema, positions]);
  const [yamlWidth, setYamlWidth] = useState(() => {
    const storedWidth = Number(window.localStorage.getItem('yamlPanelWidth'));
    return Number.isFinite(storedWidth) ? Math.min(MAX_YAML_WIDTH, Math.max(MIN_YAML_WIDTH, storedWidth)) : 380;
  });
  const [resizingYaml, setResizingYaml] = useState(false);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      setSelected({ kind: 'class', id: node.id });
    },
    [setSelected],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      connectClasses(connection);
    },
    [connectClasses],
  );

  useEffect(() => {
    window.localStorage.setItem('yamlPanelWidth', String(yamlWidth));
  }, [yamlWidth]);

  useEffect(() => {
    if (!resizingYaml) return;

    function onPointerMove(event: PointerEvent) {
      const bounds = workspaceRef.current?.getBoundingClientRect();
      if (!bounds) return;

      const nextWidth = event.clientX - bounds.left;
      setYamlWidth(Math.min(MAX_YAML_WIDTH, Math.max(MIN_YAML_WIDTH, nextWidth)));
    }

    function onPointerUp() {
      setResizingYaml(false);
    }

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [resizingYaml]);

  const workspaceStyle = { '--yaml-width': `${yamlWidth}px` } as CSSProperties;

  return (
    <div
      className={`workspace ${yamlVisible ? '' : 'workspace--yaml-hidden'} ${resizingYaml ? 'workspace--resizing' : ''}`}
      ref={workspaceRef}
      style={workspaceStyle}
    >
      {yamlVisible ? (
        <section className="yaml-panel">
          <div className="yaml-panel__header">
            <h2>Profile YAML / LinkML</h2>
            <span>{selected ? `${selected.kind}: ${selected.id}` : 'Profile output'}</span>
          </div>
          <div className="preview-tabs">
            {(['linkml', 'shacl', 'jsonschema', 'rdf'] as PreviewTab[]).map((tab) => (
              <button className={previewTab === tab ? 'active' : undefined} key={tab} onClick={() => onPreviewTabChange(tab)} type="button">
                {tab === 'linkml' ? 'Profile YAML' : tab === 'jsonschema' ? 'JSON Schema' : tab.toUpperCase()}
              </button>
            ))}
          </div>
          <Editor
            height="100%"
            language={previewTab === 'jsonschema' ? 'json' : previewTab === 'linkml' ? 'yaml' : 'turtle'}
            theme="vs-dark"
            value={previewTab === 'linkml' ? yaml : previewLoading ? 'Loading preview...' : previewText}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 12,
              wordWrap: 'on',
              scrollBeyondLastLine: false,
            }}
          />
          <div
            aria-label="Resize live YAML panel"
            aria-orientation="vertical"
            className="yaml-panel__resizer"
            onKeyDown={(event) => {
              if (event.key === 'ArrowLeft') {
                event.preventDefault();
                setYamlWidth((width) => Math.max(MIN_YAML_WIDTH, width - 24));
              }
              if (event.key === 'ArrowRight') {
                event.preventDefault();
                setYamlWidth((width) => Math.min(MAX_YAML_WIDTH, width + 24));
              }
            }}
            onPointerDown={(event) => {
              event.preventDefault();
              setResizingYaml(true);
            }}
            role="separator"
            tabIndex={0}
            title="Drag to resize live YAML"
          />
        </section>
      ) : null}
      <section className="canvas">
        <ReactFlow
          nodes={flow.nodes}
          edges={flow.edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={() => setSelected(null)}
          nodesDraggable
          fitView
        >
          <Background color="#d4dbe8" gap={18} />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
      </section>
      <Inspector />
    </div>
  );
}

export default function App() {
  const schema = useEditorStore((state) => state.schema);
  const loadSchema = useEditorStore((state) => state.loadSchema);
  const mergeSchema = useEditorStore((state) => state.mergeSchema);
  const yaml = useEditorStore((state) => state.yaml);
  const [status, setStatus] = useState('Loading schema...');
  const [yamlVisible, setYamlVisible] = useState(true);
  const [pendingUpload, setPendingUpload] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [templates, setTemplates] = useState<ProfileTemplate[]>([]);
  const [templatesOpen, setTemplatesOpen] = useState(true);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [workspace, setWorkspace] = useState<ProfileWorkspace | null>(null);
  const [workspaceInput, setWorkspaceInput] = useState('');
  const [workspaceSaving, setWorkspaceSaving] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [previewTab, setPreviewTab] = useState<PreviewTab>('linkml');
  const [previewText, setPreviewText] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<WorkbenchTab>('profile');

  useEffect(() => {
    loadSchemaModel()
      .then((result) => {
        loadSchema(result.schema);
        setStatus(result.message);
      })
      .catch((err) => {
        setStatus(`Load failed: ${err.message}`);
      });
  }, [loadSchema]);

  useEffect(() => {
    loadProfileTemplates()
      .then(setTemplates)
      .catch((error) => {
        setStatus(`Template load failed: ${error instanceof Error ? error.message : 'unknown error'}`);
      });
  }, []);

  useEffect(() => {
    loadProfileWorkspace()
      .then((result) => {
        setWorkspace(result);
        setWorkspaceInput(result.directory);
      })
      .catch((error) => {
        setStatus(`Workspace load failed: ${error instanceof Error ? error.message : 'unknown error'}`);
      });
  }, []);

  useEffect(() => {
    if (!yamlVisible || previewTab === 'linkml') return;

    setPreviewLoading(true);
    loadPreview(previewTab)
      .then(setPreviewText)
      .catch((error) => setPreviewText(`Preview failed: ${error instanceof Error ? error.message : 'unknown error'}`))
      .finally(() => setPreviewLoading(false));
  }, [previewTab, yamlVisible, schema]);

  const saveSchema = useCallback(async () => {
    setStatus('Saving...');
    try {
      const result = await saveSchemaYaml(yaml());
      setStatus(result.message);
    } catch (error) {
      setStatus(`Save failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }, [yaml]);

  const exportSchema = useCallback(async (kind: ExportKind) => {
    const label = kind === 'rdf' ? 'RDF' : kind === 'shacl' ? 'SHACL' : kind === 'package' ? 'profile package' : kind.toUpperCase();
    setStatus(`Exporting ${label}...`);
    try {
      await exportSchemaFile(schema, kind);
      setStatus(`${label} exported`);
    } catch (error) {
      setStatus(`${label} export failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }, [schema]);

  const runValidation = useCallback(async () => {
    setStatus('Validating profile...');
    try {
      const result = await validateProfile(schema);
      setValidationResult(result);
      setStatus(result.valid ? 'Profile validation passed' : `Profile validation found ${result.errors.length} error(s)`);
    } catch (error) {
      setStatus(`Validation failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }, [schema]);

  const selectTemplate = useCallback(
    async (templateId: string) => {
      setTemplateLoading(true);
      setStatus(`Loading ${templateId}...`);
      try {
        const schema = await loadProfileTemplate(templateId);
        loadSchema(schema);
        setTemplatesOpen(false);
        setStatus(`Loaded ${templateId}.`);
      } catch (error) {
        setStatus(`Template load failed: ${error instanceof Error ? error.message : 'unknown error'}`);
      } finally {
        setTemplateLoading(false);
      }
    },
    [loadSchema],
  );

  const updateWorkspace = useCallback(async () => {
    const directory = workspaceInput.trim();
    if (!directory) {
      setStatus('Workspace directory is required.');
      return;
    }

    setWorkspaceSaving(true);
    setStatus('Updating profile workspace...');
    try {
      const result = await setProfileWorkspace(directory);
      setWorkspace(result.workspace);
      setWorkspaceInput(result.workspace.directory);
      loadSchema(result.schema);
      setStatus(`Using workspace ${result.workspace.directory}`);
    } catch (error) {
      setStatus(`Workspace update failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    } finally {
      setWorkspaceSaving(false);
    }
  }, [loadSchema, workspaceInput]);

  const selectImportFile = useCallback((file: File) => {
    setPendingUpload(file);
  }, []);

  const importSchema = useCallback(
    async (mode: ImportMode) => {
      if (!pendingUpload) return;

      setImporting(true);
      setStatus(`Importing ${pendingUpload.name}...`);
      try {
        const schema = (await importSchemaFile(pendingUpload)) as SchemaModel;
        if (mode === 'merge') {
          mergeSchema(schema);
          setStatus(`Merged ${pendingUpload.name} into the current diagram.`);
        } else {
          loadSchema(schema);
          setStatus(`Imported ${pendingUpload.name}. Review the diagram, then Save to persist YAML.`);
        }
        setPendingUpload(null);
      } catch (err) {
        setStatus(`Import failed: ${err instanceof Error ? err.message : 'unknown error'}`);
      } finally {
        setImporting(false);
      }
    },
    [loadSchema, mergeSchema, pendingUpload],
  );

  const editorVisible = activeTab === 'profile' || activeTab === 'validation' || activeTab === 'export';

  const provider = useMemo(
    () => (
      <ReactFlowProvider>
        <nav aria-label="Workbench modules" className="module-tabs">
          {[
            { id: 'profile', label: 'Profile Editor' },
            { id: 'requirements', label: 'Requirement Extraction' },
            { id: 'reuse', label: 'Reuse Recommendations' },
            { id: 'validation', label: 'Validation' },
            { id: 'export', label: 'Export' },
          ].map((tab) => (
            <button
              className={activeTab === tab.id ? 'active' : undefined}
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as WorkbenchTab);
                if (tab.id === 'validation') void runValidation();
              }}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </nav>
        {editorVisible ? (
          <>
            <Toolbar
              onExport={exportSchema}
              onImport={selectImportFile}
              onSave={saveSchema}
              onShowTemplates={() => setTemplatesOpen(true)}
              onToggleYaml={() => setYamlVisible((visible) => !visible)}
              onValidate={runValidation}
              status={status}
              yamlVisible={yamlVisible}
            />
            <EditorCanvas
              onPreviewTabChange={setPreviewTab}
              previewLoading={previewLoading}
              previewTab={previewTab}
              previewText={previewText}
              yamlVisible={yamlVisible}
            />
          </>
        ) : (
          <RequirementWorkbench initialView={activeTab === 'reuse' ? 'reuse' : 'requirements'} onStatus={setStatus} />
        )}
        {editorVisible && templatesOpen ? (
          <ProfileStartScreen
            loading={templateLoading}
            onClose={() => setTemplatesOpen(false)}
            onLoadTemplate={(templateId) => void selectTemplate(templateId)}
            onSetWorkspace={() => void updateWorkspace()}
            onWorkspaceInputChange={setWorkspaceInput}
            templates={templates}
            workspace={workspace}
            workspaceInput={workspaceInput}
            workspaceSaving={workspaceSaving}
          />
        ) : null}
        {validationResult ? (
          <ProfileValidationPanel onClose={() => setValidationResult(null)} result={validationResult} />
        ) : null}
        {pendingUpload ? (
          <div className="modal-backdrop" role="presentation">
            <section aria-labelledby="import-modal-title" aria-modal="true" className="import-modal" role="dialog">
              <div>
                <h2 id="import-modal-title">Import {pendingUpload.name}</h2>
                <p>Replace the current profile diagram, or merge this semantic resource into what is already open.</p>
              </div>
              <div className="import-modal__actions">
                <button disabled={importing} onClick={() => setPendingUpload(null)} type="button">
                  Cancel
                </button>
                <button disabled={importing} onClick={() => void importSchema('merge')} type="button">
                  Merge
                </button>
                <button className="primary" disabled={importing} onClick={() => void importSchema('override')} type="button">
                  Override
                </button>
              </div>
            </section>
          </div>
        ) : null}
      </ReactFlowProvider>
    ),
    [
      activeTab,
      editorVisible,
      exportSchema,
      importSchema,
      importing,
      pendingUpload,
      previewLoading,
      previewTab,
      previewText,
      runValidation,
      saveSchema,
      selectImportFile,
      selectTemplate,
      status,
      templateLoading,
      templates,
      templatesOpen,
      updateWorkspace,
      validationResult,
      workspace,
      workspaceInput,
      workspaceSaving,
      yamlVisible,
    ],
  );

  return provider;
}
