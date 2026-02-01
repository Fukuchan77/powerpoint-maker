import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders without crashing", async () => {
    render(<App />);

    // Wait for lazy-loaded components to render
    await waitFor(() => {
      expect(
        screen.getByText(/Upload PowerPoint Template/i),
      ).toBeInTheDocument();
    });

    // Check for main heading
    expect(screen.getByText(/AI PowerPoint Agent/i)).toBeInTheDocument();
  });
});
