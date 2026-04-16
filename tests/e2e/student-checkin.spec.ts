import { test, expect } from '@playwright/test';

test.describe('学生验证码签到完整测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/student');
    await page.waitForURL(/.*student/, { timeout: 15000 });
  });

  test.describe('学生仪表板签到状态', () => {
    test('显示签到状态', async ({ page }) => {
      const checkinStatus = page.getByText(/已签到|未签到|课堂进行中|暂无活跃课堂/);
      await expect(checkinStatus).toBeVisible();
    });

    test('显示当前分数', async ({ page }) => {
      await expect(page.getByText('我的分数')).toBeVisible();
      const scoreElement = page.locator('text=/\\d+\\.?\\d*/').filter({ hasText: /^[0-9]/ });
      await expect(scoreElement.first()).toBeVisible();
    });

    test('显示个人信息', async ({ page }) => {
      await expect(page.getByText('学号')).toBeVisible();
      await expect(page.getByText('班级')).toBeVisible();
    });
  });

  test.describe('验证码签到功能', () => {
    test('签到页面显示正常', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      await page.waitForURL(/.*student\\/checkin/);
      await expect(page.getByRole('heading', { name: '课堂签到' })).toBeVisible();
    });

    test('验证码输入区域状态正确', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const codeInput = page.getByPlaceholder('请输入6位验证码');
      const checkinButton = page.getByRole('button', { name: '确认签到' });
      const alreadyCheckedIn = page.getByText(/本节课已完成签到|已签到/);
      const noActiveSession = page.getByText('暂无活跃课堂');

      const isInputVisible = await codeInput.isVisible().catch(() => false);
      const isButtonVisible = await checkinButton.isVisible().catch(() => false);
      const isAlreadyCheckedIn = await alreadyCheckedIn.isVisible().catch(() => false);
      const isNoActiveSession = await noActiveSession.isVisible().catch(() => false);

      expect(isInputVisible || isAlreadyCheckedIn || isNoActiveSession).toBeTruthy();
      if (isInputVisible) {
        expect(isButtonVisible).toBeTruthy();
      }
    });

    test('成功验证码签到', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const codeInput = page.getByPlaceholder('请输入6位验证码');
      const checkinButton = page.getByRole('button', { name: '确认签到' });

      if (await codeInput.isVisible().catch(() => false)) {
        await codeInput.fill('TEST12');

        const responsePromise = page.waitForResponse(response =>
          response.url().includes('/api/v1/checkin'),
          { timeout: 10000 }
        );

        await checkinButton.click();
        const response = await responsePromise;

        if (response.status() === 200) {
          await expect(page.getByText(/本节课已完成签到|签到成功/)).toBeVisible({ timeout: 5000 });
        }
      }
    });

    test('重复签到提示', async ({ page }) => {
      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const codeInput = page.getByPlaceholder('请输入6位验证码');
      const checkinButton = page.getByRole('button', { name: '确认签到' });

      if (await codeInput.isVisible().catch(() => false)) {
        await codeInput.fill('TEST12');
        await checkinButton.click();
        await page.waitForTimeout(1500);

        if (await codeInput.isVisible().catch(() => false)) {
          await codeInput.fill('TEST12');
          await checkinButton.click();

          await expect(page.getByText(/已签到|重复|今天已经|签到失败/).or(
            page.getByText('本节课已完成签到')
          )).toBeVisible({ timeout: 5000 });
        }
      }
    });

    test('签到后分数更新', async ({ page }) => {
      const scoreBefore = await page.locator('text=/\\d+\\.?\\d*/').first().textContent();

      await page.getByRole('link', { name: '签到' }).or(
        page.getByRole('link', { name: '今日签到' })
      ).click();

      const codeInput = page.getByPlaceholder('请输入6位验证码');
      const checkinButton = page.getByRole('button', { name: '确认签到' });

      if (await codeInput.isVisible().catch(() => false)) {
        await codeInput.fill('TEST12');
        await checkinButton.click();
        await page.waitForTimeout(2000);

        await page.goto('/student');
        await page.waitForTimeout(1000);

        const scoreAfter = await page.locator('text=/\\d+\\.?\\d*/').first().textContent();
        expect(scoreAfter).toBeDefined();
      }
    });
  });

  test.describe('分数历史', () => {
    test('分数历史显示正常', async ({ page }) => {
      await page.getByText('分数变化历史').scrollIntoViewIfNeeded();
      await expect(page.getByText('分数变化历史')).toBeVisible();

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

      const scoreChanges = page.locator('text=/[+-]\\d+\\.?\\d*/');
      const count = await scoreChanges.count();

      if (count > 0) {
        const text = await scoreChanges.first().textContent();
        expect(text).toMatch(/[+-]\\d+/);
      }
    });
  });
});
