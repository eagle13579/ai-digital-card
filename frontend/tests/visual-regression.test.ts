import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  const BASE_URL = 'http://localhost:6006';

  test('CardPreview default story matches snapshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/?path=/story/components-cardpreview--default`);
    await page.waitForSelector('[data-testid="card-preview"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="card-preview"]')).toHaveScreenshot('cardpreview-default.png');
  });

  test('CardPreview full profile story matches snapshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/?path=/story/components-cardpreview--full-profile`);
    await page.waitForSelector('[data-testid="card-preview"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="card-preview"]')).toHaveScreenshot('cardpreview-full.png');
  });

  test('SearchBar default story matches snapshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/?path=/story/components-searchbar--default`);
    await page.waitForSelector('[data-testid="search-bar"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="search-bar"]')).toHaveScreenshot('searchbar-default.png');
  });

  test('SearchBar with text story matches snapshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/?path=/story/components-searchbar--with-text`);
    await page.waitForSelector('[data-testid="search-bar"]');
    await page.waitForTimeout(500);
    await expect(page.locator('[data-testid="search-bar"]')).toHaveScreenshot('searchbar-withtext.png');
  });
});
