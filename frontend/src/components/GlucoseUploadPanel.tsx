import type { GlucoseUpload } from "../types";

/**
 * Defines props for rendering glucose uploads.
 */
interface GlucoseUploadPanelProps {
  uploads: GlucoseUpload[];
}

/**
 * Renders uploaded glucose screenshots and their descriptive summaries.
 *
 * @param props - Glucose upload panel props.
 * @returns The glucose panel component.
 * @example
 * <GlucoseUploadPanel uploads={dayLog.glucose_uploads} />
 */
export function GlucoseUploadPanel(props: GlucoseUploadPanelProps): JSX.Element {
  return (
    <article className="panel" aria-label="Glucose upload panel">
      <header className="panel__header">
        <h2>Glucose screenshots</h2>
        <p className="panel__subtext">Upload preview and AI observation summary</p>
      </header>

      {props.uploads.length === 0 ? (
        <p className="empty-state">No glucose screenshots yet.</p>
      ) : (
        <ul className="glucose-list">
          {props.uploads.map((upload) => (
            <li key={upload.id} className="glucose-card">
              <img className="glucose-card__image" src={upload.image_url} alt={upload.file_name} />
              <div>
                <p className="glucose-card__title">{upload.file_name}</p>
                <p className="glucose-card__meta">{new Date(upload.uploaded_at).toLocaleString()}</p>
                <p>{upload.ai_summary ?? "No AI summary yet."}</p>
                {upload.user_note ? <p className="glucose-card__meta">Note: {upload.user_note}</p> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
