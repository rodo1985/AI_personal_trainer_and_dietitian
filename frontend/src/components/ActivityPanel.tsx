import type { ActivityEntry } from "../types";
import { formatElapsedTime } from "../utils/date";

/**
 * Defines props for the activities panel.
 */
interface ActivityPanelProps {
  activities: ActivityEntry[];
}

/**
 * Renders synced activities for the selected day.
 *
 * @param props - Activity panel props.
 * @returns The activity panel component.
 * @example
 * <ActivityPanel activities={dayLog.activity_entries} />
 */
export function ActivityPanel(props: ActivityPanelProps): JSX.Element {
  return (
    <article className="panel" aria-label="Activity panel">
      <header className="panel__header">
        <h2>Activities</h2>
        <p className="panel__subtext">Rolling 7-day sync snapshot</p>
      </header>

      {props.activities.length === 0 ? (
        <p className="empty-state">No activities synced yet.</p>
      ) : (
        <ul className="activity-list">
          {props.activities.map((activity) => (
            <li key={activity.id} className="activity-card">
              <p className="activity-card__title">{activity.name}</p>
              <p className="activity-card__meta">
                {activity.sport_type} • {formatElapsedTime(activity.elapsed_time_s)}
              </p>
              <p className="activity-card__meta">
                {activity.calories ? `${activity.calories} kcal` : "Calories unavailable"}
                {activity.suffer_score ? ` • Suffer score ${activity.suffer_score}` : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
