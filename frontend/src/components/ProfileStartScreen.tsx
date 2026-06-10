import type { ProfileTemplate, ProfileWorkspace } from '../lib/schemaApi';

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
          </div>
          {workspace ? <span>{workspace.schema_path}</span> : null}
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
