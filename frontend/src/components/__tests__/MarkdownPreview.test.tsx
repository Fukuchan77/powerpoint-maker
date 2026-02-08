import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MarkdownPreview } from "../MarkdownPreview";
import * as pptxApi from "../../api/pptxEnhancement";

vi.mock("../../api/pptxEnhancement");

describe("MarkdownPreview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Empty State", () => {
    it("shows placeholder when content is empty", () => {
      render(<MarkdownPreview markdownContent="" />);
      expect(screen.getByText(/Start typing Markdown/i)).toBeInTheDocument();
    });
  });

  describe("Debouncing", () => {
    it("debounces parsing with default delay", async () => {
      const mockResponse = {
        presentation_title: "Test",
        slides: [
          { layout_index: 0, title: "Slide 1", bullet_points: ["Point 1"] },
        ],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValue(mockResponse);

      render(
        <MarkdownPreview
          markdownContent="# Test\n\n## Slide 1\n- Point 1"
          debounceMs={100}
        />,
      );

      // Should not call immediately
      expect(pptxApi.parseMarkdown).not.toHaveBeenCalled();

      // Wait for debounce
      await waitFor(
        () => {
          expect(pptxApi.parseMarkdown).toHaveBeenCalledTimes(1);
        },
        { timeout: 300 },
      );
    });
  });

  describe("Slide Display", () => {
    it("displays parsed slides", async () => {
      const mockResponse = {
        presentation_title: "My Presentation",
        slides: [
          {
            layout_index: 0,
            title: "Introduction",
            bullet_points: ["Welcome", "Overview"],
          },
          { layout_index: 0, title: "Conclusion", bullet_points: ["Summary"] },
        ],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValue(mockResponse);

      render(
        <MarkdownPreview
          markdownContent="# Test\n\n## Introduction\n- Welcome\n- Overview\n\n## Conclusion\n- Summary"
          debounceMs={50}
        />,
      );

      await waitFor(
        () => {
          expect(screen.getByText("2 slides detected")).toBeInTheDocument();
        },
        { timeout: 300 },
      );

      expect(screen.getByText("Slide 1: Introduction")).toBeInTheDocument();
      expect(screen.getByText("Welcome")).toBeInTheDocument();
      expect(screen.getByText("Overview")).toBeInTheDocument();
      expect(screen.getByText("Slide 2: Conclusion")).toBeInTheDocument();
      expect(screen.getByText("Summary")).toBeInTheDocument();
    });

    it("displays slide with image", async () => {
      const mockResponse = {
        presentation_title: "Test",
        slides: [
          {
            layout_index: 0,
            title: "Slide with Image",
            bullet_points: [],
            image_url: "https://example.com/image.jpg",
          },
        ],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValue(mockResponse);

      render(
        <MarkdownPreview
          markdownContent="# Test\n\n## Slide with Image\n![img](https://example.com/image.jpg)"
          debounceMs={50}
        />,
      );

      await waitFor(
        () => {
          expect(
            screen.getByText(/Image: https:\/\/example.com\/image.jpg/),
          ).toBeInTheDocument();
        },
        { timeout: 300 },
      );
    });

    it("shows message when no slides detected", async () => {
      const mockResponse = {
        presentation_title: "Test",
        slides: [],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValue(mockResponse);

      render(
        <MarkdownPreview markdownContent="# Just a title" debounceMs={50} />,
      );

      await waitFor(
        () => {
          expect(screen.getByText(/No slides detected/i)).toBeInTheDocument();
        },
        { timeout: 300 },
      );
    });
  });

  describe("Warnings Display", () => {
    it("displays warnings from parser", async () => {
      const mockResponse = {
        presentation_title: "Test",
        slides: [{ layout_index: 0, title: "Slide 1", bullet_points: [] }],
        warnings: ["Warning 1: Invalid URL", "Warning 2: Long heading"],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValue(mockResponse);

      render(
        <MarkdownPreview
          markdownContent="# Test\n\n## Slide 1"
          debounceMs={50}
        />,
      );

      await waitFor(
        () => {
          expect(
            screen.getByText(/Warning 1: Invalid URL/),
          ).toBeInTheDocument();
        },
        { timeout: 300 },
      );

      expect(screen.getByText(/Warning 2: Long heading/)).toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    it("handles parse errors gracefully", async () => {
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValue(
        new Error("Parse failed"),
      );

      render(<MarkdownPreview markdownContent="# Invalid" debounceMs={50} />);

      await waitFor(
        () => {
          expect(screen.getByText(/Invalid Markdown/i)).toBeInTheDocument();
        },
        { timeout: 300 },
      );
    });

    it("clears slides on error", async () => {
      const mockResponse = {
        presentation_title: "Test",
        slides: [{ layout_index: 0, title: "Slide 1", bullet_points: [] }],
        warnings: [],
      };

      vi.mocked(pptxApi.parseMarkdown).mockResolvedValueOnce(mockResponse);

      const { rerender } = render(
        <MarkdownPreview markdownContent="# Valid" debounceMs={50} />,
      );

      await waitFor(
        () => {
          expect(screen.getByText("1 slide detected")).toBeInTheDocument();
        },
        { timeout: 300 },
      );

      // Now cause an error
      vi.mocked(pptxApi.parseMarkdown).mockRejectedValue(
        new Error("Parse failed"),
      );
      rerender(<MarkdownPreview markdownContent="# Invalid" debounceMs={50} />);

      await waitFor(
        () => {
          expect(
            screen.queryByText("1 slide detected"),
          ).not.toBeInTheDocument();
        },
        { timeout: 300 },
      );

      expect(screen.getByText(/Invalid Markdown/i)).toBeInTheDocument();
    });
  });

  describe("Loading State", () => {
    it("shows loading indicator during parse", async () => {
      let resolvePromise: (value: {
        presentation_title: string | null;
        slides: {
          layout_index: number;
          title: string;
          bullet_points: string[];
        }[];
        warnings: string[];
      }) => void;
      const promise = new Promise<{
        presentation_title: string | null;
        slides: {
          layout_index: number;
          title: string;
          bullet_points: string[];
        }[];
        warnings: string[];
      }>((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(pptxApi.parseMarkdown).mockReturnValue(promise);

      render(<MarkdownPreview markdownContent="# Test" debounceMs={50} />);

      await waitFor(
        () => {
          expect(screen.getByText(/updating/i)).toBeInTheDocument();
        },
        { timeout: 300 },
      );

      // Resolve to clean up
      resolvePromise!({
        presentation_title: "Test",
        slides: [],
        warnings: [],
      });
    });
  });
});
