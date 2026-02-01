import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axios, { type AxiosResponse } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SlideContent, TemplateAnalysisResult } from "../../types";
import { Preview } from "../Preview";

vi.mock("axios");

describe("Preview", () => {
  const mockSlides: SlideContent[] = [
    { title: "Slide 1", bullet_points: ["Point 1"], layout_index: 0 },
    { title: "Slide 2", bullet_points: ["Point 2"], layout_index: 1 },
  ];
  const mockTemplate: TemplateAnalysisResult = {
    filename: "test.pptx",
    masters: [],
    template_id: "test-id",
  };

  beforeEach(() => {
    // Mock URL.createObjectURL
    window.URL.createObjectURL = vi.fn(() => "blob:http://localhost:3000/foo");
    vi.clearAllMocks();
  });

  it("renders slides correctly", () => {
    render(<Preview slides={mockSlides} template={mockTemplate} />);

    expect(screen.getByText("Slide 1: Slide 1")).toBeInTheDocument();
    expect(screen.getByText("Point 1")).toBeInTheDocument();
    expect(screen.getByText("Slide 2: Slide 2")).toBeInTheDocument();
  });

  it("allows changing layout index", async () => {
    render(<Preview slides={mockSlides} template={mockTemplate} />);

    // Find inputs for layout index
    const inputs = screen.getAllByRole("spinbutton"); // number inputs
    expect(inputs).toHaveLength(2);

    await userEvent.clear(inputs[0]);
    await userEvent.type(inputs[0], "5");

    expect(inputs[0]).toHaveValue(5);
  });

  it("handles generation and download link", async () => {
    // Add delay
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: new Blob(["test"]) }), 100),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<Preview slides={mockSlides} template={mockTemplate} />);

    const button = screen.getByRole("button", {
      name: /Generate Presentation/i,
    });
    await userEvent.click(button);

    expect(screen.getByText("Generating PPTX...")).toBeInTheDocument();

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        "/api/generate",
        expect.objectContaining({
          template_filename: "test.pptx",
          slides: mockSlides,
        }),
        expect.any(Object),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Download .pptx")).toBeInTheDocument();
    });
    expect(screen.getByText("Download .pptx")).toHaveAttribute(
      "href",
      "blob:http://localhost:3000/foo",
    );
  });

  it("handles generation errors gracefully", async () => {
    const alertMock = vi.spyOn(window, "alert").mockImplementation(() => {});
    const consoleErrorMock = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    // Add delay to allow state update to be captured
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Network error")), 50),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<Preview slides={mockSlides} template={mockTemplate} />);

    const button = screen.getByRole("button", {
      name: /Generate Presentation/i,
    });
    await userEvent.click(button);

    // Use waitFor to catch the loading state
    await waitFor(() => {
      expect(screen.getByText("Generating PPTX...")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith("Generation failed");
    });

    await waitFor(() => {
      expect(consoleErrorMock).toHaveBeenCalledWith(
        "Generation failed",
        expect.any(Error),
      );
    });

    expect(
      screen.getByRole("button", { name: /Generate Presentation/i }),
    ).toBeInTheDocument();

    alertMock.mockRestore();
    consoleErrorMock.mockRestore();
  });

  it("disables generate button while generating", async () => {
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: new Blob(["test"]) }), 100),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<Preview slides={mockSlides} template={mockTemplate} />);

    const button = screen.getByRole("button", {
      name: /Generate Presentation/i,
    });

    expect(button).not.toBeDisabled();

    await userEvent.click(button);

    // Button should be disabled during generation
    expect(screen.getByText("Generating PPTX...")).toBeDisabled();
  });

  it("handles invalid layout index input", async () => {
    // Create fresh mock slides to avoid state pollution
    const freshSlides: SlideContent[] = [
      { title: "Slide 1", bullet_points: ["Point 1"], layout_index: 0 },
      { title: "Slide 2", bullet_points: ["Point 2"], layout_index: 1 },
    ];

    render(<Preview slides={freshSlides} template={mockTemplate} />);

    const inputs = screen.getAllByRole("spinbutton");

    // Verify initial value from mockSlides[0].layout_index which is 0
    expect(inputs[0]).toHaveValue(0);

    // Clear and try to type invalid input
    await userEvent.clear(inputs[0]);
    await userEvent.type(inputs[0], "abc");

    // Number input rejects non-numeric input, should be empty or default
    const finalValue = (inputs[0] as HTMLInputElement).value;
    expect(finalValue === "" || finalValue === "0").toBe(true);
  });

  it("renders empty slides correctly", () => {
    render(<Preview slides={[]} template={mockTemplate} />);

    expect(screen.getByText("3. Preview & Generate")).toBeInTheDocument();
    expect(screen.queryByRole("spinbutton")).not.toBeInTheDocument();
  });
});
