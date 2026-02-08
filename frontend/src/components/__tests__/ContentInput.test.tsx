import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { ContentInput } from "../ContentInput";
import * as pptxApi from "../../api/pptxEnhancement";

vi.mock("../../api/pptxEnhancement");

describe("ContentInput", () => {
  const mockOnContentGenerated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Basic Rendering", () => {
    it("renders with all source options", () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      expect(screen.getByText(/Choose Content Source/i)).toBeInTheDocument();
      expect(screen.getByLabelText("Web Search")).toBeInTheDocument();
      expect(screen.getByLabelText("Markdown Input")).toBeInTheDocument();
    });

    it("defaults to web_search source", () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      const webSearchRadio = screen.getByLabelText(
        "Web Search",
      ) as HTMLInputElement;
      expect(webSearchRadio).toBeChecked();
    });
  });

  describe("Source Selection", () => {
    it("switches to markdown source when selected", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      const markdownRadio = screen.getByLabelText("Markdown Input");
      await userEvent.click(markdownRadio);

      expect(markdownRadio).toBeChecked();
      expect(
        screen.getByPlaceholderText(/# Presentation Title/),
      ).toBeInTheDocument();
    });

    it("shows markdown textarea when markdown source is active", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      expect(textarea).toBeInTheDocument();
      expect(screen.getByText("Generate from Markdown")).toBeInTheDocument();
    });

    it("shows topic input when web search is active", () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      expect(screen.getByText("2. Define Topic")).toBeInTheDocument();
    });
  });

  describe("Extracted Content Support", () => {
    it("shows extracted content option when extractionId provided", () => {
      const mockSlides = [
        { layout_index: 0, title: "Test Slide", bullet_points: [] },
      ];

      render(
        <ContentInput
          onContentGenerated={mockOnContentGenerated}
          extractionId="test-id"
          extractedSlides={mockSlides}
        />,
      );

      expect(screen.getByLabelText("Extracted Content")).toBeInTheDocument();
    });

    it("does not show extracted content option without extractionId", () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      expect(
        screen.queryByLabelText("Extracted Content"),
      ).not.toBeInTheDocument();
    });

    it("does not show extracted content option without extractedSlides", () => {
      render(
        <ContentInput
          onContentGenerated={mockOnContentGenerated}
          extractionId="test-id"
        />,
      );

      expect(
        screen.queryByLabelText("Extracted Content"),
      ).not.toBeInTheDocument();
    });

    it("displays slide count for extracted content", async () => {
      const mockSlides = [
        { layout_index: 0, title: "Slide 1", bullet_points: [] },
        { layout_index: 1, title: "Slide 2", bullet_points: [] },
        { layout_index: 2, title: "Slide 3", bullet_points: [] },
      ];

      render(
        <ContentInput
          onContentGenerated={mockOnContentGenerated}
          extractionId="test-id"
          extractedSlides={mockSlides}
        />,
      );

      await userEvent.click(screen.getByLabelText("Extracted Content"));

      expect(
        screen.getByText(/Using 3 slides from extracted PPTX content/),
      ).toBeInTheDocument();
    });

    it("uses extracted slides when button clicked", async () => {
      const mockSlides = [
        {
          layout_index: 0,
          title: "Extracted Slide",
          bullet_points: ["Point 1"],
        },
      ];

      render(
        <ContentInput
          onContentGenerated={mockOnContentGenerated}
          extractionId="test-id"
          extractedSlides={mockSlides}
        />,
      );

      await userEvent.click(screen.getByLabelText("Extracted Content"));
      await userEvent.click(screen.getByText("Use Extracted Content"));

      expect(mockOnContentGenerated).toHaveBeenCalledWith(mockSlides);
    });
  });

  describe("Markdown Parsing", () => {
    it("calls parseMarkdown when button clicked", async () => {
      const mockResponse = {
        presentation_title: "Test Presentation",
        slides: [
          {
            layout_index: 0,
            title: "Slide 1",
            bullet_points: ["Point A"],
            bullets: [{ text: "Point A", level: 0 }],
          },
        ],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValueOnce(mockResponse);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test\n\n## Slide 1\n- Point A");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(pptxApi.parseMarkdown).toHaveBeenCalledWith(
          "# Test\n\n## Slide 1\n- Point A",
        );
        expect(mockOnContentGenerated).toHaveBeenCalledWith(
          mockResponse.slides,
        );
      });
    });

    it("shows loading state during parsing", async () => {
      vi.mocked(pptxApi.parseMarkdown).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  slides: [],
                  warnings: [],
                  presentation_title: null,
                }),
              100,
            ),
          ),
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(screen.getByText("Parsing...")).toBeInTheDocument();
      });
    });

    it("logs warnings from API response", async () => {
      const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const mockResponse = {
        presentation_title: "Test",
        slides: [],
        warnings: ["Invalid URL: ftp://example.com"],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValueOnce(mockResponse);

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      await userEvent.click(screen.getByText("Generate from Markdown"));

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          "Markdown parsing warnings:",
          mockResponse.warnings,
        );
      });

      consoleSpy.mockRestore();
    });

    it("displays error on parsing failure", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      vi.mocked(pptxApi.parseMarkdown).mockRejectedValueOnce(
        new Error("Parse error"),
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

      consoleErrorSpy.mockRestore();
    });

    it("disables generate button when markdown is empty", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const button = screen.getByText("Generate from Markdown");
      expect(button).toBeDisabled();
    });

    it("enables generate button when markdown is entered", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      const button = screen.getByText("Generate from Markdown");
      expect(button).not.toBeDisabled();
    });

    it("disables generate button during loading", async () => {
      vi.mocked(pptxApi.parseMarkdown).mockImplementation(
        () => new Promise(() => {}), // Never resolves
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      await userEvent.type(textarea, "# Test");

      const button = screen.getByText("Generate from Markdown");
      await userEvent.click(button);

      await waitFor(() => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe("Textarea Interaction", () => {
    it("updates markdown content on textarea change", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(
        /# Presentation Title/,
      ) as HTMLTextAreaElement;
      await userEvent.type(textarea, "# My Title");

      expect(textarea.value).toBe("# My Title");
    });

    it("has correct placeholder text", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Markdown Input"));

      const textarea = screen.getByPlaceholderText(/# Presentation Title/);
      expect(textarea).toHaveAttribute("placeholder");
      expect(textarea.getAttribute("placeholder")).toContain("Slide 1");
      expect(textarea.getAttribute("placeholder")).toContain("Bullet point");
    });
  });
});
