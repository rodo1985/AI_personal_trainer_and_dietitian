import type { MealEntry, MealSlot } from "../types";
import { MEAL_SLOT_LABEL } from "../utils/meal";

/**
 * Defines props for one meal-slot section.
 */
interface MealSectionProps {
  slot: MealSlot;
  entries: MealEntry[];
}

/**
 * Renders a meal slot with its confirmed entries and nutrition summaries.
 *
 * @param props - Section slot and meal entries.
 * @returns The meal slot panel.
 * @example
 * <MealSection slot="breakfast" entries={entries} />
 */
export function MealSection(props: MealSectionProps): JSX.Element {
  return (
    <article className="panel meal-section" aria-label={`${MEAL_SLOT_LABEL[props.slot]} section`}>
      <header className="panel__header">
        <h2>{MEAL_SLOT_LABEL[props.slot]}</h2>
      </header>

      {props.entries.length === 0 ? (
        <p className="empty-state">No meals logged yet.</p>
      ) : (
        <ul className="meal-list">
          {props.entries.map((entry) => (
            <li key={entry.id} className="meal-card">
              <p className="meal-card__title">{entry.source_text}</p>
              <p className="meal-card__meta">
                {entry.calories} kcal • {entry.protein_g}g protein • {entry.carbs_g}g carbs • {entry.fat_g}g fat
              </p>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
