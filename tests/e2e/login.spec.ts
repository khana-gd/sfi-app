import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('KANHA Role-Based Authentication E2E Tests', () => {

  test('Student login and dashboard redirection', async ({ page }) => {
    await page.goto(BASE_URL);

    // Enter Student credentials
    await page.fill('input[placeholder="name@kanha.local"]', 'student1@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    
    // Click submit
    await page.click('button[type="submit"]');

    // Verify redirected to student dashboard containing "Today's Studio"
    await expect(page.locator('h1')).toContainText('Good morning, Aarav');
    await expect(page.locator('text=Today\'s Studio')).toBeVisible();
    await expect(page.getByText('STUDENT', { exact: true })).toBeVisible();
  });

  test('Faculty login and dashboard redirection', async ({ page }) => {
    await page.goto(BASE_URL);

    // Enter Faculty credentials
    await page.fill('input[placeholder="name@kanha.local"]', 'faculty@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    
    // Click submit
    await page.click('button[type="submit"]');

    // Verify redirected to faculty dashboard containing "What needs attention today?"
    await expect(page.locator('h1')).toContainText('What needs attention today?');
    await expect(page.getByText('FACULTY', { exact: true })).toBeVisible();
  });

  test('Admin login and user directory list', async ({ page }) => {
    await page.goto(BASE_URL);

    // Enter Admin credentials
    await page.fill('input[placeholder="name@kanha.local"]', 'admin@kanha.local');
    await page.fill('input[placeholder="••••••••"]', 'KanhaDevPass2026!');
    
    // Click submit
    await page.click('button[type="submit"]');

    // Verify redirected to admin dashboard containing registry
    await expect(page.locator('h1')).toContainText('Institute Registry Control');
    await expect(page.getByText('ADMIN', { exact: true }).first()).toBeVisible();
    await expect(page.locator('text=Active User Directory')).toBeVisible();
  });

});
