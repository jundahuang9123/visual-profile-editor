import { Download, FileDown, Plus, Save, Tags } from 'lucide-react';
import { useEditorStore } from '../store';

export type ExportKind = 'rdf' | 'shacl';

type ToolbarProps = {
  onExport: (kind: ExportKind) => Promise<void>;
  onSave: () => Promise<void>;
  status: string;
};

export function Toolbar({ onExport, onSave, status }: ToolbarProps) {
  const addClass = useEditorStore((state) => state.addClass);
  const addEnum = useEditorStore((state) => state.addEnum);
  const yaml = useEditorStore((state) => state.yaml());

  function downloadYaml() {
    const blob = new Blob([yaml], { type: 'application/yaml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'construct_dcat.yaml';
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <header className="toolbar">
      <div>
        <h1>Construct-DCAT Visual Schema Editor</h1>
        <p>React Flow canvas, state-first schema modeling, live LinkML YAML.</p>
      </div>
      <div className="toolbar__actions">
        <button onClick={addClass} title="Add class">
          <Plus size={16} />
          Class
        </button>
        <button onClick={addEnum} title="Add enum">
          <Tags size={16} />
          Enum
        </button>
        <button onClick={downloadYaml} title="Download YAML">
          <Download size={16} />
          YAML
        </button>
        <button onClick={() => onExport('rdf')} title="Export RDF Turtle">
          <FileDown size={16} />
          RDF
        </button>
        <button onClick={() => onExport('shacl')} title="Export SHACL Turtle">
          <FileDown size={16} />
          SHACL
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
