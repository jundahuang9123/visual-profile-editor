import { useCallback, useEffect, useMemo, useState } from 'react';
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
import { Toolbar } from './components/Toolbar';
import { useEditorStore } from './store';
import './styles.css';

const nodeTypes = { classNode: ClassNode };

function EditorCanvas() {
  const getFlow = useEditorStore((state) => state.getFlow);
  const selected = useEditorStore((state) => state.selected);
  const setSelected = useEditorStore((state) => state.setSelected);
  const onNodesChange = useEditorStore((state) => state.onNodesChange);
  const connectClasses = useEditorStore((state) => state.connectClasses);
  const yaml = useEditorStore((state) => state.yaml());
  const flow = getFlow();

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

  return (
    <div className="workspace">
      <section className="canvas">
        <ReactFlow
          nodes={flow.nodes}
          edges={flow.edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={() => setSelected(null)}
          fitView
        >
          <Background color="#d4dbe8" gap={18} />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
      </section>
      <Inspector />
      <section className="yaml-panel">
        <div className="yaml-panel__header">
          <h2>Live LinkML YAML</h2>
          <span>{selected ? `${selected.kind}: ${selected.id}` : 'Schema output'}</span>
        </div>
        <Editor
          height="100%"
          language="yaml"
          theme="vs-dark"
          value={yaml}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 12,
            wordWrap: 'on',
            scrollBeyondLastLine: false,
          }}
        />
      </section>
    </div>
  );
}

export default function App() {
  const loadSchema = useEditorStore((state) => state.loadSchema);
  const yaml = useEditorStore((state) => state.yaml);
  const [status, setStatus] = useState('Loading schema...');

  useEffect(() => {
    fetch('/api/schema/model')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((schema) => {
        loadSchema(schema);
        setStatus('Loaded');
      })
      .catch((err) => {
        setStatus(`Load failed: ${err.message}`);
      });
  }, [loadSchema]);

  const saveSchema = useCallback(async () => {
    setStatus('Saving...');
    const res = await fetch('/api/schema/linkml', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ yaml: yaml() }),
    });
    if (!res.ok) {
      const detail = await res.text();
      setStatus(`Save failed: ${detail}`);
      return;
    }
    setStatus('Saved to schemas/construct_dcat.yaml');
  }, [yaml]);

  const provider = useMemo(
    () => (
      <ReactFlowProvider>
        <Toolbar onSave={saveSchema} status={status} />
        <EditorCanvas />
      </ReactFlowProvider>
    ),
    [saveSchema, status],
  );

  return provider;
}
