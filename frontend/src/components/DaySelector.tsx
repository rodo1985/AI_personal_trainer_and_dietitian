import { formatDisplayDate } from "../utils/date";

/**
 * Defines props for the day selector controls.
 */
interface DaySelectorProps {
  selectedDate: string;
  onDateChange: (nextDate: string) => void;
  onPreviousDay: () => void;
  onNextDay: () => void;
}

/**
 * Renders date navigation controls for switching between day logs.
 *
 * @param props - Day selector props.
 * @returns The day selector component.
 * @example
 * <DaySelector selectedDate="2026-03-06" onDateChange={setDate} onPreviousDay={prev} onNextDay={next} />
 */
export function DaySelector(props: DaySelectorProps): JSX.Element {
  return (
    <section className="panel day-selector" aria-label="Day selector">
      <div className="day-selector__controls">
        <button type="button" className="secondary-button" onClick={props.onPreviousDay}>
          Previous
        </button>
        <div>
          <p className="eyebrow">Selected day</p>
          <h1>{formatDisplayDate(props.selectedDate)}</h1>
        </div>
        <button type="button" className="secondary-button" onClick={props.onNextDay}>
          Next
        </button>
      </div>

      <label className="field">
        <span>Jump to date</span>
        <input
          aria-label="Jump to date"
          type="date"
          value={props.selectedDate}
          onChange={(event) => {
            props.onDateChange(event.target.value);
          }}
        />
      </label>
    </section>
  );
}
