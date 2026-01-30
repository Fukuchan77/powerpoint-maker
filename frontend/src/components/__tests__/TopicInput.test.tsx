import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import axios from "axios";
import type { AxiosResponse } from "axios";
import { TopicInput } from "../TopicInput";

vi.mock("axios");

describe("TopicInput", () => {
  it("renders and updates input value", async () => {
    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, "Test Topic");

    expect(input).toHaveValue("Test Topic");
  });

  it("calls API and returns content on button click", async () => {
    const handleGenerated = vi.fn();
    const mockSlides = [
      { title: "Slide 1", bullet_points: [], layout_index: 0 },
    ];
    // Add delay to check loading state
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: mockSlides }), 100),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<TopicInput onContentGenerated={handleGenerated} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, "Test Topic");

    const button = screen.getByRole("button", { name: /Generate Content/i });
    await userEvent.click(button);

    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("Researching...");

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith("/api/research", null, {
        params: { topic: "Test Topic" },
      });
      expect(handleGenerated).toHaveBeenCalledWith(mockSlides);
    });

    expect(button).toBeEnabled();
    expect(button).toHaveTextContent("Generate Content");
  });

  it("shows error on failure", async () => {
    vi.mocked(axios.post).mockRejectedValueOnce(new Error("Failed"));
    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, "Test Topic");

    const button = screen.getByRole("button", { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to generate content/i),
      ).toBeInTheDocument();
    });
  });
});
