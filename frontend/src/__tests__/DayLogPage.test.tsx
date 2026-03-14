import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DayLogPage } from "../DayLogPage";

/**
 * Renders the day-log page and returns a configured user-event instance.
 *
 * @param initialDate - Optional starting date for deterministic test flows.
 * @returns A configured user-event controller.
 * @example
 * const user = renderPage("2026-03-06");
 */
function renderPage(initialDate = "2026-03-06"): ReturnType<typeof userEvent.setup> {
  const user = userEvent.setup();
  render(<DayLogPage initialDate={initialDate} />);
  return user;
}

/**
 * Returns scoped queries for the assistant composer panel.
 *
 * @returns Query helpers scoped to the assistant composer.
 * @example
 * const composer = getComposer();
 */
function getComposer(): ReturnType<typeof within> {
  return within(screen.getByLabelText("Assistant composer"));
}

describe("DayLogPage", () => {
  it("renders loading first, then shows meals, activities, and glucose uploads", async () => {
    renderPage();

    expect(screen.getByText("Loading selected day log...")).toBeInTheDocument();

    await screen.findByRole("heading", { name: "Day summary" });

    expect(screen.getByText("Tempo Run")).toBeInTheDocument();
    expect(screen.getByText("chia pudding with berries")).toBeInTheDocument();
    expect(screen.getByText("libre-2026-03-06-morning.png")).toBeInTheDocument();
  });

  it("navigates to an empty day and shows empty-state messaging", async () => {
    const user = renderPage();

    await screen.findByRole("heading", { name: "Day summary" });
    const daySelector = within(screen.getByLabelText("Day selector"));
    await user.click(daySelector.getByRole("button", { name: "Next" }));

    await screen.findByRole("heading", { name: "Day summary" });

    const mealEmptyStates = screen.getAllByText("No meals logged yet.");
    expect(mealEmptyStates).toHaveLength(4);
    expect(screen.getByText("No activities synced yet.")).toBeInTheDocument();
    expect(screen.getByText("No glucose screenshots yet.")).toBeInTheDocument();
  });

  it("creates a meal draft, shows preview, and saves it into the selected slot", async () => {
    const user = renderPage("2026-03-07");

    await screen.findByRole("heading", { name: "Day summary" });
    const composer = getComposer();

    await user.selectOptions(composer.getByLabelText("Meal slot"), "lunch");
    await user.type(composer.getByLabelText("Meal description"), "oats, banana, yogurt");
    await user.click(composer.getByRole("button", { name: "Generate meal draft" }));

    await screen.findByText("Draft preview");
    expect(await screen.findByText(/Totals:/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save meal to day" }));

    await screen.findByText("Meal saved to lunch.");

    const lunchSection = screen.getByLabelText("Lunch section");
    expect(within(lunchSection).getByText("oats, banana, yogurt")).toBeInTheDocument();
  });

  it("shows a save error when the adapter rejects persistence", async () => {
    const user = renderPage("2026-03-07");

    await screen.findByRole("heading", { name: "Day summary" });
    const composer = getComposer();

    await user.type(composer.getByLabelText("Meal description"), "#fail-save eggs");
    await user.click(composer.getByRole("button", { name: "Generate meal draft" }));
    await screen.findByRole("button", { name: "Save meal to day" });

    await user.click(screen.getByRole("button", { name: "Save meal to day" }));

    await screen.findByText("Meal save failed in the mock adapter. Remove #fail-save and retry.");
  });

  it("shows microphone trigger feedback and appends mocked transcript", async () => {
    const user = renderPage("2026-03-07");

    await screen.findByRole("heading", { name: "Day summary" });
    const composer = getComposer();

    await user.click(composer.getByRole("button", { name: "Start voice note" }));
    expect(composer.getByRole("button", { name: "Recording voice note..." })).toBeInTheDocument();

    await waitFor(() => {
      expect(composer.getByLabelText("Meal description")).toHaveValue("eggs, toast, avocado");
    });
  });
});
