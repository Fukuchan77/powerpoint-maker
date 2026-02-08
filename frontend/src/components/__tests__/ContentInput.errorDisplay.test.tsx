import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { ContentInput } from "../ContentInput";
import * as pptxApi from "../../api/pptxEnhancement";
import axios from "axios";

vi.mock("../../api/pptxEnhancement");
vi.mock("axios");

describe("ContentInput - Error Display", () => {
  const mockOnContentGenerated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Structured Syntax Error Display", () => {
    it("displays structured error for MARKDOWN_SYNTAX_ERROR", async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: {
              error_code: "MARKDOWN_SYNTAX_ERROR",
              message: "No slides found. Use '## Heading' to create slides.",
              location: {
                line: 1,
                column: 1,
              },
            },
          },
        },
      };

      vi.mocked(axios.isAxiosError).mockReturnValue(true);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(mockError);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Just a title");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(screen.getByText("Markdown Syntax Error")).toBeInTheDocument();
        expect(
          screen.getByText(
            "No slides found. Use '## Heading' to create slides.",
          ),
        ).toBeInTheDocument();
        expect(
          screen.getByText(/Location: Line 1, Column 1/),
        ).toBeInTheDocument();
      });
    });

    it("displays line and column information correctly", async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: {
              error_code: "MARKDOWN_SYNTAX_ERROR",
              message: "Empty Markdown content.",
              location: {
                line: 5,
                column: 12,
              },
            },
          },
        },
      };

      vi.mocked(axios.isAxiosError).mockReturnValue(true);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(mockError);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(
          screen.getByText(/Location: Line 5, Column 12/),
        ).toBeInTheDocument();
      });
    });

    it("shows generic error for non-syntax errors", async () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            detail: "Internal server error",
          },
        },
      };

      vi.mocked(axios.isAxiosError).mockReturnValue(true);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(mockError);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to parse Markdown/i),
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Markdown Syntax Error"),
        ).not.toBeInTheDocument();
      });
    });

    it("shows generic error for non-400 status codes", async () => {
      const mockError = {
        response: {
          status: 422,
          data: {
            detail: {
              error_code: "VALIDATION_ERROR",
              message: "Content too large",
            },
          },
        },
      };

      vi.mocked(axios.isAxiosError).mockReturnValue(true);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(mockError);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to parse Markdown/i),
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Markdown Syntax Error"),
        ).not.toBeInTheDocument();
      });
    });

    it("clears syntax error when user starts typing", async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: {
              error_code: "MARKDOWN_SYNTAX_ERROR",
              message: "No slides found.",
              location: { line: 1, column: 1 },
            },
          },
        },
      };

      vi.mocked(axios.isAxiosError).mockReturnValue(true);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(mockError);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(screen.getByText("Markdown Syntax Error")).toBeInTheDocument();
      });

      // Start typing again
      await userEvent.type(textarea, "\n\n## Slide 1");

      await waitFor(() => {
        expect(
          screen.queryByText("Markdown Syntax Error"),
        ).not.toBeInTheDocument();
      });
    });

    it("clears generic error when user starts typing", async () => {
      vi.mocked(axios.isAxiosError).mockReturnValue(false);
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(
        new Error("Network error"),
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to parse Markdown/i),
        ).toBeInTheDocument();
      });

      // Start typing again
      await userEvent.type(textarea, " more");

      await waitFor(() => {
        expect(
          screen.queryByText(/Failed to parse Markdown/i),
        ).not.toBeInTheDocument();
      });
    });
  });
});
