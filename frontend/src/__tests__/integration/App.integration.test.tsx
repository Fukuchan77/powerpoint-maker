import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AxiosResponse } from "axios";
import axios from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import type { SlideContent, TemplateAnalysisResult } from "../../types";

// Mock axios
vi.mock("axios");

// Mock URL.createObjectURL
window.URL.createObjectURL = vi.fn(() => "mock-url");

describe("App Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ... (skipping first test which is already fixed mostly, I should target specific lines)
  // wait, replace_file_content replaces a block. I should be careful not to overwrite my previous fix if I target the whole file.
  // I will target specific blocks.

  it("completes the full flow: upload -> research -> generate", async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    // 1. Check initial state - wait for lazy-loaded components
    expect(screen.getByText(/AI PowerPoint Agent/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText(/1. Upload PowerPoint Template/i),
      ).toBeInTheDocument();
    });

    // Topic input should not be visible yet
    expect(screen.queryByText(/2. Define Topic/i)).not.toBeInTheDocument();

    // 2. Upload Template
    const file = new File(["(content)"], "template.pptx", {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });

    const fileInputRetry = container.querySelector('input[type="file"]');
    expect(fileInputRetry).toBeInTheDocument();

    // Mock API response for analyze
    // Mock API response for analyze
    const analyzeResponse: Partial<AxiosResponse<TemplateAnalysisResult>> = {
      data: {
        filename: "template.pptx",
        masters: [{ layouts: [{}, {}] }],
      } as TemplateAnalysisResult,
    };
    vi.mocked(axios.post).mockResolvedValueOnce(analyzeResponse);

    if (fileInputRetry) {
      await user.upload(fileInputRetry as HTMLElement, file);
    }

    // Wait for analysis to complete and Topic Input to appear (lazy loaded)
    await waitFor(() => {
      expect(
        screen.getByText(/Template Loaded: template.pptx/i),
      ).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/2. Define Topic/i)).toBeInTheDocument();
    });

    // 3. Enter Topic and Research
    const topicInput = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await user.type(topicInput, "AI in Healthcare");

    const generateContentBtn = screen.getByRole("button", {
      name: /Generate Content/i,
    });

    // Mock API response for research
    // Mock API response for research
    const researchResponse: Partial<AxiosResponse<SlideContent[]>> = {
      data: [
        {
          layout_index: 0,
          title: "Intro to AI",
          bullet_points: ["Point 1", "Point 2"],
        } as SlideContent,
      ],
    };
    vi.mocked(axios.post).mockResolvedValueOnce(researchResponse);

    await user.click(generateContentBtn);

    // Wait for Preview to appear
    await waitFor(() => {
      expect(screen.getByText(/3. Preview & Generate/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Slide 1: Intro to AI/i)).toBeInTheDocument();

    // 4. Generate Presentation
    const generatePptxBtn = screen.getByRole("button", {
      name: /Generate Presentation/i,
    });

    // Mock API response for generate
    // Mock API response for generate
    const generateResponse: Partial<AxiosResponse<Blob>> = {
      data: new Blob(["mock content"]),
    };
    vi.mocked(axios.post).mockResolvedValueOnce(generateResponse);

    await user.click(generatePptxBtn);

    // Wait for Download button
    await waitFor(() => {
      expect(screen.getByText(/Download .pptx/i)).toBeInTheDocument();
    });

    const downloadLink = screen.getByText(/Download .pptx/i);
    expect(downloadLink).toHaveAttribute("href", "mock-url");
  });

  it("displays error when analysis fails", async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    // Wait for lazy-loaded components first
    await waitFor(() => {
      expect(container.querySelector('input[type="file"]')).toBeInTheDocument();
    });

    const fileInput = container.querySelector('input[type="file"]');
    const file = new File([""], "bad.pptx", { type: "application/pdf" }); // Type doesn't matter for mock

    // Mock API failure
    vi.mocked(axios.post).mockRejectedValueOnce(new Error("Network Error"));

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, file);
    }

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to analyze template/i),
      ).toBeInTheDocument();
    });
  });
});
