import { test, expect } from '@playwright/test';

test.describe('KANHA Phase 7 Portfolio System E2E Tests', () => {

  test('Complete Student Portfolio lifecycle: Upload, Filter, PDF compilation, Delete', async ({ page }) => {
    // 1. Student logs in
    await page.goto('http://localhost:5173/');
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    // 2. Open Portfolio tab
    await page.click('text=Portfolio');
    await expect(page.locator('h1')).toContainText('Fashion Design Portfolio');

    // 3. Fill and submit Add Portfolio Work form
    await page.fill('input[placeholder="e.g. Traditional Zardozi Lehenga"]', 'E2E Bridal Silk Gown');
    await page.selectOption('select', { value: 'EMBROIDERY' });
    await page.click('button:has-text("Use Lehenga")'); // Auto-populates File URL
    await page.fill('textarea[placeholder="Detail materials, embroidery stitches, silhouette inspiration..."]', 'Unique metallic threads work');
    await page.click('button:has-text("Add to Showcase")');

    // Verify card is added to showcase
    await expect(page.locator('h4:has-text("E2E Bridal Silk Gown")')).toBeVisible();

    // 4. Test Category Filter Chips
    await page.click('button:has-text("EMBROIDERY")');
    await expect(page.locator('h4:has-text("E2E Bridal Silk Gown")')).toBeVisible();

    await page.click('button:has-text("ILLUSTRATION")');
    await expect(page.locator('h4:has-text("E2E Bridal Silk Gown")')).not.toBeVisible();

    // Reset filter
    await page.click('button:has-text("ALL")');
    await expect(page.locator('h4:has-text("E2E Bridal Silk Gown")')).toBeVisible();

    // 5. Test PDF Compilation Export (opens new print-ready window)
    const [popup] = await Promise.all([
      page.waitForEvent('popup'),
      page.click('button:has-text("Compile Portfolio PDF")')
    ]);
    await popup.waitForLoadState();
    await expect(popup.locator('body')).toContainText('Fashion Portfolio');
    await expect(popup.locator('body')).toContainText('E2E Bridal Silk Gown');
    await popup.close();

    // 6. Delete item and verify removal
    await page.click('button:has-text("Delete Item")');
    await expect(page.locator('h4:has-text("E2E Bridal Silk Gown")')).not.toBeVisible();
  });

});
