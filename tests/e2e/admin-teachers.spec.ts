import { test, expect } from '@playwright/test';

test.describe('管理员教师管理完整测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问教师管理页面
    await page.goto('/admin/teachers');
    await page.waitForURL(/.*admin\/teachers/, { timeout: 15000 });
  });

  test.describe('教师列表', () => {
    test('教师管理页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '教师管理' })).toBeVisible();
      await expect(page.getByText('管理教师账号')).toBeVisible();
    });

    test('搜索框显示正常', async ({ page }) => {
      await expect(page.getByPlaceholder('搜索教师...')).toBeVisible();
    });
  });
});
