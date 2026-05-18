import { useRef } from 'react';
import { Download, Eye, EyeOff, FileArchive, FileDown, ListChecks, Plus, Save, Tags, Upload } from 'lucide-react';
import { downloadText } from '../lib/schemaApi';
import { useEditorStore } from '../store';

export type ExportKind = 'rdf' | 'shacl' | 'jsonschema' | 'linkml' | 'package';

type ToolbarProps = {
  onExport: (kind: ExportKind) => Promise<void>;
  onImport: (file: File) => void;
  onSave: () => Promise<void>;
  onShowTemplates: () => void;
  onToggleYaml: () => void;
  onValidate: () => Promise<void>;
  status: string;
  yamlVisible: boolean;
};

export function Toolbar({ onExport, onImport, onSave, onShowTemplates, onToggleYaml, onValidate, status, yamlVisible }: ToolbarProps) {
  const addClass = useEditorStore((state) => state.addClass);
  const addEnum = useEditorStore((state) => state.addEnum);
  const yaml = useEditorStore((state) => state.yaml());
  const fileInput = useRef<HTMLInputElement>(null);

  function downloadYaml() {
    downloadText(yaml, 'profile.yaml', 'application/yaml');
  }

  return (
    <header className="toolbar">
      <div>
        <h1>Construct-DCAT Profile Editor</h1>
        <p>Select a base profile, constrain DCAT terms, add semantic anchors, validate, and export profile artifacts.</p>
      </div>
      <div className="toolbar__actions">
        <button onClick={onShowTemplates} title="Choose profile template">
          <FileArchive size={16} />
          Templates
        </button>
        <button onClick={addClass} title="Add class">
          <Plus size={16} />
          Class Profile
        </button>
        <button onClick={addEnum} title="Add enum">
          <Tags size={16} />
          Enum
        </button>
        <button onClick={downloadYaml} title="Download YAML">
          <Download size={16} />
          Profile YAML
        </button>
        <button aria-pressed={yamlVisible} onClick={onToggleYaml} title={yamlVisible ? 'Hide live YAML' : 'Show live YAML'}>
          {yamlVisible ? <EyeOff size={16} /> : <Eye size={16} />}
          Preview
        </button>
        <button onClick={() => fileInput.current?.click()} title="Upload RDF, OWL, or SHACL">
          <Upload size={16} />
          Upload
        </button>
        <input
          ref={fileInput}
          accept=".yaml,.yml,.ttl,.rdf,.owl,.xml,.jsonld,.json,.nt,.n3,.trig,.shacl"
          hidden
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = '';
            if (file) {
              void onImport(file);
            }
          }}
        />
        <button onClick={() => onExport('rdf')} title="Export RDF Turtle">
          <FileDown size={16} />
          RDF
        </button>
        <button onClick={() => onExport('shacl')} title="Export SHACL Turtle">
          <FileDown size={16} />
          SHACL
        </button>
        <button onClick={onValidate} title="Validate Construct-DCAT profile">
          <ListChecks size={16} />
          Validate
        </button>
        <button onClick={() => onExport('package')} title="Export Construct-DCAT profile package">
          <FileArchive size={16} />
          Package
        </button>
        <button className="primary" onClick={onSave} title="Save YAML">
          <Save size={16} />
          Save
        </button>
      </div>
      <span className="status">{status}</span>
    </header>
  );
}
