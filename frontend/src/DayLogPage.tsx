import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ActivityPanel } from "./components/ActivityPanel";
import { AssistantComposer } from "./components/AssistantComposer";
import { DailyTotalsCard } from "./components/DailyTotalsCard";
import { DaySelector } from "./components/DaySelector";
import { DraftPreview } from "./components/DraftPreview";
import { GlucoseUploadPanel } from "./components/GlucoseUploadPanel";
import { MealSection } from "./components/MealSection";
import { useDayLog } from "./hooks/useDayLog";
import type { MealSlot } from "./types";
import { getTodayIsoDate, shiftIsoDate } from "./utils/date";
import { MEAL_SLOTS } from "./utils/meal";

/**
 * Defines props for the day-log page component.
 */
interface DayLogPageProps {
  initialDate?: string;
}

/**
 * Merges a mock voice transcript into an existing composer value.
 *
 * @param previousValue - Existing composer text.
 * @param transcript - New transcript text from voice input.
 * @returns Combined value preserving existing text when present.
 * @example
 * const next = mergeTranscript("oats", "banana");
 */
function mergeTranscript(previousValue: string, transcript: string): string {
  if (!previousValue.trim()) {
    return transcript;
  }

  return `${previousValue.trim()}, ${transcript}`;
}

/**
 * Renders the mobile-first day-log interface for meals, activities, and glucose uploads.
 *
 * @param props - Optional initial date for testability.
 * @returns The complete day-log page.
 * @example
 * <DayLogPage />
 */
export function DayLogPage(props: DayLogPageProps): JSX.Element {
  const [selectedDate, setSelectedDate] = useState<string>(props.initialDate ?? getTodayIsoDate());
  const [selectedMealSlot, setSelectedMealSlot] = useState<MealSlot>("breakfast");
  const [composerText, setComposerText] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(false);
  const voiceTimeoutRef = useRef<number | null>(null);

  const {
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
  } = useDayLog(selectedDate);

  useEffect(() => {
    return () => {
      if (voiceTimeoutRef.current !== null) {
        window.clearTimeout(voiceTimeoutRef.current);
      }
    };
  }, []);

  /**
   * Moves the current day selection by a relative offset.
   *
   * @param dayOffset - Number of days to shift.
   * @returns Nothing.
   * @example
   * changeDay(-1);
   */
  function changeDay(dayOffset: number): void {
    setSelectedDate((currentDate) => shiftIsoDate(currentDate, dayOffset));
  }

  /**
   * Validates date input before setting selection.
   *
   * @param nextDate - Candidate ISO date from the date picker.
   * @returns Nothing.
   * @example
   * handleDateChange("2026-03-06");
   */
  function handleDateChange(nextDate: string): void {
    if (!nextDate) {
      return;
    }

    setSelectedDate(nextDate);
  }

  /**
   * Starts a mocked voice capture flow and appends a transcript to the composer.
   *
   * @returns Nothing.
   * @example
   * handleStartMicrophone();
   */
  function handleStartMicrophone(): void {
    setIsListening(true);

    if (voiceTimeoutRef.current !== null) {
      window.clearTimeout(voiceTimeoutRef.current);
    }

    voiceTimeoutRef.current = window.setTimeout(() => {
      setComposerText((currentText) => mergeTranscript(currentText, "eggs, toast, avocado"));
      setIsListening(false);
    }, 850);
  }

  /**
   * Requests a draft from current composer state.
   *
   * @returns Resolves when the async request completes.
   * @example
   * await handleGenerateDraft();
   */
  async function handleGenerateDraft(): Promise<void> {
    await generateDraft(composerText, selectedMealSlot);
  }

  /**
   * Saves the current draft and clears composer text after success.
   *
   * @returns Resolves when save flow finishes.
   * @example
   * await handleSaveDraft();
   */
  async function handleSaveDraft(): Promise<void> {
    await saveDraft();
    setComposerText("");
  }

  return (
    <main className="page-shell">
      <DaySelector
        selectedDate={selectedDate}
        onDateChange={handleDateChange}
        onPreviousDay={() => {
          changeDay(-1);
        }}
        onNextDay={() => {
          changeDay(1);
        }}
      />

      {loadState === "loading" ? <section className="panel loading-state">Loading selected day log...</section> : null}

      {loadState === "error" ? (
        <section className="panel" role="alert">
          <h2>Could not load this day</h2>
          <p>{loadError}</p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              void refresh();
            }}
          >
            Retry load
          </button>
        </section>
      ) : null}

      {loadState === "success" && dayLog ? (
        <div className="layout-grid">
          <section className="stack" style={{ "--stagger-index": 0 } as CSSProperties}>
            <DailyTotalsCard dayLog={dayLog} />
            <AssistantComposer
              sourceText={composerText}
              selectedMealSlot={selectedMealSlot}
              isGeneratingDraft={draftState === "loading"}
              isListening={isListening}
              onSourceTextChange={setComposerText}
              onMealSlotChange={setSelectedMealSlot}
              onGenerateDraft={() => {
                void handleGenerateDraft();
              }}
              onStartMicrophone={handleStartMicrophone}
            />
            {draftError ? <p className="message message--error">{draftError}</p> : null}
            <DraftPreview
              draft={draft}
              saveState={saveState}
              saveError={saveError}
              saveSuccessMessage={saveSuccessMessage}
              onSaveDraft={() => {
                void handleSaveDraft();
              }}
              onDiscardDraft={clearDraft}
            />
          </section>

          <section className="stack" style={{ "--stagger-index": 1 } as CSSProperties}>
            <div className="meal-grid">
              {MEAL_SLOTS.map((slot) => (
                <MealSection key={slot} slot={slot} entries={dayLog.meal_entries.filter((entry) => entry.meal_slot === slot)} />
              ))}
            </div>
            <ActivityPanel activities={dayLog.activity_entries} />
            <GlucoseUploadPanel uploads={dayLog.glucose_uploads} />
          </section>
        </div>
      ) : null}
    </main>
  );
}
