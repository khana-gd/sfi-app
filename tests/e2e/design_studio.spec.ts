import { test, expect } from '@playwright/test';

test.describe('KANHA Phase 6 Design Studio E2E Tests', () => {

  test('Complete Design Studio lifecycle: Projects, Moodboards, AI Concept Gen, Sketch Analysis, Attribution', async ({ page }) => {
    // 1. Student logs in
    await page.goto('http://localhost:5173/');
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    // 2. Open Design Studio tab
    await page.click('text=Design Studio');
    await expect(page.locator('h1')).toContainText('Fashion AI Design Studio');

    // 3. Create a unique Design Project
    const uniqueProj = `Bridal Gown Project ${Date.now()}`;
    await page.fill('input[placeholder="New Project Name..."]', uniqueProj);
    await page.click('button:has-text("Create")');

    // Verify project card appears and is selected
    await expect(page.locator('.card-glass').filter({ hasText: 'Design Projects' })).toContainText(uniqueProj);

    // 4. Create a Moodboard
    await page.fill('input[placeholder="New Moodboard..."]', 'Embellishments Board');
    await page.click('button:has-text("Add")');

    // Verify moodboard header is selected
    await expect(page.locator('h3:has-text("Embellishments Board")')).toBeVisible();

    // 5. Generate Text-to-Design Concept
    await page.selectOption('select', { value: 'Lehenga' });
    await page.fill('input[placeholder="e.g. Velvet, Raw Silk, Organza"]', 'Raw Silk');
    await page.fill('input[placeholder="e.g. Navy Blue & Gold, Rose Pink"]', 'Crimson Red');
    await page.fill('input[placeholder="e.g. Zardozi, Chikankari stitches"]', 'Zardozi embroidery');
    await page.click('button:has-text("Generate AI Concept")');

    // Verify AI generated concept item is created and has "AI Generated Concept" watermark overlay
    await expect(page.locator('text=AI Generated: Lehenga | Raw Silk')).toBeVisible();
    await expect(page.locator('text=AI Generated Concept')).toBeVisible();

    // 6. Upload a pencil sketch file to vision analyzer
    await page.setInputFiles('input[type="file"]', {
      name: 'sketch.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.from('mock pencil sketch image contents')
    });
    await page.click('button:has-text("Analyze Sketch")');

    // Verify Vision Recommendations appear
    await expect(page.locator('strong:has-text("KANHA Recommendations:")')).toBeVisible();
    await expect(page.locator('text=Flared Kalidar Gown')).toBeVisible();
    await expect(page.locator('text=Uploaded Sketch: Flared Kalidar Gown')).toBeVisible();

    // 7. Add a third-party reference image with attribution
    await page.fill('input[placeholder="https://..."]', 'https://images.unsplash.com/photo-1595777457583-95e059d581b8');
    await page.fill('input[placeholder="e.g. Wikipedia page"]', 'Unsplash Dress reference');
    await page.fill('input[placeholder="https://attribution..."]', 'https://unsplash.com/photos/dress-reference');
    await page.fill('input[placeholder="e.g. Dome shape"]', 'Modern silhouette inspiration');
    await page.click('button:has-text("Add Item")');

    // Verify third-party item is listed with source attribution link
    await expect(page.locator('text=Modern silhouette inspiration')).toBeVisible();
    const linkLocator = page.locator('a:has-text("Unsplash Dress reference")');
    await expect(linkLocator).toBeVisible();
    await expect(linkLocator).toHaveAttribute('href', 'https://unsplash.com/photos/dress-reference');
  });

});
