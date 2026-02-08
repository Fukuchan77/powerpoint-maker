import { test, expect } from "@playwright/test";

test("complete user flow: upload, generate, and download", async ({ page }) => {
  // 1. Go to home page
  await page.goto("/");
  await expect(page).toHaveTitle(/frontend/);

  // 2. Upload a dummy PPTX template
  // Note: This relies on the backend being able to handle the file or us mocking the response if we were intercepting.
  // In a true E2E, we need the backend.

  // Create a dummy PPTX file buffer (empty or minimal valid structure if possible, but for this test we use a simple buffer)
  const buffer = Buffer.from("PK\x03\x04\x14\x00\x08\x00\x08\x00", "binary"); // Minimal fake zip signature

  // Upload the file directly to the input element
  // Mock the analysis response because we are using a dummy file that the backend validation would reject.
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

  // Mock generation response to return a dummy file
  await page.route("**/api/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType:
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      body: Buffer.from("PK\x03\x04\x14\x00\x08\x00\x08\x00", "binary"), // Minimal zip
    });
  });

  // Upload the file directly to the input element
  await page.setInputFiles('input[type="file"]', {
    name: "template.pptx",
    mimeType:
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    buffer: buffer,
  });

  // 3. Wait for analysis to complete and Topic Input to appear
  // We expect the topic input to appear after upload analysis.
  // Note: If the backend strictly checks for a valid PPTX structure, this might fail with the dummy buffer.
  // Ideally, we should check for a success indicator or the next step's visibility.
  await expect(page.getByPlaceholder("e.g., The Future of AI")).toBeVisible({
    timeout: 30000,
  });

  // Wait for network to be idle after upload
  await page.waitForLoadState("networkidle");

  // 4. Enter Topic
  const input = page.getByPlaceholder("e.g., The Future of AI");
  await input.fill("E2E Test Topic");

  // Small delay to ensure state is updated
  await page.waitForTimeout(500);

  // 5. Click Generate
  await page.getByRole("button", { name: "Generate Content" }).click();

  // 6. Verify Content Generation
  // Wait for the "Preview & Generate" header or similar to confirm generation worked.
  // Increased timeout to 90 seconds for slow research API calls
  await expect(page.getByText("3. Preview & Generate")).toBeVisible({
    timeout: 120000,
  });

  // Wait for network to be idle after generation
  await page.waitForLoadState("networkidle");

  // 7. Generate PPTX and Download
  // Click "Generate Presentation" button in Preview to create the file
  await page.getByRole("button", { name: "Generate Presentation" }).click();

  // Wait for "Download .pptx" link to appear (after mock generation)
  const downloadLink = page.getByRole("link", { name: "Download .pptx" });
  await expect(downloadLink).toBeVisible({ timeout: 30000 });

  // Initiate download
  const downloadPromise = page.waitForEvent("download");
  await downloadLink.click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBeDefined();
});
