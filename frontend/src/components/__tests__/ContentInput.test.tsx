import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as layoutIntelligenceApi from "../../api/layoutIntelligence";
import * as pptxApi from "../../api/pptxEnhancement";
import { ContentInput } from "../ContentInput";

vi.mock("../../api/pptxEnhancement");
vi.mock("../../api/layoutIntelligence");

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
      expect(screen.getByLabelText("Text Input")).toBeInTheDocument();
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

  describe("Text Input", () => {
    it("shows text input tab when selected", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      expect(screen.getByLabelText("Text Input")).toBeChecked();
      expect(
        screen.getByPlaceholderText(/Enter your presentation content here/),
      ).toBeInTheDocument();
    });

    it("displays character counter that updates on input", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      const counter = screen.getByTestId("character-counter");

      expect(counter).toHaveTextContent("0 / 10,000");

      await userEvent.type(textarea, "Hello World");

      expect(counter).toHaveTextContent("11 / 10,000");
    });

    it("calls generateFromText API when Generate Slides clicked", async () => {
      const mockResponse = {
        slides: [
          {
            layout_index: 0,
            title: "Generated Slide",
            bullet_points: ["Point 1", "Point 2"],
          },
        ],
        warnings: [],
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockResolvedValueOnce(
        mockResponse,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(
        textarea,
        "Our company achieved 50% growth this year.",
      );

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(layoutIntelligenceApi.generateFromText).toHaveBeenCalledWith(
          "Our company achieved 50% growth this year.",
        );
        expect(mockOnContentGenerated).toHaveBeenCalledWith(
          mockResponse.slides,
        );
      });
    });

    it("shows loading state during generation", async () => {
      vi.mocked(layoutIntelligenceApi.generateFromText).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  slides: [],
                  warnings: [],
                }),
              100,
            ),
          ),
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(screen.getByText("Generating Slides...")).toBeInTheDocument();
      });
    });

    it("disables button when textarea is empty", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const button = screen.getByTestId("generate-from-text-btn");
      expect(button).toBeDisabled();

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Some text");

      expect(button).not.toBeDisabled();
    });

    it("displays error message for empty text", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      // Button should be disabled for empty/whitespace text
      const button = screen.getByTestId("generate-from-text-btn");
      expect(button).toBeDisabled();
    });

    it("enforces 10,000 character limit on textarea", async () => {
      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId(
        "text-input-textarea",
      ) as HTMLTextAreaElement;
      expect(textarea).toHaveAttribute("maxlength", "10000");
    });

    it("displays timeout error message", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const timeoutError = new Error("timeout of 65000ms exceeded");
      Object.assign(timeoutError, {
        isAxiosError: true,
        code: "ECONNABORTED",
      });

      vi.mocked(layoutIntelligenceApi.generateFromText).mockRejectedValueOnce(
        timeoutError,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(
          screen.getByText(
            /Request timed out. The text may be too complex. Please try with shorter content./,
          ),
        ).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it("displays 504 error message", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const error = {
        isAxiosError: true,
        message: "Request failed with status code 504",
        response: {
          status: 504,
          data: { detail: "Gateway Timeout" },
        },
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockRejectedValueOnce(
        error as never,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(
          screen.getByText(
            /Processing took too long. Please try with shorter or simpler content./,
          ),
        ).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it("displays 400 error message", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const error = {
        isAxiosError: true,
        message: "Request failed with status code 400",
        response: {
          status: 400,
          data: { detail: "Invalid input format" },
        },
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockRejectedValueOnce(
        error as never,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(screen.getByText(/Invalid input format/)).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it("displays generic error message for other errors", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const error = {
        isAxiosError: true,
        message: "Request failed with status code 500",
        response: {
          status: 500,
          data: { detail: "Internal Server Error" },
        },
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockRejectedValueOnce(
        error as never,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to generate slides. Please try again./),
        ).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it("clears error when user starts typing", async () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const error = {
        isAxiosError: true,
        message: "Request failed",
        response: {
          status: 500,
          data: { detail: "Error" },
        },
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockRejectedValueOnce(
        error as never,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to generate slides/),
        ).toBeInTheDocument();
      });

      // Type more content - error should clear
      await userEvent.type(textarea, " more");

      expect(
        screen.queryByText(/Failed to generate slides/),
      ).not.toBeInTheDocument();

      consoleErrorSpy.mockRestore();
    });

    it("logs warnings from API response", async () => {
      const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const mockResponse = {
        slides: [
          {
            layout_index: 0,
            title: "Test",
            bullet_points: [],
          },
        ],
        warnings: ["Layout fallback applied", "Content truncated"],
      };

      vi.mocked(layoutIntelligenceApi.generateFromText).mockResolvedValueOnce(
        mockResponse,
      );

      render(<ContentInput onContentGenerated={mockOnContentGenerated} />);

      await userEvent.click(screen.getByLabelText("Text Input"));

      const textarea = screen.getByTestId("text-input-textarea");
      await userEvent.type(textarea, "Test content");

      await userEvent.click(screen.getByTestId("generate-from-text-btn"));

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          "Layout intelligence warnings:",
          mockResponse.warnings,
        );
      });

      consoleSpy.mockRestore();
    });
  });
});
