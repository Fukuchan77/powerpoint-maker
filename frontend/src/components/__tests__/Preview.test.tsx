import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import axios, { type AxiosResponse } from "axios";
import { Preview } from "../Preview";
import type { SlideContent, TemplateAnalysisResult } from "../../types";

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
});
