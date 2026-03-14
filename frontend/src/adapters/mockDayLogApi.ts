import { createEmptyDayLog, SEED_DAY_LOGS } from "../fixtures/dayLogFixtures";
import { normalizeMealInput } from "../utils/meal";
import type { AssistantDraft, CreateDraftInput, DayLog, DailyTotals, MealItem, SaveMealInput } from "../types";

/**
 * Describes the adapter contract the UI uses for day-log operations.
 */
export interface DayLogApi {
  getDayLog: (date: string) => Promise<DayLog>;
  createAssistantDraft: (input: CreateDraftInput) => Promise<AssistantDraft>;
  saveMeal: (input: SaveMealInput) => Promise<DayLog>;
}

/**
 * Provides lightweight nutrition references for common demo meal ingredients.
 */
const FOOD_LIBRARY: Record<string, Omit<MealItem, "quantity">> = {
  oats: { name: "oats", calories: 190, protein_g: 7, carbs_g: 33, fat_g: 4 },
  banana: { name: "banana", calories: 105, protein_g: 1, carbs_g: 27, fat_g: 0 },
  yogurt: { name: "yogurt", calories: 110, protein_g: 9, carbs_g: 8, fat_g: 4 },
  berries: { name: "berries", calories: 70, protein_g: 1, carbs_g: 17, fat_g: 0 },
  eggs: { name: "eggs", calories: 140, protein_g: 12, carbs_g: 1, fat_g: 10 },
  rice: { name: "rice", calories: 205, protein_g: 4, carbs_g: 45, fat_g: 0 },
  salmon: { name: "salmon", calories: 240, protein_g: 26, carbs_g: 0, fat_g: 14 },
  toast: { name: "toast", calories: 140, protein_g: 5, carbs_g: 24, fat_g: 2 },
  avocado: { name: "avocado", calories: 160, protein_g: 2, carbs_g: 9, fat_g: 15 },
  tofu: { name: "tofu", calories: 180, protein_g: 18, carbs_g: 6, fat_g: 10 }
};

/**
 * Stores mutable mock data by date to simulate backend persistence.
 */
const dayLogStore = new Map<string, DayLog>();

/**
 * Tracks generated IDs for newly saved meals in the mocked store.
 */
let mealIdCounter = 100;

/**
 * Deep clones a JSON-safe value so UI state cannot mutate adapter state directly.
 *
 * @param value - Any JSON-safe value.
 * @returns A deeply cloned value.
 * @example
 * const copied = deepClone(seedObject);
 */
function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

/**
 * Applies an artificial network delay to mimic async backend calls.
 *
 * @param delayMs - Delay duration in milliseconds.
 * @returns A promise that resolves after the delay.
 * @example
 * await sleep(100);
 */
function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, delayMs);
  });
}

/**
 * Generates a stable key for ingredient lookup from raw token text.
 *
 * @param token - Candidate ingredient text.
 * @returns A normalized token suitable for dictionary lookups.
 * @example
 * const key = normalizeToken("  BANANA "); // "banana"
 */
function normalizeToken(token: string): string {
  return token.toLowerCase().replace(/[^a-z\s]/g, "").trim();
}

/**
 * Splits free-text meal input into candidate ingredient tokens.
 *
 * @param sourceText - Raw composer text.
 * @returns A list of normalized tokens in input order.
 * @example
 * const tokens = tokenizeMealText("oats, banana and yogurt");
 */
function tokenizeMealText(sourceText: string): string[] {
  return sourceText
    .split(/,|\band\b|\+/gi)
    .map((token) => normalizeToken(token))
    .filter((token) => token.length > 0);
}

/**
 * Calculates nutrition totals for a list of parsed items.
 *
 * @param items - Parsed food items.
 * @returns Summed nutrition totals.
 * @example
 * const totals = summarizeTotals(parsedItems);
 */
function summarizeTotals(items: MealItem[]): DailyTotals {
  return items.reduce<DailyTotals>(
    (totals, item) => ({
      calories: totals.calories + item.calories,
      protein_g: totals.protein_g + item.protein_g,
      carbs_g: totals.carbs_g + item.carbs_g,
      fat_g: totals.fat_g + item.fat_g
    }),
    {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    }
  );
}

/**
 * Builds a parsed draft payload from free text using local ingredient rules.
 *
 * @param sourceText - User text from the assistant composer.
 * @returns Parsed items plus assumptions and warnings.
 * @example
 * const parsed = parseDraftText("oats, banana, yogurt");
 */
function parseDraftText(sourceText: string): {
  items: MealItem[];
  assumptions: string[];
  warnings: string[];
  confidence: number;
} {
  const tokens = tokenizeMealText(sourceText);
  const assumptions: string[] = [];
  const warnings: string[] = [];
  const items: MealItem[] = [];

  if (tokens.length === 0) {
    warnings.push("No recognizable ingredients were found. Please add more detail.");

    return {
      items,
      assumptions,
      warnings,
      confidence: 0.25
    };
  }

  let matchedTokens = 0;

  tokens.forEach((token) => {
    const libraryMatch = FOOD_LIBRARY[token];

    if (libraryMatch) {
      matchedTokens += 1;
      items.push({
        ...libraryMatch,
        quantity: "1 serving"
      });
      return;
    }

    // We keep unmatched items visible so users can confirm or edit uncertainty.
    warnings.push(`Could not confidently match nutrition for \"${token}\".`);
    assumptions.push(`Estimated \"${token}\" as one serving with placeholder nutrition.`);
    items.push({
      name: token,
      quantity: "1 serving",
      calories: 120,
      protein_g: 4,
      carbs_g: 14,
      fat_g: 5
    });
  });

  const confidence = Math.max(0.35, matchedTokens / tokens.length);
  return { items, assumptions, warnings, confidence };
}

/**
 * Computes day totals from saved meal entries.
 *
 * @param dayLog - The day log to summarize.
 * @returns Updated day log totals.
 * @example
 * const totals = computeDayTotals(day);
 */
function computeDayTotals(dayLog: DayLog): DailyTotals {
  return dayLog.meal_entries.reduce<DailyTotals>(
    (totals, meal) => ({
      calories: totals.calories + meal.calories,
      protein_g: totals.protein_g + meal.protein_g,
      carbs_g: totals.carbs_g + meal.carbs_g,
      fat_g: totals.fat_g + meal.fat_g
    }),
    {
      calories: 0,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0
    }
  );
}

/**
 * Returns a day log from the in-memory store or creates an empty fallback.
 *
 * @param date - Target day in ISO format.
 * @returns A mutable day-log reference stored in memory.
 * @example
 * const day = getOrCreateDay("2026-03-07");
 */
function getOrCreateDay(date: string): DayLog {
  const existingLog = dayLogStore.get(date);

  if (existingLog) {
    return existingLog;
  }

  const seededDay = SEED_DAY_LOGS[date];
  const dayLog = seededDay ? deepClone(seededDay) : createEmptyDayLog(date);
  dayLogStore.set(date, dayLog);
  return dayLog;
}

/**
 * Fetches the aggregate data for a specific day.
 *
 * @param date - Target day in ISO format.
 * @returns The day log payload used by the UI.
 * @throws Error when the mock is configured to force a load failure.
 * @example
 * const day = await mockDayLogApi.getDayLog("2026-03-06");
 */
async function getDayLog(date: string): Promise<DayLog> {
  await sleep(150);

  // Allows the frontend to validate load-error UI states without backend wiring.
  if (date === "2026-03-04") {
    throw new Error("Unable to load day log for this date. Please retry.");
  }

  return deepClone(getOrCreateDay(date));
}

/**
 * Creates a structured meal draft from free text.
 *
 * @param input - Date, meal slot, and source text from the composer.
 * @returns A draft payload that must be reviewed before save.
 * @throws Error when source text is empty.
 * @example
 * const draft = await mockDayLogApi.createAssistantDraft({
 *   date: "2026-03-06",
 *   meal_slot: "breakfast",
 *   source_text: "oats, banana"
 * });
 */
async function createAssistantDraft(input: CreateDraftInput): Promise<AssistantDraft> {
  await sleep(220);

  const normalizedText = normalizeMealInput(input.source_text);

  if (!normalizedText) {
    throw new Error("Please add a meal description before generating a draft.");
  }

  const parsed = parseDraftText(normalizedText);

  return {
    draft_type: "meal",
    meal_slot: input.meal_slot,
    source_text: normalizedText,
    items: parsed.items,
    totals: summarizeTotals(parsed.items),
    assumptions: parsed.assumptions,
    warnings: parsed.warnings,
    confirm_before_save: true,
    confidence: Number(parsed.confidence.toFixed(2))
  };
}

/**
 * Saves a confirmed draft into the selected day and returns the new day log.
 *
 * @param input - Date and confirmed draft payload.
 * @returns Updated day-log aggregate.
 * @throws Error when the draft text includes `#fail-save` for UI testing.
 * @example
 * const day = await mockDayLogApi.saveMeal({ date: "2026-03-06", draft });
 */
async function saveMeal(input: SaveMealInput): Promise<DayLog> {
  await sleep(180);

  if (input.draft.source_text.includes("#fail-save")) {
    throw new Error("Meal save failed in the mock adapter. Remove #fail-save and retry.");
  }

  const dayLog = getOrCreateDay(input.date);
  mealIdCounter += 1;

  dayLog.meal_entries.push({
    id: `meal-${mealIdCounter}`,
    meal_slot: input.draft.meal_slot,
    source_text: input.draft.source_text,
    items: input.draft.items,
    calories: input.draft.totals.calories,
    protein_g: input.draft.totals.protein_g,
    carbs_g: input.draft.totals.carbs_g,
    fat_g: input.draft.totals.fat_g,
    confidence: input.draft.confidence,
    status: "confirmed",
    created_at: new Date().toISOString()
  });

  dayLog.daily_totals = computeDayTotals(dayLog);
  return deepClone(dayLog);
}

/**
 * Mock adapter implementation used until the backend endpoints are ready.
 */
export const mockDayLogApi: DayLogApi = {
  getDayLog,
  createAssistantDraft,
  saveMeal
};
