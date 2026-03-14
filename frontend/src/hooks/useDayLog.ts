import { useCallback, useEffect, useState } from "react";
import { mockDayLogApi } from "../adapters/mockDayLogApi";
import type { AssistantDraft, DayLog, MealSlot, RequestState } from "../types";

/**
 * Describes state and actions exposed by the day-log data hook.
 */
export interface UseDayLogResult {
  dayLog: DayLog | null;
  loadState: RequestState;
  loadError: string | null;
  draft: AssistantDraft | null;
  draftState: RequestState;
  draftError: string | null;
  saveState: RequestState;
  saveError: string | null;
  saveSuccessMessage: string | null;
  generateDraft: (sourceText: string, mealSlot: MealSlot) => Promise<void>;
  clearDraft: () => void;
  saveDraft: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * Manages day-log loading, draft creation, and save operations.
 *
 * @param selectedDate - The date currently shown in the day selector.
 * @returns Async state plus actions for the day-log page.
 * @example
 * const dayLogState = useDayLog("2026-03-06");
 */
export function useDayLog(selectedDate: string): UseDayLogResult {
  const [dayLog, setDayLog] = useState<DayLog | null>(null);
  const [loadState, setLoadState] = useState<RequestState>("idle");
  const [loadError, setLoadError] = useState<string | null>(null);

  const [draft, setDraft] = useState<AssistantDraft | null>(null);
  const [draftState, setDraftState] = useState<RequestState>("idle");
  const [draftError, setDraftError] = useState<string | null>(null);

  const [saveState, setSaveState] = useState<RequestState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);

  /**
   * Loads the selected day from the mocked API and resets volatile UI states.
   *
   * @returns Resolves when the request completes.
   * @example
   * await refresh();
   */
  const refresh = useCallback(async () => {
    setLoadState("loading");
    setLoadError(null);
    setSaveSuccessMessage(null);

    try {
      const nextDayLog = await mockDayLogApi.getDayLog(selectedDate);
      setDayLog(nextDayLog);
      setLoadState("success");
      setDraft(null);
      setDraftState("idle");
      setDraftError(null);
      setSaveState("idle");
      setSaveError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to load day log.";
      setLoadError(message);
      setLoadState("error");
      setDayLog(null);
    }
  }, [selectedDate]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  /**
   * Requests an assistant meal draft for the current day.
   *
   * @param sourceText - Free-text meal description.
   * @param mealSlot - Selected meal slot.
   * @returns Resolves when draft creation completes.
   * @example
   * await generateDraft("oats and banana", "breakfast");
   */
  const generateDraft = useCallback(
    async (sourceText: string, mealSlot: MealSlot) => {
      setDraftState("loading");
      setDraftError(null);
      setSaveState("idle");
      setSaveError(null);
      setSaveSuccessMessage(null);

      try {
        const nextDraft = await mockDayLogApi.createAssistantDraft({
          date: selectedDate,
          meal_slot: mealSlot,
          source_text: sourceText
        });
        setDraft(nextDraft);
        setDraftState("success");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Draft generation failed.";
        setDraftError(message);
        setDraftState("error");
      }
    },
    [selectedDate]
  );

  /**
   * Clears the currently displayed assistant draft and related statuses.
   *
   * @returns Nothing.
   * @example
   * clearDraft();
   */
  const clearDraft = useCallback(() => {
    setDraft(null);
    setDraftState("idle");
    setDraftError(null);
    setSaveState("idle");
    setSaveError(null);
  }, []);

  /**
   * Persists the current draft and refreshes daily totals.
   *
   * @returns Resolves when save operation completes.
   * @throws Error when called without a current draft.
   * @example
   * await saveDraft();
   */
  const saveDraft = useCallback(async () => {
    if (!draft) {
      throw new Error("No draft is available to save.");
    }

    setSaveState("loading");
    setSaveError(null);
    setSaveSuccessMessage(null);

    try {
      const updatedDayLog = await mockDayLogApi.saveMeal({
        date: selectedDate,
        draft
      });

      setDayLog(updatedDayLog);
      setSaveState("success");
      setSaveSuccessMessage(`Meal saved to ${draft.meal_slot}.`);
      setDraft(null);
      setDraftState("idle");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Meal save failed.";
      setSaveError(message);
      setSaveState("error");
    }
  }, [draft, selectedDate]);

  return {
    dayLog,
    loadState,
    loadError,
    draft,
    draftState,
    draftError,
    saveState,
    saveError,
    saveSuccessMessage,
    generateDraft,
    clearDraft,
    saveDraft,
    refresh
  };
}
