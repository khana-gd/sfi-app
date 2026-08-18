import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('KANHA AI Companion & Tiered Doubt Escalation E2E Tests', () => {

  test('Tiered AI Doubt Flow: Student L1 -> L2 Escalation -> Faculty Review', async ({ page }) => {
    // 1. Student logs in and posts an AI doubt ticket
    await page.goto(BASE_URL);
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    const uniqueDoubt = `I need help clarifying illustration borders ${Date.now()}`;

    // Open assignment details modal where doubt ticket form is located
    await page.click('text=Mughal Costume Sketches');

    // Create a new doubt ticket
    await page.selectOption('select', { value: 'INSTRUCTION_HELP' });
    await page.fill('input[placeholder="What are you stuck on?"]', uniqueDoubt);
    await page.click('button:has-text("Ask KANHA / Request Faculty Review")');

    // Wait for API roundtrip to complete and register the ticket
    await expect(page.locator('text=Help ticket created!')).toBeVisible();
    await page.click('button:has-text("×")');

    // Open the created ticket from the AI Doubt Solutions dashboard card specifically
    await page.locator('.card-glass').filter({ hasText: 'AI Doubt Solutions' }).locator(`text=${uniqueDoubt}`).click();

    // Verify Level 1 AI Tutor response is visible in modal
    await expect(page.locator('text=KANHA AI Tutor')).toBeVisible();
    await expect(page.locator('text=SFI Technical Illustration Tips')).toBeVisible();

    // Student escalates the ticket to Level 2
    await page.click('button:has-text("Escalate to Faculty Review")');

    // Verify escalation level badge changes to Level 2
    await expect(page.locator('text=Level 2 Escalation')).toBeVisible();

    await page.click('button:has-text("×")'); // close modal
    await page.click('button:has-text("Sign Out")');

    // 2. Faculty logs in and approves/edits co-pilot draft reply
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    // Faculty clicks the escalated ticket in their dashboard list
    await page.locator(`text=${uniqueDoubt}`).click();

    // Verify AI Co-Pilot Suggested Draft textarea is present
    await expect(page.locator('.card-glass').filter({ hasText: 'Escalation Ticket' }).locator('textarea')).toHaveValue(/Draft response:/);

    // Faculty approves and sends the draft
    await page.click('button:has-text("Approve & Send Draft Reply")');

    // Verify the draft reply is posted to the thread
    await expect(page.locator('p:has-text("Draft response:")')).toBeVisible();
  });

});
