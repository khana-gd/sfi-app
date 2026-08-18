import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('KANHA Real-Time Chat E2E Tests', () => {

  test('Student to Faculty message exchange', async ({ page }) => {
    // 1. Student logs in and sends a chat message
    await page.goto(BASE_URL);
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await expect(page.locator('h1')).toContainText('Good morning, Aarav');

    // Click KANHA Chat link in the sidebar
    await page.click('text="KANHA Chat"');
    await expect(page.locator('text=Real-time SFI Academic Exchange')).toBeVisible();

    // Verify contact is visible
    await expect(page.locator('text=Prof. Sarah Jenkins')).toBeVisible();

    // Send a message
    const uniqueMessage = `Hello Professor! Drafting check ${Date.now()}`;
    await page.fill('input[placeholder="Type a message..."]', uniqueMessage);
    await page.click('button:has-text("Send")');

    // Verify it is appended locally in speech bubbles
    await expect(page.locator(`text=${uniqueMessage}`)).toBeVisible();
    await page.click('button:has-text("Sign Out")');

    // 2. Faculty logs in and verifies receiving the message
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    await page.click('button[type="submit"]');

    await page.click('text="KANHA Chat"');
    await expect(page.locator('text=Real-time SFI Academic Exchange')).toBeVisible();

    // Faculty clicks Aarav Mehta to open the conversation
    await page.click('text=Aarav Mehta');

    // Verify the student's message is visible in the faculty chat feed
    await expect(page.locator(`text=${uniqueMessage}`)).toBeVisible();
  });

});
