import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('KANHA Academic Flow & Doubt Escalation E2E Tests', () => {

  test('Complete assignment, submission, review and doubt escalation cycle', async ({ page }) => {
    // 1. Faculty creates assignment
    await page.goto(BASE_URL);
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('What needs attention today?');

    const uniqueTitle = `Pattern Drafting ${Date.now()}`;
    await page.fill('input[placeholder="e.g. Surface ornamentation construction"]', uniqueTitle);
    await page.fill('textarea[placeholder="Detailed instructions for the student task..."]', 'Draft a basic sloper pattern.');
    await page.fill('input[type="datetime-local"]', '2026-08-30T18:00');
    await page.fill('input[placeholder="e.g. Textiles, Draping"]', 'Pattern Making');
    await page.fill('input[placeholder="e.g. Presentation (50%), Accuracy (50%)"]', 'Accuracy (100%)');

    await page.click('button:has-text("Publish to Student Portals")');
    await expect(page.locator('text=Assignment published successfully!')).toBeVisible();
    await page.click('button:has-text("Sign Out")');

    // 2. Student logs in and submits work
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('Good morning, Aarav');
    
    // Open assignment detail modal
    await page.click(`text=${uniqueTitle}`);
    await expect(page.locator('h3').filter({ hasText: uniqueTitle })).toBeVisible();

    // Fill and submit project
    await page.fill('textarea[placeholder="Describe the materials, fabrics, silhouettes, or design inspiration you used..."]', 'Muslin is draped on dress form.');
    await page.click('button:has-text("Submit Work")');
    await expect(page.locator('text=Work submitted successfully!')).toBeVisible();

    // Request KANHA AI / Faculty help (escalating with extension request)
    await page.selectOption('select', 'EXTENSION_REQUEST');
    await page.fill('input[placeholder="What are you stuck on?"]', 'I need more time to buy tools.');
    await page.click('button:has-text("Ask KANHA / Request Faculty Review")');
    await expect(page.locator('text=Help ticket created!')).toBeVisible();

    // Close modal
    await page.click('text=×');
    await page.click('button:has-text("Sign Out")');

    // 3. Faculty evaluates submission and checks escalations
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    // Locate the student submission under checklist
    await page.locator('text=Submission #').first().click();
    await page.fill('textarea[placeholder="Write constructive advice... (Include word \'revision\' to request updates)"]', 'Review details. Revision required.');
    await page.fill('input[placeholder="e.g. A, B+, Pass"]', 'B-');
    await page.click('button:has-text("Submit Evaluation")');
    await expect(page.locator('text=Evaluation saved!')).toBeVisible();

    // Verify escalated issue is visible on the escalation board
    await expect(page.locator('text=LEVEL 3').first()).toBeVisible();
    await expect(page.locator('text=I need more time to buy tools.').first()).toBeVisible();
  });

});
