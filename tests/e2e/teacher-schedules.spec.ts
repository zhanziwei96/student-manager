import { test, expect } from '@playwright/test';

test.describe('教师课表查看测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问教师课表页面
    await page.goto('/teacher/schedules');
    await page.waitForURL(/.*teacher\/schedules/, { timeout: 15000 });
  });

  test.describe('课表页面', () => {
    test('课表页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: /我的课表|本周课表/ })).toBeVisible();
    });

    test('课表按星期显示', async ({ page }) => {
      const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
      for (const day of weekdays) {
        await expect(page.getByText(day).first()).toBeVisible();
      }
    });

    test('课程卡片显示信息', async ({ page }) => {
      await page.waitForTimeout(1000);

      const courseCards = page.locator('[class*="course"], [class*="schedule"]').filter({
        has: page.locator('text=/\\d{2}:\\d{2}/')
      });

      if (await courseCards.first().isVisible().catch(() => false)) {
        await expect(courseCards.first().locator('text=/[\u4e00-\u9fa5]+/')).toBeVisible();
      }
    });
  });

  test.describe('课表筛选', () => {
    test('显示今日课表', async ({ page }) => {
      await expect(page.getByText(/今日|今天/).or(
        page.getByRole('button', { name: /今天/ })
      )).toBeVisible();
    });
  });
});
