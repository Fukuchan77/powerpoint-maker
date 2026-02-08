/**
 * Unit tests for Layout Intelligence API client
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import { generateFromText } from "../layoutIntelligence";

vi.mock("axios");
const mockedAxios = vi.mocked(axios, true);

describe("generateFromText", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should call API with correct parameters", async () => {
    const mockResponse = {
      data: {
        slides: [
          {
            layout_index: 1,
            title: "Test Slide",
            bullet_points: ["Point 1", "Point 2"],
          },
        ],
        warnings: [],
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    const text = "Test content for slide generation";
    const templateId = "test-template-123";

    const result = await generateFromText(text, templateId);

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/layout-intelligence",
      {
        text,
        template_id: templateId,
      },
      {
        timeout: 65000,
      },
    );

    expect(result).toEqual(mockResponse.data);
  });

  it("should work without template_id", async () => {
    const mockResponse = {
      data: {
        slides: [
          {
            layout_index: 0,
            title: "Default Template Slide",
            bullet_points: ["Content"],
          },
        ],
        warnings: [],
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    const text = "Simple text input";
    const result = await generateFromText(text);

    expect(mockedAxios.post).toHaveBeenCalledWith(
      "/api/layout-intelligence",
      {
        text,
        template_id: undefined,
      },
      {
        timeout: 65000,
      },
    );

    expect(result).toEqual(mockResponse.data);
  });

  it("should have 65 second timeout configured", async () => {
    const mockResponse = {
      data: {
        slides: [],
        warnings: [],
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    await generateFromText("test");

    const callConfig = mockedAxios.post.mock.calls[0][2];
    expect(callConfig?.timeout).toBe(65000);
  });

  it("should handle API errors", async () => {
    const errorMessage = "Layout intelligence processing failed";
    mockedAxios.post.mockRejectedValue(new Error(errorMessage));

    await expect(generateFromText("test")).rejects.toThrow(errorMessage);
  });

  it("should handle timeout errors", async () => {
    const timeoutError = new Error("timeout of 65000ms exceeded");
    mockedAxios.post.mockRejectedValue(timeoutError);

    await expect(generateFromText("test")).rejects.toThrow("timeout");
  });

  it("should return warnings from API", async () => {
    const mockResponse = {
      data: {
        slides: [
          {
            layout_index: 1,
            title: "Test",
            bullet_points: [],
          },
        ],
        warnings: [
          "Layout 4 (Two-Column) unavailable, used Title+Bullets instead",
        ],
      },
    };

    mockedAxios.post.mockResolvedValue(mockResponse);

    const result = await generateFromText("test");

    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]).toContain("Two-Column");
  });
});

// Made with Bob
