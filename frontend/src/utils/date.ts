/**
 * Returns an ISO calendar date string (`YYYY-MM-DD`) for a Date object.
 *
 * @param date - The date object to format.
 * @returns A local-time calendar date string.
 * @example
 * const value = toIsoDate(new Date("2026-03-06T08:00:00"));
 */
export function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");

  return `${year}-${month}-${day}`;
}

/**
 * Returns today's date formatted as `YYYY-MM-DD`.
 *
 * @returns Today's local calendar date.
 * @example
 * const today = getTodayIsoDate();
 */
export function getTodayIsoDate(): string {
  return toIsoDate(new Date());
}

/**
 * Shifts an ISO date by a number of days and returns a new ISO date string.
 *
 * @param isoDate - The source date in `YYYY-MM-DD` format.
 * @param dayOffset - Number of days to add (negative for previous days).
 * @returns The shifted date in `YYYY-MM-DD` format.
 * @throws Error when the date cannot be parsed.
 * @example
 * const yesterday = shiftIsoDate("2026-03-06", -1);
 */
export function shiftIsoDate(isoDate: string, dayOffset: number): string {
  const parsedDate = new Date(`${isoDate}T12:00:00`);

  if (Number.isNaN(parsedDate.getTime())) {
    throw new Error(`Invalid ISO date: ${isoDate}`);
  }

  parsedDate.setDate(parsedDate.getDate() + dayOffset);
  return toIsoDate(parsedDate);
}

/**
 * Formats an ISO date string for human-readable headings.
 *
 * @param isoDate - The date to format.
 * @returns A long, locale-aware date label.
 * @throws Error when the date cannot be parsed.
 * @example
 * const label = formatDisplayDate("2026-03-06");
 */
export function formatDisplayDate(isoDate: string): string {
  const parsedDate = new Date(`${isoDate}T12:00:00`);

  if (Number.isNaN(parsedDate.getTime())) {
    throw new Error(`Invalid ISO date: ${isoDate}`);
  }

  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "long",
    day: "numeric",
    year: "numeric"
  }).format(parsedDate);
}

/**
 * Converts elapsed seconds into an `Hh Mm` readable label.
 *
 * @param elapsedTimeSeconds - Duration in seconds.
 * @returns A compact duration label.
 * @example
 * const label = formatElapsedTime(5400); // "1h 30m"
 */
export function formatElapsedTime(elapsedTimeSeconds: number): string {
  const totalMinutes = Math.max(0, Math.floor(elapsedTimeSeconds / 60));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) {
    return `${minutes}m`;
  }

  return `${hours}h ${minutes}m`;
}
