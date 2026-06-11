import { useCallback, useState } from 'react';
import { ChevronUp, Folder, Home, RotateCcw, Server } from 'lucide-react';
import { browseProfileWorkspace, type ProfileTemplate, type ProfileWorkspace, type ProfileWorkspaceBrowse } from '../lib/schemaApi';

type Props = {
  loading: boolean;
  onClose: () => void;
  onLoadTemplate: (templateId: string) => void;
  onSetWorkspace: () => void;
  onWorkspaceInputChange: (directory: string) => void;
  templates: ProfileTemplate[];
  workspace: ProfileWorkspace | null;
  workspaceInput: string;
  workspaceSaving: boolean;
};

export function ProfileStartScreen({
  loading,
  onClose,
  onLoadTemplate,
  onSetWorkspace,
  onWorkspaceInputChange,
  templates,
  workspace,
  workspaceInput,
  workspaceSaving,
}: Props) {
  const [browserOpen, setBrowserOpen] = useState(false);
  const [browser, setBrowser] = useState<ProfileWorkspaceBrowse | null>(null);
  const [browserLoading, setBrowserLoading] = useState(false);
  const [browserError, setBrowserError] = useState('');

  const openBrowser = useCallback(
    async (directory?: string) => {
      setBrowserOpen(true);
      setBrowserLoading(true);
      setBrowserError('');
      try {
        const result = await browseProfileWorkspace(directory || workspaceInput || workspace?.directory || workspace?.default_directory);
        setBrowser(result);
      } catch (error) {
        setBrowserError(error instanceof Error ? error.message : 'Folder browser failed.');
      } finally {
        setBrowserLoading(false);
      }
    },
    [workspace, workspaceInput],
  );

  const chooseDirectory = useCallback(
    (directory: string) => {
      onWorkspaceInputChange(directory);
      setBrowserOpen(false);
    },
    [onWorkspaceInputChange],
  );

  return (
    <div className="modal-backdrop" role="presentation">
      <section aria-labelledby="profile-start-title" aria-modal="true" className="start-modal" role="dialog">
        <div>
          <h2 id="profile-start-title">Select Base Profile</h2>
          <p>Start from an empty profile, DCAT, DCAT-AP, or the Construct-DCAT starter profile.</p>
        </div>
        <section aria-label="Active schema folder" className="workspace-settings">
          <label htmlFor="workspace-directory">Active Schema Folder</label>
          <div className="workspace-settings__row">
            <input
              disabled={workspaceSaving}
              id="workspace-directory"
              onChange={(event) => onWorkspaceInputChange(event.target.value)}
              placeholder={workspace?.default_directory ?? '.vpe-workspace/profiles'}
              type="text"
              value={workspaceInput}
            />
            <button disabled={workspaceSaving || !workspaceInput.trim()} onClick={onSetWorkspace} type="button">
              Use Folder
            </button>
            <button disabled={workspaceSaving} onClick={() => void openBrowser()} type="button">
              <Folder size={16} />
              Browse
            </button>
          </div>
          {workspace ? <span>{workspace.schema_path}</span> : null}
          {browserOpen ? (
            <div className="workspace-browser">
              <div className="workspace-browser__header">
                <strong>{browser?.directory ?? 'Folders'}</strong>
                <button disabled={!browser || browserLoading} onClick={() => browser ? chooseDirectory(browser.directory) : undefined} type="button">
                  Use This Folder
                </button>
              </div>
              {browser ? (
                <div className="workspace-browser__shortcuts">
                  <button disabled={browserLoading || !browser.parent_directory} onClick={() => browser.parent_directory ? void openBrowser(browser.parent_directory) : undefined} type="button">
                    <ChevronUp size={15} />
                    Parent
                  </button>
                  <button disabled={browserLoading} onClick={() => void openBrowser(browser.home_directory)} type="button">
                    <Home size={15} />
                    Home
                  </button>
                  <button disabled={browserLoading} onClick={() => void openBrowser(browser.default_directory)} type="button">
                    <RotateCcw size={15} />
                    Default
                  </button>
                  <button disabled={browserLoading} onClick={() => void openBrowser(browser.repo_directory)} type="button">
                    <Server size={15} />
                    Repo
                  </button>
                </div>
              ) : null}
              {browserLoading ? <span>Loading folders...</span> : null}
              {browserError ? <span className="workspace-browser__error">{browserError}</span> : null}
              {browser && !browserLoading ? (
                <div className="workspace-browser__list">
                  {browser.entries.length ? browser.entries.map((entry) => (
                    <button key={entry.path} onClick={() => void openBrowser(entry.path)} type="button">
                      <Folder size={15} />
                      <span>{entry.name}</span>
                    </button>
                  )) : <span>No folders here.</span>}
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
        <div className="template-grid">
          {templates.map((template) => (
            <button disabled={loading} key={template.id} onClick={() => onLoadTemplate(template.id)} type="button">
              <strong>{template.title}</strong>
              <span>{template.description}</span>
            </button>
          ))}
        </div>
        <div className="import-modal__actions">
          <button disabled={loading} onClick={onClose} type="button">
            Continue Current Profile
          </button>
        </div>
      </section>
    </div>
  );
}
