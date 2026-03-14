import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ApiError,
  createMealDraft,
  editMealEntry,
  fetchDayLog,
  saveMealDraft,
  syncRecentActivities,
  uploadGlucoseScreenshot
} from "./api/client";
import type { AssistantDraft, DayLogResponse, MealEntry } from "./types";

type AsyncState = "idle" | "loading" | "success" | "error";

interface StatusMessage {
  state: AsyncState;
  message: string;
}

const MS_PER_DAY = 86_400_000;

/**
 * Return a YYYY-MM-DD string for current local day.
 */
function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Return true when date is within the rolling recent sync window.
 */
function isRecentDay(dayIso: string): boolean {
  const selected = new Date(`${dayIso}T00:00:00`);
  const now = new Date();
  const current = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const difference = Math.floor((current.getTime() - selected.getTime()) / MS_PER_DAY);
  return difference >= 0 && difference <= 6;
}

/**
 * Add or subtract calendar days from an ISO date.
 */
function shiftIsoDate(dayIso: string, dayDelta: number): string {
  const target = new Date(`${dayIso}T00:00:00`);
  target.setDate(target.getDate() + dayDelta);
  return target.toISOString().slice(0, 10);
}

/**
 * Render the end-to-end day log flow using live backend APIs.
 */
export default function App(): JSX.Element {
  const [selectedDate, setSelectedDate] = useState<string>(todayIsoDate());
  const [dayLog, setDayLog] = useState<DayLogResponse | null>(null);

  const [dayStatus, setDayStatus] = useState<StatusMessage>({
    state: "loading",
    message: "Loading day log..."
  });
  const [syncStatus, setSyncStatus] = useState<StatusMessage>({
    state: "idle",
    message: ""
  });

  const [mealNote, setMealNote] = useState<string>("");
  const [draft, setDraft] = useState<AssistantDraft | null>(null);
  const [draftStatus, setDraftStatus] = useState<StatusMessage>({ state: "idle", message: "" });
  const [saveStatus, setSaveStatus] = useState<StatusMessage>({ state: "idle", message: "" });

  const [editingMeal, setEditingMeal] = useState<MealEntry | null>(null);
  const [editingText, setEditingText] = useState<string>("");
  const [editStatus, setEditStatus] = useState<StatusMessage>({ state: "idle", message: "" });

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadNote, setUploadNote] = useState<string>("");
  const [uploadStatus, setUploadStatus] = useState<StatusMessage>({ state: "idle", message: "" });

  const autoSyncEnabled = import.meta.env.MODE !== "test";

  const loadDayLog = useCallback(async (dayIso: string) => {
    setDayStatus({ state: "loading", message: "Loading day log..." });

    try {
      const payload = await fetchDayLog(dayIso);
      setDayLog(payload);
      setDayStatus({ state: "success", message: "" });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Failed to load day log.";
      setDayStatus({ state: "error", message });
    }
  }, []);

  const runRecentSync = useCallback(
    async (reloadDayAfterSync: boolean) => {
      setSyncStatus({ state: "loading", message: "Syncing recent activities..." });

      try {
        const payload = await syncRecentActivities();
        setSyncStatus({
          state: "success",
          message: `Recent sync complete. Imported ${payload.imported_count}, updated ${payload.updated_count}.`
        });

        if (reloadDayAfterSync) {
          await loadDayLog(selectedDate);
        }
      } catch (error) {
        const message = error instanceof ApiError ? error.message : "Sync failed.";
        setSyncStatus({ state: "error", message });
      }
    },
    [loadDayLog, selectedDate]
  );

  useEffect(() => {
    void loadDayLog(selectedDate);
  }, [loadDayLog, selectedDate]);

  useEffect(() => {
    if (!autoSyncEnabled || !isRecentDay(selectedDate)) {
      setSyncStatus({ state: "idle", message: "" });
      return;
    }

    void runRecentSync(true);
  }, [autoSyncEnabled, runRecentSync, selectedDate]);

  const groupedMeals = useMemo(() => {
    if (!dayLog) {
      return {
        breakfast: [],
        lunch: [],
        dinner: [],
        snacks: []
      } as Record<"breakfast" | "lunch" | "dinner" | "snacks", MealEntry[]>;
    }

    return {
      breakfast: dayLog.meal_entries.filter((entry) => entry.meal_slot === "breakfast"),
      lunch: dayLog.meal_entries.filter((entry) => entry.meal_slot === "lunch"),
      dinner: dayLog.meal_entries.filter((entry) => entry.meal_slot === "dinner"),
      snacks: dayLog.meal_entries.filter((entry) => entry.meal_slot === "snacks")
    };
  }, [dayLog]);

  async function handleGenerateDraft(): Promise<void> {
    if (!mealNote.trim()) {
      setDraftStatus({ state: "error", message: "Add a meal note before generating a draft." });
      return;
    }

    setDraftStatus({ state: "loading", message: "Generating draft..." });
    setSaveStatus({ state: "idle", message: "" });

    try {
      const payload = await createMealDraft(selectedDate, mealNote.trim());
      setDraft(payload);
      setDraftStatus({ state: "success", message: "Draft ready for review." });
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Draft generation failed.";
      setDraftStatus({ state: "error", message });
    }
  }

  async function handleSaveDraft(): Promise<void> {
    if (!draft) {
      return;
    }

    setSaveStatus({ state: "loading", message: "Saving meal..." });

    try {
      await saveMealDraft(selectedDate, draft.normalized_payload);
      setSaveStatus({ state: "success", message: "Meal saved." });
      setDraft(null);
      setMealNote("");
      await loadDayLog(selectedDate);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Could not save meal.";
      setSaveStatus({ state: "error", message });
    }
  }

  async function handleEditMealSave(): Promise<void> {
    if (!editingMeal || !editingText.trim()) {
      setEditStatus({ state: "error", message: "Meal text cannot be empty." });
      return;
    }

    setEditStatus({ state: "loading", message: "Saving edit..." });

    try {
      await editMealEntry(selectedDate, editingMeal.id, editingText.trim());
      setEditStatus({ state: "success", message: "Meal updated." });
      setEditingMeal(null);
      setEditingText("");
      await loadDayLog(selectedDate);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Meal edit failed.";
      setEditStatus({ state: "error", message });
    }
  }

  async function handleGlucoseUpload(): Promise<void> {
    if (!uploadFile) {
      setUploadStatus({ state: "error", message: "Choose an image before uploading." });
      return;
    }

    setUploadStatus({ state: "loading", message: "Uploading screenshot..." });

    try {
      await uploadGlucoseScreenshot(selectedDate, uploadFile, uploadNote);
      setUploadStatus({ state: "success", message: "Screenshot uploaded." });
      setUploadFile(null);
      setUploadNote("");
      await loadDayLog(selectedDate);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Upload failed.";
      setUploadStatus({ state: "error", message });
    }
  }

  return (
    <div className="app-shell">
      <header className="page-header">
        <h1>Personal Endurance Trainer Log</h1>
        <p>Track meals, recent Strava activity, and glucose screenshots in one daily timeline.</p>
      </header>

      <section className="panel day-controls">
        <h2>Day Selector</h2>
        <div className="day-control-row">
          <button type="button" onClick={() => setSelectedDate((current) => shiftIsoDate(current, -1))}>
            Previous Day
          </button>
          <input
            aria-label="Selected day"
            type="date"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
          />
          <button type="button" onClick={() => setSelectedDate((current) => shiftIsoDate(current, 1))}>
            Next Day
          </button>
        </div>

        {dayStatus.state === "loading" && <p className="status loading">{dayStatus.message}</p>}
        {dayStatus.state === "error" && (
          <div className="status error" role="alert">
            <p>{dayStatus.message}</p>
            <button type="button" onClick={() => void loadDayLog(selectedDate)}>
              Retry Day Load
            </button>
          </div>
        )}

        {syncStatus.state === "loading" && <p className="status loading">{syncStatus.message}</p>}
        {syncStatus.state === "success" && <p className="status success">{syncStatus.message}</p>}
        {syncStatus.state === "error" && (
          <div className="status error" role="alert">
            <p>{syncStatus.message}</p>
            <button type="button" onClick={() => void runRecentSync(true)}>
              Retry Activity Sync
            </button>
          </div>
        )}
      </section>

      <main className="grid-layout">
        <section className="panel">
          <h2>Meal Draft Composer</h2>
          <label htmlFor="meal-note">Meal note</label>
          <textarea
            id="meal-note"
            placeholder="Example: lunch rice bowl with chicken and salad"
            value={mealNote}
            onChange={(event) => setMealNote(event.target.value)}
            rows={4}
          />

          <div className="action-row">
            <button type="button" disabled={draftStatus.state === "loading"} onClick={() => void handleGenerateDraft()}>
              Generate Draft
            </button>
            {draftStatus.state === "error" && (
              <button type="button" onClick={() => void handleGenerateDraft()}>
                Retry Draft
              </button>
            )}
          </div>

          {draftStatus.state !== "idle" && <p className={`status ${draftStatus.state}`}>{draftStatus.message}</p>}
          {saveStatus.state !== "idle" && <p className={`status ${saveStatus.state}`}>{saveStatus.message}</p>}

          {draft && (
            <div className="draft-preview">
              <h3>Draft Preview</h3>
              <p>
                Slot: <strong>{draft.normalized_payload.meal_slot}</strong>
              </p>
              <p>
                Calories: {draft.normalized_payload.calories} | Protein: {draft.normalized_payload.protein_g}g |
                Carbs: {draft.normalized_payload.carbs_g}g | Fat: {draft.normalized_payload.fat_g}g
              </p>

              {draft.assumptions.length > 0 && (
                <ul>
                  {draft.assumptions.map((assumption) => (
                    <li key={assumption}>{assumption}</li>
                  ))}
                </ul>
              )}

              {draft.warnings.length > 0 && (
                <ul className="warnings">
                  {draft.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              )}

              {draft.confirm_before_save && (
                <p className="status warning">Review the draft before saving because ambiguity was detected.</p>
              )}

              <button type="button" disabled={saveStatus.state === "loading"} onClick={() => void handleSaveDraft()}>
                Save Draft to Day
              </button>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Meals</h2>
          {dayLog && dayLog.meal_entries.length === 0 && (
            <p className="status empty">No meals saved for this day yet.</p>
          )}

          {(["breakfast", "lunch", "dinner", "snacks"] as const).map((slot) => (
            <article key={slot} className="slot-block">
              <h3>{slot}</h3>

              {groupedMeals[slot].length === 0 && <p className="slot-empty">No {slot} entries.</p>}

              {groupedMeals[slot].map((mealEntry) => (
                <div key={mealEntry.id} className="meal-card">
                  <p>{mealEntry.source_text}</p>
                  <p>
                    {mealEntry.calories} kcal | {mealEntry.protein_g}p / {mealEntry.carbs_g}c / {mealEntry.fat_g}f
                  </p>
                  <p>Status: {mealEntry.status}</p>

                  {editingMeal?.id === mealEntry.id ? (
                    <div className="edit-area">
                      <textarea
                        aria-label="Edit meal text"
                        value={editingText}
                        onChange={(event) => setEditingText(event.target.value)}
                        rows={3}
                      />
                      <div className="action-row">
                        <button type="button" onClick={() => void handleEditMealSave()}>
                          Save Meal Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingMeal(null);
                            setEditingText("");
                            setEditStatus({ state: "idle", message: "" });
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                      {editStatus.state !== "idle" && (
                        <p className={`status ${editStatus.state}`}>{editStatus.message}</p>
                      )}
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingMeal(mealEntry);
                        setEditingText(mealEntry.source_text);
                        setEditStatus({ state: "idle", message: "" });
                      }}
                    >
                      Edit Meal
                    </button>
                  )}
                </div>
              ))}
            </article>
          ))}

          {dayLog && (
            <div className="totals-block">
              <h3>Daily Totals</h3>
              <p>
                {dayLog.daily_totals.calories} kcal | {dayLog.daily_totals.protein_g}p / {dayLog.daily_totals.carbs_g}c /
                {" "}
                {dayLog.daily_totals.fat_g}f
              </p>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Activities</h2>
          <button type="button" onClick={() => void runRecentSync(true)}>
            Sync Recent Activities
          </button>

          {dayLog && dayLog.activity_entries.length === 0 && (
            <p className="status empty">No synced activities for this day yet.</p>
          )}

          {dayLog?.activity_entries.map((activity) => (
            <div className="activity-card" key={activity.strava_activity_id}>
              <p>
                <strong>{activity.name}</strong> ({activity.sport_type})
              </p>
              <p>
                Duration: {Math.round(activity.elapsed_time_s / 60)} min | Calories: {activity.calories ?? "n/a"} |
                Suffer score: {activity.suffer_score ?? "n/a"}
              </p>
            </div>
          ))}
        </section>

        <section className="panel">
          <h2>Glucose Uploads</h2>

          <label htmlFor="glucose-file">Screenshot file</label>
          <input
            id="glucose-file"
            aria-label="Glucose screenshot"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => {
              const nextFile = event.target.files?.[0] ?? null;
              setUploadFile(nextFile);
            }}
          />

          <label htmlFor="upload-note">Optional note</label>
          <textarea
            id="upload-note"
            value={uploadNote}
            onChange={(event) => setUploadNote(event.target.value)}
            rows={3}
          />

          <div className="action-row">
            <button type="button" disabled={uploadStatus.state === "loading"} onClick={() => void handleGlucoseUpload()}>
              Upload Screenshot
            </button>
            {uploadStatus.state === "error" && (
              <button type="button" onClick={() => void handleGlucoseUpload()}>
                Retry Upload
              </button>
            )}
          </div>

          {uploadStatus.state !== "idle" && <p className={`status ${uploadStatus.state}`}>{uploadStatus.message}</p>}

          {dayLog && dayLog.glucose_uploads.length === 0 && (
            <p className="status empty">No glucose screenshots uploaded for this day yet.</p>
          )}

          {dayLog?.glucose_uploads.map((upload) => (
            <div className="upload-card" key={upload.id}>
              <p>
                <a href={`http://localhost:8000${upload.file_url}`} target="_blank" rel="noreferrer">
                  {upload.original_filename}
                </a>
              </p>
              <p>{upload.ai_summary}</p>
              {upload.user_note && <p>User note: {upload.user_note}</p>}
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
