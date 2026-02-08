import { expect, test } from "@playwright/test";

test.describe("PPTX Enhancement - Markdown Parsing", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173");
    // Wait for page to load
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");
    // Click "Use Default Template" to make ContentInput visible
    await page.getByRole("button", { name: /use default template/i }).click();
    // Wait for ContentInput to appear
    await expect(page.getByText(/2. Choose Content Source/i)).toBeVisible();
  });

  test("should parse valid Markdown and generate slides", async ({ page }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Enter Markdown content
    const markdownContent = `# My Presentation

## Introduction
- Welcome to the presentation
- Overview of topics

## Main Content
- Key point 1
- Key point 2
- Key point 3

## Conclusion
- Summary
- Thank you`;

    await page.getByPlaceholder(/# Presentation Title/i).fill(markdownContent);

    // Wait for live preview to update (debounced at 500ms + API call time)
    await expect(page.getByText("3 slides detected")).toBeVisible({
      timeout: 5000,
    });

    // Verify preview shows correct slides
    await expect(page.getByText("Slide 1: Introduction")).toBeVisible();
    await expect(page.getByText("Slide 2: Main Content")).toBeVisible();
    await expect(page.getByText("Slide 3: Conclusion")).toBeVisible();

    // Click generate button
    await page.getByRole("button", { name: /generate from markdown/i }).click();

    // Wait for slides to be generated (Preview component to appear)
    await expect(page.getByText(/3. Preview & Generate/i)).toBeVisible({
      timeout: 5000,
    });

    // Verify slide count
    await expect(page.getByText(/3 slides/i)).toBeVisible();
  });

  test("should display syntax error with line and column information", async ({
    page,
  }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Enter invalid Markdown (no slides)
    await page.getByPlaceholder(/# Presentation Title/i).fill("# Just a title");

    // Click generate button
    await page.getByRole("button", { name: /generate from markdown/i }).click();

    // Wait for error to appear
    await expect(page.getByText("Markdown Syntax Error")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/No slides found/i)).toBeVisible();
    await expect(page.getByText(/Location: Line 1, Column 1/i)).toBeVisible();
  });

  test("should show validation warnings in preview", async ({ page }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Enter Markdown with validation issues
    const longTitle = "A".repeat(101);
    const markdownContent = `# ${longTitle}

## Slide 1
![image](ftp://example.com/image.pdf)
- Content`;

    await page.getByPlaceholder(/# Presentation Title/i).fill(markdownContent);

    // Wait for preview to update and show warnings (debounced)
    await expect(page.getByText(/exceeds 100 characters/i)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/Invalid URL protocol/i)).toBeVisible();
  });

  test("should clear errors when user starts typing", async ({ page }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Enter invalid Markdown
    await page.getByPlaceholder(/# Presentation Title/i).fill("# Just a title");
    await page.getByRole("button", { name: /generate from markdown/i }).click();

    // Wait for error
    await expect(page.getByText("Markdown Syntax Error")).toBeVisible({
      timeout: 5000,
    });

    // Start typing to clear error
    await page
      .getByPlaceholder(/# Presentation Title/i)
      .fill("# New content\n\n## Slide 1");

    // Error should be cleared
    await expect(page.getByText("Markdown Syntax Error")).not.toBeVisible();
  });
});

test.describe("PPTX Enhancement - Content Extraction", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173");
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");
  });

  test("should switch to content extraction mode", async ({ page }) => {
    // Template mode should show upload and mode switch options

    // Click on template uploader area
    const uploaderSection = page.locator("text=1. Upload PowerPoint Template");
    await expect(uploaderSection).toBeVisible();

    // Switch to content mode
    await page.getByRole("radio", { name: /extract content/i }).click();

    // Verify mode switched
    await expect(
      page.getByRole("radio", { name: /extract content/i }),
    ).toBeChecked();
  });

  test("should show default template button in template mode", async ({
    page,
  }) => {
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");

    // Template mode should be default
    await expect(
      page.getByRole("button", { name: /use default template/i }),
    ).toBeVisible();
  });
});

test.describe("PPTX Enhancement - Mode Switching", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173");
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");
    // Click "Use Default Template" to make ContentInput visible
    await page.getByRole("button", { name: /use default template/i }).click();
    // Wait for ContentInput to appear
    await expect(page.getByText(/2. Choose Content Source/i)).toBeVisible();
  });

  test("should switch between content input modes", async ({ page }) => {
    // Start with web search (default)
    await expect(
      page.getByRole("radio", { name: /web search/i }),
    ).toBeChecked();

    // Switch to Markdown
    await page.getByRole("radio", { name: /markdown input/i }).click();
    await expect(page.getByPlaceholder(/# Presentation Title/i)).toBeVisible();

    // Switch back to web search
    await page.getByRole("radio", { name: /web search/i }).click();
    await expect(
      page.getByPlaceholder(/e.g., The Future of AI/i),
    ).toBeVisible();
  });

  test("should preserve content when switching modes", async ({ page }) => {
    // Enter Markdown content

    // Enter Markdown content
    await page.getByRole("radio", { name: /markdown input/i }).click();
    const markdownContent = "# Test\n\n## Slide 1\n- Content";
    await page.getByPlaceholder(/# Presentation Title/i).fill(markdownContent);

    // Switch to web search
    await page.getByRole("radio", { name: /web search/i }).click();

    // Switch back to Markdown
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Content should still be there
    await expect(page.getByPlaceholder(/# Presentation Title/i)).toHaveValue(
      markdownContent,
    );
  });
});

test.describe("PPTX Enhancement - Live Preview", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173");
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");
    // Click "Use Default Template" to make ContentInput visible
    await page.getByRole("button", { name: /use default template/i }).click();
    // Wait for ContentInput to appear
    await expect(page.getByText(/2. Choose Content Source/i)).toBeVisible();
  });

  test("should show live preview as user types", async ({
    page,
    browserName,
  }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Initially should show placeholder
    await expect(page.getByText(/start typing markdown/i)).toBeVisible();

    // Start typing
    await page.getByPlaceholder(/# Presentation Title/i).fill("# Test");

    // Webkit-specific timeout adjustment
    const previewTimeout = browserName === "webkit" ? 10000 : 5000;

    // Preview should update (debounced, wait for API response)
    await expect(page.getByText(/no slides detected/i)).toBeVisible({
      timeout: previewTimeout,
    });

    // Add a slide
    await page
      .getByPlaceholder(/# Presentation Title/i)
      .fill("# Test\n\n## Slide 1\n- Point 1");

    // Wait for debounce and network to settle before checking preview
    await page.waitForTimeout(600);
    await page.waitForLoadState("networkidle", { timeout: 10000 });

    // Preview should show the slide (debounced + API call)
    await expect(page.getByText("1 slide detected")).toBeVisible({
      timeout: previewTimeout,
    });
    await expect(page.getByText("Slide 1: Slide 1")).toBeVisible();
    await expect(page.getByText("Point 1")).toBeVisible();
  });

  test("should debounce preview updates", async ({ page, browserName }) => {
    // Select Markdown input mode
    await page.getByRole("radio", { name: /markdown input/i }).click();

    // Type quickly
    await page
      .getByPlaceholder(/# Presentation Title/i)
      .type("# Test\n\n## Slide", { delay: 50 });

    // Should show updating indicator
    await expect(page.getByText(/updating/i)).toBeVisible({ timeout: 600 });

    // Wait for debounce to complete and network to settle
    await page.waitForTimeout(800);
    await page.waitForLoadState("networkidle", { timeout: 10000 });

    // Webkit-specific timeout adjustment
    const previewTimeout = browserName === "webkit" ? 10000 : 5000;

    // Preview should be updated
    await expect(page.getByText(/1 slide detected/i)).toBeVisible({
      timeout: previewTimeout,
    });
  });
});
