import type { MealSlot } from "../types";
import { MEAL_SLOT_LABEL, MEAL_SLOTS } from "../utils/meal";

/**
 * Defines props for the assistant composer controls.
 */
interface AssistantComposerProps {
  sourceText: string;
  selectedMealSlot: MealSlot;
  isGeneratingDraft: boolean;
  isListening: boolean;
  onSourceTextChange: (nextText: string) => void;
  onMealSlotChange: (mealSlot: MealSlot) => void;
  onGenerateDraft: () => void;
  onStartMicrophone: () => void;
}

/**
 * Renders free-text and microphone controls used to create meal drafts.
 *
 * @param props - Assistant composer props.
 * @returns The assistant composer section.
 * @example
 * <AssistantComposer {...composerProps} />
 */
export function AssistantComposer(props: AssistantComposerProps): JSX.Element {
  return (
    <article className="panel" aria-label="Assistant composer">
      <header className="panel__header">
        <h2>Assistant composer</h2>
        <p className="panel__subtext">Write or dictate a quick meal note, then review draft details before save.</p>
      </header>

      <div className="composer-grid">
        <label className="field">
          <span>Meal slot</span>
          <select
            aria-label="Meal slot"
            value={props.selectedMealSlot}
            onChange={(event) => {
              props.onMealSlotChange(event.target.value as MealSlot);
            }}
          >
            {MEAL_SLOTS.map((mealSlot) => (
              <option key={mealSlot} value={mealSlot}>
                {MEAL_SLOT_LABEL[mealSlot]}
              </option>
            ))}
          </select>
        </label>

        <label className="field field--wide">
          <span>Meal description</span>
          <textarea
            aria-label="Meal description"
            placeholder="Example: oats, banana, yogurt"
            value={props.sourceText}
            onChange={(event) => {
              props.onSourceTextChange(event.target.value);
            }}
          />
        </label>
      </div>

      <div className="composer-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={props.onStartMicrophone}
          disabled={props.isListening}
        >
          {props.isListening ? "Recording voice note..." : "Start voice note"}
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={props.onGenerateDraft}
          disabled={props.isGeneratingDraft}
        >
          {props.isGeneratingDraft ? "Generating draft..." : "Generate meal draft"}
        </button>
      </div>
    </article>
  );
}
