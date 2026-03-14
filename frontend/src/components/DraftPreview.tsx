import type { AssistantDraft, RequestState } from "../types";

/**
 * Defines props for draft preview and save confirmation controls.
 */
interface DraftPreviewProps {
  draft: AssistantDraft | null;
  saveState: RequestState;
  saveError: string | null;
  saveSuccessMessage: string | null;
  onSaveDraft: () => void;
  onDiscardDraft: () => void;
}

/**
 * Renders the AI draft preview and final save confirmation action.
 *
 * @param props - Draft preview props.
 * @returns The draft preview panel.
 * @example
 * <DraftPreview draft={draft} saveState={saveState} onSaveDraft={saveDraft} onDiscardDraft={clearDraft} />
 */
export function DraftPreview(props: DraftPreviewProps): JSX.Element {
  if (!props.draft) {
    return (
      <article className="panel" aria-label="Draft preview">
        <header className="panel__header">
          <h2>Draft preview</h2>
        </header>
        <p className="empty-state">No draft yet. Generate one from the composer to review before saving.</p>
        {props.saveSuccessMessage ? <p className="message message--success">{props.saveSuccessMessage}</p> : null}
      </article>
    );
  }

  return (
    <article className="panel" aria-label="Draft preview">
      <header className="panel__header">
        <h2>Draft preview</h2>
        <p className="panel__subtext">Confirm this draft before saving it to the day log.</p>
      </header>

      <p>
        <strong>Source:</strong> {props.draft.source_text}
      </p>
      <p>
        <strong>Confidence:</strong> {Math.round(props.draft.confidence * 100)}%
      </p>

      <ul className="draft-items">
        {props.draft.items.map((item, index) => (
          <li key={`${item.name}-${index}`}>
            {item.quantity} {item.name} ({item.calories} kcal)
          </li>
        ))}
      </ul>

      <p className="draft-totals">
        Totals: {props.draft.totals.calories} kcal • {props.draft.totals.protein_g}g protein • {props.draft.totals.carbs_g}g carbs • {props.draft.totals.fat_g}g fat
      </p>

      {props.draft.assumptions.length > 0 ? (
        <div>
          <h3>Assumptions</h3>
          <ul>
            {props.draft.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {props.draft.warnings.length > 0 ? (
        <div>
          <h3>Warnings</h3>
          <ul>
            {props.draft.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="composer-actions">
        <button type="button" className="secondary-button" onClick={props.onDiscardDraft}>
          Discard draft
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={props.onSaveDraft}
          disabled={props.saveState === "loading"}
        >
          {props.saveState === "loading" ? "Saving..." : "Save meal to day"}
        </button>
      </div>

      {props.saveError ? <p className="message message--error">{props.saveError}</p> : null}
      {props.saveSuccessMessage ? <p className="message message--success">{props.saveSuccessMessage}</p> : null}
    </article>
  );
}
