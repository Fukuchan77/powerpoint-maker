import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import type { AxiosResponse } from "axios";
import axios from "axios";
import { TemplateUploader } from "../TemplateUploader";

vi.mock("axios");

describe("TemplateUploader", () => {
  const mockOnAnalysisComplete = vi.fn();
  const mockOnContentExtracted = vi.fn();
  const mockOnUseDefault = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Basic Rendering", () => {
    it("renders correctly with required props", () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );
      expect(
        screen.getByText(/Upload PowerPoint Template/i),
      ).toBeInTheDocument();
      expect(document.querySelector('input[type="file"]')).toBeInTheDocument();
    });

    it("renders default template button", () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );
      expect(screen.getByText("Use Default Template")).toBeInTheDocument();
    });
  });

  describe("Mode Selection", () => {
    it("defaults to template mode", () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const templateRadio = screen.getByLabelText(
        "Template Only",
      ) as HTMLInputElement;
      expect(templateRadio).toBeChecked();
    });

    it("switches to content mode when selected", async () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const contentRadio = screen.getByLabelText(
        "Extract Content",
      ) as HTMLInputElement;
      await userEvent.click(contentRadio);

      expect(contentRadio).toBeChecked();
    });

    it("displays both mode options", () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      expect(screen.getByLabelText("Template Only")).toBeInTheDocument();
      expect(screen.getByLabelText("Extract Content")).toBeInTheDocument();
    });
  });

  describe("File Upload - Template Mode", () => {
    it("calls analyze-template endpoint in template mode", async () => {
      const mockResult = {
        filename: "test.pptx",
        template_id: "12345",
        masters: [],
      };

      vi.mocked(axios.post).mockResolvedValueOnce({
        data: mockResult,
      } as AxiosResponse);

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const file = new File(["dummy content"], "test.pptx", {
        type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          "/api/analyze-template",
          expect.any(FormData),
          expect.objectContaining({
            headers: { "Content-Type": "multipart/form-data" },
          }),
        );
        expect(mockOnAnalysisComplete).toHaveBeenCalledWith(mockResult);
      });
    });

    it("displays loading state during template analysis", async () => {
      vi.mocked(axios.post).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ data: { filename: "test.pptx", masters: [] } }),
              100,
            ),
          ) as unknown as Promise<AxiosResponse>,
      );

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const file = new File(["content"], "test.pptx", {
        type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(screen.getByText(/Processing.../i)).toBeInTheDocument();
      });
    });
  });

  describe("File Upload - Content Mode", () => {
    it("calls extract-content endpoint in content mode", async () => {
      const mockResult = {
        extraction_id: "abc-123",
        filename: "test.pptx",
        slides: [],
        images: [],
        warnings: [],
        expires_at: "2026-02-02T00:00:00Z",
      };

      vi.mocked(axios.post).mockResolvedValueOnce({
        data: mockResult,
      } as AxiosResponse);

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onContentExtracted={mockOnContentExtracted}
          onUseDefault={mockOnUseDefault}
        />,
      );

      // Switch to content mode
      const contentRadio = screen.getByLabelText("Extract Content");
      await userEvent.click(contentRadio);

      const file = new File(["content"], "test.pptx", {
        type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          "/api/extract-content?mode=content",
          expect.any(FormData),
          expect.objectContaining({
            headers: { "Content-Type": "multipart/form-data" },
          }),
        );
        expect(mockOnContentExtracted).toHaveBeenCalledWith(mockResult);
      });
    });

    it("does not call onContentExtracted if callback not provided", async () => {
      const mockResult = {
        extraction_id: "abc-123",
        slides: [],
        images: [],
        warnings: [],
      };

      vi.mocked(axios.post).mockResolvedValueOnce({
        data: mockResult,
      } as AxiosResponse);

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      // Switch to content mode
      const contentRadio = screen.getByLabelText("Extract Content");
      await userEvent.click(contentRadio);

      const file = new File(["content"], "test.pptx");
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalled();
        // Should not throw error
      });
    });
  });

  describe("Default Template Button", () => {
    it("calls onUseDefault when clicked", async () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const defaultButton = screen.getByText("Use Default Template");
      await userEvent.click(defaultButton);

      expect(mockOnUseDefault).toHaveBeenCalled();
    });

    it("disables default button during upload", async () => {
      vi.mocked(axios.post).mockImplementation(
        () => new Promise(() => {}) as unknown as Promise<AxiosResponse>,
      );

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const file = new File(["content"], "test.pptx");
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        const defaultButton = screen.getByText("Use Default Template");
        expect(defaultButton).toBeDisabled();
      });
    });
  });

  describe("Error Handling", () => {
    it("displays error for failed template analysis", async () => {
      vi.mocked(axios.post).mockRejectedValueOnce(new Error("Network Error"));

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const file = new File([""], "test.pptx");
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to analyze template/i),
        ).toBeInTheDocument();
      });
    });

    it("displays error for failed content extraction", async () => {
      vi.mocked(axios.post).mockRejectedValueOnce(
        new Error("Extraction failed"),
      );

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onContentExtracted={mockOnContentExtracted}
          onUseDefault={mockOnUseDefault}
        />,
      );

      // Switch to content mode
      const contentRadio = screen.getByLabelText("Extract Content");
      await userEvent.click(contentRadio);

      const file = new File([""], "test.pptx");
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to extract content/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Disabled States", () => {
    it("disables file input while loading", async () => {
      vi.mocked(axios.post).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () => resolve({ data: { filename: "test.pptx", masters: [] } }),
              100,
            ),
          ) as unknown as Promise<AxiosResponse>,
      );

      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const file = new File(["content"], "test.pptx");
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      await userEvent.upload(fileInput, file);

      await waitFor(() => {
        expect(fileInput).toBeDisabled();
      });

      await waitFor(() => {
        expect(mockOnAnalysisComplete).toHaveBeenCalled();
        expect(fileInput).not.toBeDisabled();
      });
    });
  });

  describe("Edge Cases", () => {
    it("does not call API when no file is selected", async () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      const changeEvent = new Event("change", { bubbles: true });
      Object.defineProperty(changeEvent, "target", {
        value: { files: null },
        writable: false,
      });

      fileInput.dispatchEvent(changeEvent);

      await waitFor(() => {
        expect(axios.post).not.toHaveBeenCalled();
      });
    });

    it("does not call API when empty file list provided", async () => {
      render(
        <TemplateUploader
          onAnalysisComplete={mockOnAnalysisComplete}
          onUseDefault={mockOnUseDefault}
        />,
      );

      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      const changeEvent = new Event("change", { bubbles: true });
      Object.defineProperty(changeEvent, "target", {
        value: { files: [] },
        writable: false,
      });

      fileInput.dispatchEvent(changeEvent);

      await waitFor(() => {
        expect(axios.post).not.toHaveBeenCalled();
      });
    });
  });
});
