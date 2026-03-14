import type { DayLog } from "../types";

/**
 * Defines props for the daily totals summary card.
 */
interface DailyTotalsCardProps {
  dayLog: DayLog;
}

/**
 * Renders aggregate nutrition totals and optional day note.
 *
 * @param props - Daily totals props.
 * @returns The daily totals card.
 * @example
 * <DailyTotalsCard dayLog={dayLog} />
 */
export function DailyTotalsCard(props: DailyTotalsCardProps): JSX.Element {
  return (
    <article className="panel panel--accent" aria-label="Daily totals">
      <header className="panel__header">
        <h2>Day summary</h2>
      </header>
      <p className="totals-row">Calories: {props.dayLog.daily_totals.calories} kcal</p>
      <p className="totals-row">Protein: {props.dayLog.daily_totals.protein_g}g</p>
      <p className="totals-row">Carbs: {props.dayLog.daily_totals.carbs_g}g</p>
      <p className="totals-row">Fat: {props.dayLog.daily_totals.fat_g}g</p>
      <p className="panel__subtext">{props.dayLog.daily_notes || "No day-level notes yet."}</p>
    </article>
  );
}
