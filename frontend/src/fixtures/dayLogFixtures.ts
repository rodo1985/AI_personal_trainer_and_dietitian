import type { DayLog, MealEntry } from "../types";

/**
 * Creates a stable meal entry fixture used in seeded day logs.
 *
 * @param mealEntry - Partial meal data to shape into a consistent record.
 * @returns A fully typed meal entry fixture.
 * @example
 * const breakfast = createMealEntry({ id: "meal-1", meal_slot: "breakfast", source_text: "oats" });
 */
function createMealEntry(mealEntry: {
  id: string;
  meal_slot: MealEntry["meal_slot"];
  source_text: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}): MealEntry {
  return {
    ...mealEntry,
    items: [
      {
        name: mealEntry.source_text,
        quantity: "1 serving",
        calories: mealEntry.calories,
        protein_g: mealEntry.protein_g,
        carbs_g: mealEntry.carbs_g,
        fat_g: mealEntry.fat_g
      }
    ],
    confidence: 0.88,
    status: "confirmed",
    created_at: `${new Date().toISOString()}`
  };
}

/**
 * Creates an empty day template for dates without seed data.
 *
 * @param date - The target day in `YYYY-MM-DD` format.
 * @returns An empty day log object with zero totals.
 * @example
 * const empty = createEmptyDayLog("2026-03-07");
 */
export function createEmptyDayLog(date: string): DayLog {
  return {
    date,
    meal_entries: [],
    activity_entries: [],
    glucose_uploads: [],
    daily_notes: "",
    daily_totals: {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    }
  };
}

/**
 * Stores seed day logs keyed by ISO date for predictable development flows.
 */
export const SEED_DAY_LOGS: Record<string, DayLog> = {
  "2026-03-06": {
    date: "2026-03-06",
    meal_entries: [
      createMealEntry({
        id: "meal-b-1",
        meal_slot: "breakfast",
        source_text: "chia pudding with berries",
        calories: 320,
        protein_g: 14,
        carbs_g: 38,
        fat_g: 11
      }),
      createMealEntry({
        id: "meal-l-1",
        meal_slot: "lunch",
        source_text: "salmon rice bowl",
        calories: 540,
        protein_g: 34,
        carbs_g: 45,
        fat_g: 21
      })
    ],
    activity_entries: [
      {
        id: "activity-1",
        strava_activity_id: "987654",
        name: "Tempo Run",
        sport_type: "Run",
        start_time: "2026-03-06T07:10:00Z",
        elapsed_time_s: 4360,
        calories: 642,
        suffer_score: 83
      },
      {
        id: "activity-2",
        strava_activity_id: "987655",
        name: "Evening Recovery Spin",
        sport_type: "Ride",
        start_time: "2026-03-06T18:20:00Z",
        elapsed_time_s: 2650,
        calories: 280
      }
    ],
    glucose_uploads: [
      {
        id: "glucose-1",
        file_name: "libre-2026-03-06-morning.png",
        image_url: "https://images.unsplash.com/photo-1510253687831-0f982d7862fc?w=640",
        uploaded_at: "2026-03-06T08:40:00Z",
        ai_summary:
          "Morning trend shows a quick rise after breakfast and a stable return toward baseline before lunch.",
        user_note: "Felt normal after run."
      }
    ],
    daily_notes: "Hydration felt better than yesterday.",
    daily_totals: {
      calories: 860,
      protein_g: 48,
      carbs_g: 83,
      fat_g: 32
    }
  },
  "2026-03-05": {
    date: "2026-03-05",
    meal_entries: [
      createMealEntry({
        id: "meal-d-1",
        meal_slot: "dinner",
        source_text: "whole wheat pasta with tofu",
        calories: 610,
        protein_g: 28,
        carbs_g: 86,
        fat_g: 16
      })
    ],
    activity_entries: [],
    glucose_uploads: [],
    daily_notes: "",
    daily_totals: {
      calories: 610,
      protein_g: 28,
      carbs_g: 86,
      fat_g: 16
    }
  }
};
