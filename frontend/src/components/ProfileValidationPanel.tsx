type ValidationResult = {
  valid: boolean;
  errors: Array<Record<string, string>>;
  warnings: Array<Record<string, string>>;
  suggestions: Array<Record<string, string>>;
};

type Props = {
  onClose: () => void;
  result: ValidationResult;
};

export function ProfileValidationPanel({ onClose, result }: Props) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section aria-labelledby="validation-title" aria-modal="true" className="validation-modal" role="dialog">
        <div className="validation-modal__header">
          <h2 id="validation-title">Profile Validation</h2>
          <button onClick={onClose} type="button">Close</button>
        </div>
        <p className={result.valid ? 'validation-ok' : 'validation-bad'}>
          {result.valid ? 'Profile is valid.' : `${result.errors.length} error(s) need attention.`}
        </p>
        <IssueList items={result.errors} title="Errors" />
        <IssueList items={result.warnings} title="Warnings" />
        <IssueList items={result.suggestions} title="Suggestions" />
      </section>
    </div>
  );
}

function IssueList({ items, title }: { items: Array<Record<string, string>>; title: string }) {
  return (
    <section>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="muted">None.</p>
      ) : (
        <div className="issue-list">
          {items.map((item, index) => (
            <article key={`${item.code}-${index}`}>
              <strong>{item.code}</strong>
              <span>{item.message}</span>
              <small>{item.path}</small>
              {item.suggested_fix ? <em>{item.suggested_fix}</em> : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export type { ValidationResult };
