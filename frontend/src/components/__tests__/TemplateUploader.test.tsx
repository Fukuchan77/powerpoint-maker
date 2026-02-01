import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import type { AxiosResponse } from "axios";
import axios from "axios";
import { TemplateUploader } from "../TemplateUploader";

vi.mock("axios");

describe("TemplateUploader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it("renders correctly", () => {
    render(<TemplateUploader onAnalysisComplete={() => {}} />);
    expect(screen.getByText(/Upload PowerPoint Template/i)).toBeInTheDocument();
    // Check for file input
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  it("handles file upload and calls onAnalysisComplete on success", async () => {
    const handleComplete = vi.fn();
    const mockResult = { filename: "test.pptx", masters: [] };
    // Add delay to check loading state
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: mockResult }), 100),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<TemplateUploader onAnalysisComplete={handleComplete} />);

    const file = new File(["dummy content"], "test.pptx", {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });
    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(screen.getByText(/Analyzing template.../i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledTimes(1);
      expect(handleComplete).toHaveBeenCalledWith(mockResult);
    });
  });

  it("displays error message on failure", async () => {
    vi.mocked(axios.post).mockRejectedValueOnce(new Error("Network Error"));

    render(<TemplateUploader onAnalysisComplete={() => {}} />);
    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const file = new File([""], "test.pptx");

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to analyze template/i),
      ).toBeInTheDocument();
    });
  });

  it("does not call API when no file is selected", async () => {
    render(<TemplateUploader onAnalysisComplete={() => {}} />);
    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    // Simulate change event with no files
    const changeEvent = new Event("change", { bubbles: true });
    Object.defineProperty(changeEvent, "target", {
      value: { files: null },
      writable: false,
    });

    fileInput.dispatchEvent(changeEvent);

    // Should not call API
    await waitFor(() => {
      expect(axios.post).not.toHaveBeenCalled();
    });
  });

  it("does not call API when empty file list is provided", async () => {
    render(<TemplateUploader onAnalysisComplete={() => {}} />);
    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    // Simulate change event with empty files array
    const changeEvent = new Event("change", { bubbles: true });
    Object.defineProperty(changeEvent, "target", {
      value: { files: [] },
      writable: false,
    });

    fileInput.dispatchEvent(changeEvent);

    // Should not call API
    await waitFor(() => {
      expect(axios.post).not.toHaveBeenCalled();
    });
  });

  it("disables file input while loading", async () => {
    const handleComplete = vi.fn();
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ data: { filename: "test.pptx", masters: [] } }),
            100,
          ),
        ) as unknown as Promise<AxiosResponse>,
    );

    render(<TemplateUploader onAnalysisComplete={handleComplete} />);

    const file = new File(["dummy content"], "test.pptx", {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });
    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    // Input should be disabled while loading
    await waitFor(() => {
      expect(fileInput).toBeDisabled();
    });

    // After completion, should be enabled again
    await waitFor(() => {
      expect(handleComplete).toHaveBeenCalled();
      expect(fileInput).not.toBeDisabled();
    });
  });
});
