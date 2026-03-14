import type { MealSlot } from "../types";

/**
 * Enumerates meal slots in the order expected by the day-log UI.
 */
export const MEAL_SLOTS: MealSlot[] = ["breakfast", "lunch", "dinner", "snacks"];

/**
 * Provides readable labels for meal slot headings.
 */
export const MEAL_SLOT_LABEL: Record<MealSlot, string> = {
  breakfast: "Breakfast",
  lunch: "Lunch",
  dinner: "Dinner",
  snacks: "Snacks"
};

/**
 * Normalizes user text before draft parsing.
 *
 * @param sourceText - Raw free-text input from the composer.
 * @returns Trimmed text ready for adapter processing.
 * @example
 * const cleaned = normalizeMealInput("  yogurt and berries  ");
 */
export function normalizeMealInput(sourceText: string): string {
  return sourceText.trim();
}
