import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('KANHA Phase 5 Fashion Research & Google Workspace Integration E2E Tests', () => {

  test('Search Grounded Fashion Query & Export Google Doc', async ({ page, context }) => {
    // 1. Student logs in
    await page.goto(BASE_URL);
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    // 2. Navigate to the Fashion Research Engine tab
    await page.click('text=Fashion Research');

    // Verify page headers
    await expect(page.locator('h1:has-text("Fashion Research Engine")')).toBeVisible();

    // 3. Perform a research search using a suggestion chip click
    await page.click('text=Mughal embroidery motifs');

    // Click search button
    await page.click('button:has-text("Search")');

    // Verify findings are displayed
    await expect(page.locator('text=Research Findings')).toBeVisible();
    await expect(page.locator('text=pietra dura')).toBeVisible();

    // Verify grounded citations are loaded
    await expect(page.locator('text=SOURCE [1]')).toBeVisible();
    await expect(page.locator('text=National Museum India')).toBeVisible();

    // 4. Test Google Docs Export (mock opens link in new tab)
    // We expect a new page to open when clicking the export button
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      page.click('button:has-text("Export to Google Docs")')
    ]);

    await newPage.waitForLoadState();
    
    // Verify the mock Google Doc page content in the new tab
    await expect(newPage.locator('h1')).toContainText('Mughal embroidery motifs');
    await expect(newPage.locator('text=SFI KANHA Google Workspace Export')).toBeVisible();
    await expect(newPage.locator('text=pietra dura')).toBeVisible();
  });
});
