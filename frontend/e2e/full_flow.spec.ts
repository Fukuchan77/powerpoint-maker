import { expect, test } from "@playwright/test";

test("complete user flow: upload, generate, and download", async ({ page }) => {
  await test.step("Navigate to application", async () => {
    await page.goto("/");
    await expect(page).toHaveTitle(/frontend/);
  });

  await test.step("Upload and analyze template", async () => {
    // Create a dummy PPTX file buffer (minimal valid structure)
    const buffer = Buffer.from([
      0x50, 0x4b, 0x03, 0x04, 0x14, 0x00, 0x08, 0x00, 0x08, 0x00,
    ]); // Minimal fake zip signature (PK header)

    // Mock the analysis response
    await page.route("**/api/analyze-template", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          filename: "template.pptx",
          template_id: "dummy-template-id",
          masters: [
            {
              index: 0,
              name: "Master 0",
              layouts: [
                {
                  index: 0,
                  name: "Title Slide",
                  placeholders: [],
                },
                {
                  index: 1,
                  name: "Content Slide",
                  placeholders: [],
                },
              ],
            },
          ],
        }),
      });
    });

    // Upload the file
    await page.setInputFiles('input[type="file"]', {
      name: "template.pptx",
      mimeType:
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      buffer: buffer,
    });

    // Wait for analysis to complete and Topic Input to appear
    await expect(
      page.getByPlaceholder("e.g., The Future of AI in Healthcare"),
    ).toBeVisible({
      timeout: 10000,
    });
  });

  await test.step("Perform research", async () => {
    // Mock research API response
    await page.route("**/api/research**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            title: "E2E Test Slide 1",
            bullet_points: ["Test point 1", "Test point 2"],
            layout_index: 0,
          },
          {
            title: "E2E Test Slide 2",
            bullet_points: ["Test point 3", "Test point 4"],
            layout_index: 1,
          },
        ]),
      });
    });

    // Enter topic
    const input = page.getByPlaceholder("e.g., The Future of AI in Healthcare");
    await input.fill("E2E Test Topic");

    // Click Generate
    await page.getByRole("button", { name: "Generate Content" }).click();

    // Wait for content generation to complete (P0-3, P0-4 fix: removed networkidle and waitForTimeout)
    await expect(page.getByText("3. Preview & Generate")).toBeVisible({
      timeout: 10000,
    });
  });

  await test.step("Generate and download presentation", async () => {
    // Mock generation response
    await page.route("**/api/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType:
          "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        body: Buffer.from([
          0x50, 0x4b, 0x03, 0x04, 0x14, 0x00, 0x08, 0x00, 0x08, 0x00,
        ]), // Minimal zip (PK header)
      });
    });

    // Click "Generate Presentation" button
    await page.getByRole("button", { name: "Generate Presentation" }).click();

    // Wait for download link to appear
    const downloadLink = page.getByRole("link", { name: "Download .pptx" });
    await expect(downloadLink).toBeVisible({ timeout: 10000 });

    // Initiate download (P1-5 fix: reduced timeout from 120s to 10s)
    const downloadPromise = page.waitForEvent("download", { timeout: 10000 });
    await downloadLink.click();
    const download = await downloadPromise;

    // Verify download (P1-6 fix: added .pptx extension check)
    expect(download.suggestedFilename()).toBeDefined();
    expect(download.suggestedFilename()).toMatch(/\.pptx$/);
  });
});
