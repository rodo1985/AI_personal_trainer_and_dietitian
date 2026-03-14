/**
 * Shared frontend types matching backend API response contracts.
 */

export type MealSlot = "breakfast" | "lunch" | "dinner" | "snacks";

export interface FoodItem {
  name: string;
  quantity_text: string;
  matched: boolean;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
}

export interface MealEntry {
  id: number;
  meal_slot: MealSlot;
  source_text: string;
  items: FoodItem[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  status: "needs_review" | "confirmed" | "edited";
  updated_at: string;
}

export interface ActivityEntry {
  strava_activity_id: string;
  name: string;
  sport_type: string;
  start_time: string;
  elapsed_time_s: number;
  calories: number | null;
  suffer_score: number | null;
  rpe_override: number | null;
}

export interface GlucoseUpload {
  id: number;
  file_url: string;
  original_filename: string;
  uploaded_at: string;
  ai_summary: string | null;
  user_note: string | null;
}

export interface DailyTotals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface DayLogResponse {
  date: string;
  meal_entries: MealEntry[];
  activity_entries: ActivityEntry[];
  glucose_uploads: GlucoseUpload[];
  daily_notes: string;
  daily_totals: DailyTotals;
}

export interface MealDraftPayload {
  meal_slot: MealSlot;
  source_text: string;
  items: FoodItem[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  status: "needs_review" | "confirmed" | "edited";
}

export interface AssistantDraft {
  draft_type: "meal";
  normalized_payload: MealDraftPayload;
  assumptions: string[];
  warnings: string[];
  confirm_before_save: boolean;
}

export interface StravaSyncResult {
  started_at: string;
  finished_at: string;
  imported_count: number;
  updated_count: number;
  window_start: string;
  window_end: string;
  status: "success" | "partial" | "failed";
}
