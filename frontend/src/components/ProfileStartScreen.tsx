import type { ProfileTemplate } from '../lib/schemaApi';

type Props = {
  loading: boolean;
  onClose: () => void;
  onLoadTemplate: (templateId: string) => void;
  templates: ProfileTemplate[];
};

export function ProfileStartScreen({ loading, onClose, onLoadTemplate, templates }: Props) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section aria-labelledby="profile-start-title" aria-modal="true" className="start-modal" role="dialog">
        <div>
          <h2 id="profile-start-title">Select Base Profile</h2>
          <p>Start from an empty profile, DCAT, DCAT-AP, or the Construct-DCAT starter profile.</p>
        </div>
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
