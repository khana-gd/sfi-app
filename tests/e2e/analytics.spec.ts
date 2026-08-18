import { test, expect } from '@playwright/test';

test.describe('KANHA Phase 8 Analytics Suite E2E Tests', () => {

  test('Student Progress Dashboard Widgets & Faculty Watchlist Warnings', async ({ page }) => {
    // 1. Student logs in to verify progress widgets
    await page.goto('http://localhost:5173/');
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    // Wait for student dashboard to load
    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    // Verify progress analytics cards are visible
    await expect(page.locator('text=Your Studio Progress & Analytics')).toBeVisible();
    await expect(page.locator('text=Attendance Rate')).toBeVisible();
    await expect(page.locator('text=Showcase Items')).toBeVisible();
    await expect(page.locator('text=Approved Submissions')).toBeVisible();

    // Log out
    await page.click('button:has-text("Sign Out")');

    // 2. Faculty logs in to publish overdue assignments and verify watchlist warning flags
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('What needs attention today?');

    // Publish first overdue assignment targeted to Batch 1
    await page.fill('input[placeholder="e.g. Surface ornamentation construction"]', 'E2E Overdue Assignment 1');
    await page.fill('textarea[placeholder="Detailed instructions for the student task..."]', 'Analyze styling templates');
    await page.fill('input[type="datetime-local"]', '2025-01-01T12:00');
    await page.click('button:has-text("Publish to Student Portals")');
    await expect(page.locator('text=Assignment published successfully')).toBeVisible();

    // Publish second overdue assignment targeted to Batch 1
    await page.fill('input[placeholder="e.g. Surface ornamentation construction"]', 'E2E Overdue Assignment 2');
    await page.fill('textarea[placeholder="Detailed instructions for the student task..."]', 'Review patterns');
    await page.fill('input[type="datetime-local"]', '2025-01-02T12:00');
    await page.click('button:has-text("Publish to Student Portals")');
    await expect(page.locator('text=Assignment published successfully')).toBeVisible();

    // Scroll to Student Watchlist Warning System card and verify Aarav Mehta is flagged
    await expect(page.locator('text=Student Watchlist Warning System')).toBeVisible();
    await expect(page.locator('strong:has-text("Aarav Mehta")')).toBeVisible();
    
    // Verify intervention reason text is displayed
    await expect(page.locator('text=Unfinished overdue work').first()).toBeVisible();

    // Handle alert popup when clicking Intervene button
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('Escalating academic intervention checklist for student Aarav Mehta');
      await dialog.accept();
    });
    await page.click('button:has-text("Intervene")');
  });

});
