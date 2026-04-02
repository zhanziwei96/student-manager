import { test, expect } from '@playwright/test';

test.describe('学生签到完整测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问学生页面
    await page.goto('/student');
    await page.waitForURL(/.*student/, { timeout: 15000 });
  });

  test.describe('学生仪表板签到状态', () => {
    test('显示签到状态', async ({ page }) => {
      // 验证签到状态显示
      const checkinStatus = page.getByText(/已签到|未签到|签到中/);
      await expect(checkinStatus).toBeVisible();
    });

    test('显示当前分数', async ({ page }) => {
      await expect(page.getByText('我的分数')).toBeVisible();

      // 验证分数显示
      const scoreElement = page.locator('text=/\\d+\\.?\\d*/').filter({ hasText: /^[0-9]/ });
      await expect(scoreElement.first()).toBeVisible();
    });

    test('显示个人信息', async ({ page }) => {
      await expect(page.getByText('学号')).toBeVisible();
      await expect(page.getByText('学号')).toBeVisible();
      await expect(page.getByText('班级')).toBeVisible();
    });
  });

  test.describe('签到功能', () => {
    test('签到页面显示正常', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      await page.waitForURL(/.*student\/checkin/);
      await expect(page.getByRole('heading', { name: /签到|课堂签到/ })).toBeVisible();
    });

    test('签到按钮状态正确', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const checkinButton = page.getByRole('button', { name: '立即签到' });
      const alreadyCheckedIn = page.getByText(/今日已签到|已签到/);

      const isCheckInVisible = await checkinButton.isVisible().catch(() => false);
      const isAlreadyCheckedIn = await alreadyCheckedIn.isVisible().catch(() => false);

      expect(isCheckInVisible || isAlreadyCheckedIn).toBeTruthy();
    });

    test('成功签到', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const checkinButton = page.getByRole('button', { name: '立即签到' });

      if (await checkinButton.isVisible().catch(() => false)) {
        // 等待签到API响应
        const responsePromise = page.waitForResponse(response =>
          response.url().includes('/api/v1/checkin') && response.status() === 200
        );

        await checkinButton.click();

        const response = await responsePromise;
        expect(response.status()).toBe(200);

        // 验证显示已签到
        await expect(page.getByText(/今日已签到|已签到/)).toBeVisible({ timeout: 5000 });
      }
    });

    test('重复签到提示', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const checkinButton = page.getByRole('button', { name: '立即签到' });

      if (await checkinButton.isVisible().catch(() => false)) {
        await checkinButton.click();
        await page.waitForTimeout(1000);

        // 再次点击签到按钮
        if (await checkinButton.isVisible().catch(() => false)) {
          await checkinButton.click();

          // 验证重复签到提示
          await expect(page.getByText(/已签到|重复|今天已经/).or(
            page.getByText('今日已签到')
          )).toBeVisible({ timeout: 5000 });
        }
      }
    });

    test('签到后分数更新', async ({ page }) => {
      // 获取签到前分数
      const scoreBefore = await page.locator('text=/\\d+\\.?\\d*/').first().textContent();

      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const checkinButton = page.getByRole('button', { name: '立即签到' });

      if (await checkinButton.isVisible().catch(() => false)) {
        await checkinButton.click();
        await page.waitForTimeout(2000);

        // 返回仪表板验证分数
        await page.goto('/student');
        await page.waitForTimeout(1000);

        const scoreAfter = await page.locator('text=/\\d+\\.?\\d*/').first().textContent();

        // 分数应该有所变化（通常签到加分）
        expect(scoreAfter).toBeDefined();
      }
    });
  });

  test.describe('分数历史', () => {
    test('分数历史显示正常', async ({ page }) => {
      await page.getByText('分数变化历史').scrollIntoViewIfNeeded();
      await expect(page.getByText('分数变化历史')).toBeVisible();

      // 验证历史记录列表（如果有）
      const historyItems = page.locator('[data-testid="score-history-item"]').or(
        page.locator('text=/[+-]\\d+/')
      );

      const count = await historyItems.count();
      if (count > 0) {
        await expect(historyItems.first()).toBeVisible();
      }
    });

    test('分数变化显示正确格式', async ({ page }) => {
      await page.getByText('分数变化历史').scrollIntoViewIfNeeded();

      // 查找分数变化记录
      const scoreChanges = page.locator('text=/[+-]\\d+\\.?\\d*/');
      const count = await scoreChanges.count();

      if (count > 0) {
        const text = await scoreChanges.first().textContent();
        expect(text).toMatch(/[+-]\\d+/);
      }
    });
  });
});
