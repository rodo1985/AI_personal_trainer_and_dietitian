/**
 * Represents the supported meal slots in the daily log.
 */
export type MealSlot = "breakfast" | "lunch" | "dinner" | "snacks";

/**
 * Represents one parsed food item in a meal entry or draft.
 */
export interface MealItem {
  name: string;
  quantity: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

/**
 * Represents one meal record saved to a day.
 */
export interface MealEntry {
  id: string;
  meal_slot: MealSlot;
  source_text: string;
  items: MealItem[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  status: "confirmed";
  created_at: string;
}

/**
 * Represents one synced activity for the day summary.
 */
export interface ActivityEntry {
  id: string;
  strava_activity_id?: string;
  name: string;
  sport_type: string;
  start_time: string;
  elapsed_time_s: number;
  calories?: number;
  suffer_score?: number;
  rpe_override?: number;
}

/**
 * Represents a glucose screenshot upload and optional analysis.
 */
export interface GlucoseUpload {
  id: string;
  file_name: string;
  image_url: string;
  uploaded_at: string;
  ai_summary?: string;
  user_note?: string;
}

/**
 * Represents the nutrition totals shown in the daily summary.
 */
export interface DailyTotals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

/**
 * Represents all day-level data rendered by the main page.
 */
export interface DayLog {
  date: string;
  meal_entries: MealEntry[];
  activity_entries: ActivityEntry[];
  glucose_uploads: GlucoseUpload[];
  daily_notes: string;
  daily_totals: DailyTotals;
}

/**
 * Represents a structured assistant draft that requires review before save.
 */
export interface AssistantDraft {
  draft_type: "meal";
  meal_slot: MealSlot;
  source_text: string;
  items: MealItem[];
  totals: DailyTotals;
  assumptions: string[];
  warnings: string[];
  confirm_before_save: boolean;
  confidence: number;
}

/**
 * Represents payload needed to request a meal draft.
 */
export interface CreateDraftInput {
  date: string;
  meal_slot: MealSlot;
  source_text: string;
}

/**
 * Represents payload needed to save a confirmed meal draft.
 */
export interface SaveMealInput {
  date: string;
  draft: AssistantDraft;
}

/**
 * Represents all states for async request handling in the UI.
 */
export type RequestState = "idle" | "loading" | "success" | "error";
