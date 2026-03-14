import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App shell", () => {
  it("renders the scaffold headline", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Personal Endurance Trainer Log" })
    ).toBeInTheDocument();
  });

  it("lists the backend health endpoint in scaffold features", () => {
    render(<App />);

    expect(
      screen.getByText(/FastAPI backend with \/api\/health endpoint/i)
    ).toBeInTheDocument();
  });
});
