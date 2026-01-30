import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders without crashing", () => {
    render(<App />);
    // Adjust this expectation based on actual App content,
    // for now just checking if it renders
    // Check for specific text that should be present
    expect(screen.getByText(/Upload PowerPoint Template/i)).toBeInTheDocument();
  });
});
