import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

interface MockResponse {
  status?: number;
  body: unknown;
}

/**
 * Build a JSON Response object suitable for fetch mocks.
 */
function jsonResponse({ status = 200, body }: MockResponse): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json"
    }
  });
}

/**
 * Install a sequential fetch mock for one test.
 */
function mockFetchSequence(sequence: MockResponse[]): void {
  const fetchMock = vi.fn();

  for (const item of sequence) {
    fetchMock.mockResolvedValueOnce(jsonResponse(item));
  }

  vi.stubGlobal("fetch", fetchMock);
}

const emptyDayPayload = {
  date: "2026-03-05",
  meal_entries: [],
  activity_entries: [],
  glucose_uploads: [],
  daily_notes: "",
  daily_totals: {
    calories: 0,
    protein_g: 0,
    carbs_g: 0,
    fat_g: 0
  }
};

describe("App", () => {
  /**
   * Reset global fetch mocks between test cases.
   */
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Verify empty states render for meals, activities, and uploads.
   */
  it("renders empty-state messaging after day load", async () => {
    mockFetchSequence([{ body: emptyDayPayload }]);

    render(<App />);

    expect(await screen.findByText("No meals saved for this day yet.")).toBeInTheDocument();
    expect(screen.getByText("No synced activities for this day yet.")).toBeInTheDocument();
    expect(screen.getByText("No glucose screenshots uploaded for this day yet.")).toBeInTheDocument();
  });

  /**
   * Verify meal draft generation and save flow updates the day view.
   */
  it("supports draft, review, and save meal flow", async () => {
    mockFetchSequence([
      { body: emptyDayPayload },
      {
        body: {
          draft_type: "meal",
          normalized_payload: {
            meal_slot: "breakfast",
            source_text: "Breakfast: oats and banana",
            items: [],
            calories: 255,
            protein_g: 6.3,
            carbs_g: 54,
            fat_g: 3.3,
            confidence: 0.8,
            status: "needs_review"
          },
          assumptions: ["Assumed one serving for each item."],
          warnings: ["No quantity for oats."],
          confirm_before_save: true
        }
      },
      {
        body: {
          id: 1,
          meal_slot: "breakfast",
          source_text: "Breakfast: oats and banana",
          items: [],
          calories: 255,
          protein_g: 6.3,
          carbs_g: 54,
          fat_g: 3.3,
          confidence: 0.8,
          status: "confirmed",
          updated_at: "2026-03-05T09:15:00Z"
        }
      },
      {
        body: {
          ...emptyDayPayload,
          meal_entries: [
            {
              id: 1,
              meal_slot: "breakfast",
              source_text: "Breakfast: oats and banana",
              items: [],
              calories: 255,
              protein_g: 6.3,
              carbs_g: 54,
              fat_g: 3.3,
              confidence: 0.8,
              status: "confirmed",
              updated_at: "2026-03-05T09:15:00Z"
            }
          ],
          daily_totals: {
            calories: 255,
            protein_g: 6.3,
            carbs_g: 54,
            fat_g: 3.3
          }
        }
      }
    ]);

    render(<App />);

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Meal note"), "Breakfast: oats and banana");
    await user.click(screen.getByRole("button", { name: "Generate Draft" }));

    expect(await screen.findByText("Draft ready for review.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save Draft to Day" }));
    expect(await screen.findByText("Meal saved.")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Breakfast: oats and banana")).toBeInTheDocument();
    });
  });

  /**
   * Verify sync failures expose retry controls and recover cleanly.
   */
  it("allows retrying activity sync after a failure", async () => {
    mockFetchSequence([
      { body: emptyDayPayload },
      { status: 500, body: { detail: "Strava rate limit" } },
      {
        body: {
          started_at: "2026-03-05T09:00:00Z",
          finished_at: "2026-03-05T09:00:02Z",
          imported_count: 1,
          updated_count: 0,
          window_start: "2026-02-28",
          window_end: "2026-03-05",
          status: "success"
        }
      },
      {
        body: {
          ...emptyDayPayload,
          activity_entries: [
            {
              strava_activity_id: "demo-2026-03-05-run",
              name: "Run Session 2026-03-05",
              sport_type: "Run",
              start_time: "2026-03-05T07:30:00Z",
              elapsed_time_s: 3600,
              calories: 640,
              suffer_score: null,
              rpe_override: null
            }
          ]
        }
      }
    ]);

    render(<App />);

    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Sync Recent Activities" }));
    expect(await screen.findByText("Strava rate limit")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry Activity Sync" }));

    expect(await screen.findByText("Recent sync complete. Imported 1, updated 0.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Run Session 2026-03-05/)).toBeInTheDocument();
    });
  });
});
