import { test, expect } from '@playwright/test';

test.describe('管理员班级管理测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问班级管理页面
    await page.goto('/admin/classes');
    await page.waitForURL(/.*admin\/classes/, { timeout: 15000 });
  });

  test.describe('班级列表', () => {
    test('班级管理页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '班级管理' })).toBeVisible();
      await expect(page.getByText(/管理班级信息/)).toBeVisible();
    });

    test('搜索框显示正常', async ({ page }) => {
      await expect(page.getByPlaceholder('搜索班级...')).toBeVisible();
    });

    test('班级数据加载显示', async ({ page }) => {
      await page.waitForTimeout(1000);
      const hasCards = await page.locator('text=/名学生/').first().isVisible().catch(() => false);
      const hasEmptyState = await page.getByText('暂无班级数据').isVisible().catch(() => false);
      expect(hasCards || hasEmptyState).toBeTruthy();
    });
  });
});
