/**
 * E2E tests for Layout Intelligence feature.
 *
 * Tests the complete flow from text input through layout intelligence
 * to PPTX generation in the browser.
 */

import { expect, test } from "@playwright/test";

test.describe("Layout Intelligence E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("AI PowerPoint Agent");
    // Click "Use Default Template" to make ContentInput visible
    await page.getByRole("button", { name: /use default template/i }).click();
    // Wait for ContentInput to appear
    await expect(page.getByText(/2. Choose Content Source/i)).toBeVisible();
  });

  // T082: Frontend E2E test for text input to PPTX flow
  test("complete text input to PPTX generation flow", async ({ page }) => {
    // Mock layout intelligence API
    await page.route("**/api/layout-intelligence", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          slides: [
            {
              layout_index: 0,
              title: "Introduction to AI",
              bullet_points: [
                "Artificial Intelligence is transforming industries worldwide",
              ],
              bullets: [
                {
                  text: "Artificial Intelligence is transforming industries worldwide",
                  level: 0,
                },
                { text: "Automation of repetitive tasks", level: 1 },
                { text: "Enhanced decision-making capabilities", level: 1 },
              ],
            },
            {
              layout_index: 1,
              title: "Machine Learning vs Deep Learning",
              bullet_points: [],
              bullets: [
                {
                  text: "ML uses algorithms to learn from data",
                  level: 0,
                },
                { text: "DL uses neural networks", level: 0 },
              ],
            },
            {
              layout_index: 1,
              title: "Future Outlook",
              bullet_points: [],
              bullets: [
                {
                  text: "The AI market is expected to grow significantly",
                  level: 0,
                },
              ],
            },
          ],
          warnings: [],
        }),
      });
    });

    // Step 1: Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Verify Text Input tab is active
    await expect(page.getByTestId("text-input-textarea")).toBeVisible();

    // Step 2: Enter text content
    const sampleText = `Introduction to AI

Artificial Intelligence is transforming industries worldwide. Key benefits include:
- Automation of repetitive tasks
- Enhanced decision-making capabilities
- Improved customer experiences

Machine Learning vs Deep Learning

Machine Learning uses algorithms to learn from data, while Deep Learning uses neural networks.
ML is better for structured data, DL excels at unstructured data like images.

Future Outlook

The AI market is expected to grow significantly in the coming years.`;

    await page.getByTestId("text-input-textarea").fill(sampleText);

    // Verify character counter updates
    const charCount = sampleText.length;
    await expect(page.getByText(`${charCount} / 10,000`)).toBeVisible();

    // Step 3: Click Generate Slides button
    await page.getByTestId("generate-from-text-btn").click();

    // Step 4: Wait for slides to be generated
    await expect(page.getByText(/3. Preview & Generate/i)).toBeVisible({
      timeout: 10000,
    });

    // Verify slides are displayed in preview
    await expect(page.getByText("Slide 1: Introduction to AI")).toBeVisible();
    await expect(
      page.getByText("Slide 2: Machine Learning vs Deep Learning"),
    ).toBeVisible();
    await expect(page.getByText("Slide 3: Future Outlook")).toBeVisible();
  });

  test("text input with character counter", async ({ page }) => {
    // Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Verify initial character count
    await expect(page.getByText("0 / 10,000")).toBeVisible();

    // Type some text
    const shortText = "Hello World";
    await page.getByTestId("text-input-textarea").fill(shortText);

    // Verify character count updates
    await expect(page.getByText(`${shortText.length} / 10,000`)).toBeVisible();
  });

  test("text input error handling - timeout", async ({ page }) => {
    // Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Enter text
    await page
      .getByTestId("text-input-textarea")
      .fill("Test content for timeout");

    // Mock a timeout by immediately aborting the route (P0-1 fix)
    await page.route("**/api/layout-intelligence", async (route) => {
      await route.abort("timedout");
    });

    // Click Generate
    await page.getByTestId("generate-from-text-btn").click();

    // Verify timeout error message - use specific locator to avoid ambiguity
    await expect(page.getByTestId("error-message")).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByTestId("error-message")).toContainText(
      /Request timed out|timeout|Failed to generate|network error/i,
    );
  });

  test("text input error handling - server error", async ({ page }) => {
    // Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Enter text
    await page
      .getByTestId("text-input-textarea")
      .fill("Test content for error");

    // Mock a server error
    await page.route("**/api/layout-intelligence", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    // Click Generate
    await page.getByTestId("generate-from-text-btn").click();

    // Verify error message
    await expect(page.getByText(/Failed to generate slides/)).toBeVisible({
      timeout: 10000,
    });
  });

  test("text input clears error on new input", async ({ page }) => {
    // Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Enter text
    await page.getByTestId("text-input-textarea").fill("Test content");

    // Mock an error
    await page.route("**/api/layout-intelligence", async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid input" }),
      });
    });

    // Click Generate to trigger error
    await page.getByTestId("generate-from-text-btn").click();
    await expect(page.getByText("Invalid input")).toBeVisible({
      timeout: 10000,
    });

    // Type new text - error should clear
    await page.getByTestId("text-input-textarea").fill("New test content");

    // Verify error is cleared
    await expect(page.getByText("Invalid input")).not.toBeVisible();
  });

  test("text input tab switching preserves content", async ({ page }) => {
    // Switch to Text Input tab
    await page.getByLabel("Text Input").click();

    // Enter text
    const testText = "This content should be preserved";
    await page.getByTestId("text-input-textarea").fill(testText);

    // Switch to another tab
    await page.getByLabel("Web Search").click();

    // Switch back to Text Input
    await page.getByLabel("Text Input").click();

    // Verify content is preserved
    await expect(page.getByTestId("text-input-textarea")).toHaveValue(testText);
  });
});
