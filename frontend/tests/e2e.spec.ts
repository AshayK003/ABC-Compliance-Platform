import { test, expect } from '@playwright/test';

test.describe('ABC Compliance Platform', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/');
  });

  test('login page loads', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('ABC Digital Compliance');
    await expect(page.locator('input[type="tel"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('navigation to protected routes redirects to login', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    await expect(page).toHaveURL(/.*login/);
  });
});