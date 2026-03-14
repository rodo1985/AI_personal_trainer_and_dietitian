import type {
  AssistantDraft,
  DayLogResponse,
  MealDraftPayload,
  MealEntry,
  StravaSyncResult,
  GlucoseUpload
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

/**
 * Error type used when API requests fail with non-2xx responses.
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Parse a fetch response and throw an actionable error when needed.
 */
async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;

    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      // Ignore body parse errors and fall back to HTTP status text.
    }

    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

/**
 * Load one day aggregate from backend.
 */
export async function fetchDayLog(dayIso: string): Promise<DayLogResponse> {
  const response = await fetch(`${API_BASE}/day/${dayIso}`);
  return parseJson<DayLogResponse>(response);
}

/**
 * Request an assistant-generated meal draft from user text.
 */
export async function createMealDraft(dayIso: string, text: string): Promise<AssistantDraft> {
  const response = await fetch(`${API_BASE}/day/${dayIso}/assistant/draft`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });

  return parseJson<AssistantDraft>(response);
}

/**
 * Persist a confirmed meal payload.
 */
export async function saveMealDraft(dayIso: string, payload: MealDraftPayload): Promise<MealEntry> {
  const response = await fetch(`${API_BASE}/day/${dayIso}/meals`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseJson<MealEntry>(response);
}

/**
 * Edit an existing meal entry.
 */
export async function editMealEntry(
  dayIso: string,
  mealId: number,
  sourceText: string
): Promise<MealEntry> {
  const response = await fetch(`${API_BASE}/day/${dayIso}/meals/${mealId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ source_text: sourceText, status: "edited" })
  });

  return parseJson<MealEntry>(response);
}

/**
 * Run rolling seven-day sync.
 */
export async function syncRecentActivities(): Promise<StravaSyncResult> {
  const response = await fetch(`${API_BASE}/strava/sync/recent`, {
    method: "POST"
  });

  return parseJson<StravaSyncResult>(response);
}

/**
 * Upload glucose screenshot and optional note.
 */
export async function uploadGlucoseScreenshot(
  dayIso: string,
  file: File,
  userNote: string
): Promise<GlucoseUpload> {
  const form = new FormData();
  form.append("file", file);
  if (userNote.trim()) {
    form.append("user_note", userNote.trim());
  }

  const response = await fetch(`${API_BASE}/day/${dayIso}/glucose-uploads`, {
    method: "POST",
    body: form
  });

  return parseJson<GlucoseUpload>(response);
}
