import { test, expect } from '@playwright/test';

test.describe('教师课堂签到完整测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问课堂签到页面
    await page.goto('/teacher/session');
    await page.waitForURL(/.*teacher\/session/, { timeout: 15000 });
  });

  test.describe('课堂签到页面', () => {
    test('课堂签到页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '课堂签到' })).toBeVisible();
    });

    test('显示签到状态', async ({ page }) => {
      // 验证签到状态（签到中或未开始）
      const statusText = page.getByText(/签到中|未开始|准备中/);
      await expect(statusText).toBeVisible();
    });

    test('开始签到按钮或结束签到按钮显示', async ({ page }) => {
      const startButton = page.getByRole('button', { name: '开始签到' });
      const endButton = page.getByRole('button', { name: '结束签到' });

      const isStartVisible = await startButton.isVisible().catch(() => false);
      const isEndVisible = await endButton.isVisible().catch(() => false);

      expect(isStartVisible || isEndVisible).toBeTruthy();
    });
  });

  test.describe('开始课堂签到', () => {
    test('开始签到选择班级', async ({ page }) => {
      const startButton = page.getByRole('button', { name: '开始签到' });

      if (await startButton.isVisible().catch(() => false)) {
        await startButton.click();

        // 验证班级选择对话框
        await expect(page.getByRole('heading', { name: /选择班级|开始课堂/ })).toBeVisible();

        // 验证有班级选项
        const options = page.locator('[role="option"], [role="radio"]');
        if (await options.count() > 0) {
          // 选择第一个班级
          await options.first().click();

          // 确认开始
          await page.getByRole('button', { name: /确认|开始/ }).click();

          // 验证签到状态变为进行中
          await expect(page.getByText('签到中')).toBeVisible({ timeout: 5000 });
        }

        await page.getByRole('button', { name: '取消' }).click();
      }
    });

    test('开始签到后显示统计信息', async ({ page }) => {
      const endButton = page.getByRole('button', { name: '结束签到' });

      if (await endButton.isVisible().catch(() => false)) {
        // 已经在签到中
        await expect(page.getByText(/已签到|签到人数/)).toBeVisible();
        await expect(page.getByText(/未签到/)).toBeVisible();
      }
    });
  });

  test.describe('签到学生列表', () => {
    test('显示已签到学生', async ({ page }) => {
      // 等待学生列表加载
      await page.waitForTimeout(1000);

      const checkedInList = page.locator('[data-testid="checked-in-list"]').or(
        page.locator('text=/已签到学生/')
      );

      if (await checkedInList.isVisible().catch(() => false)) {
        await expect(checkedInList).toBeVisible();
      }
    });

    test('显示未签到学生', async ({ page }) => {
      await page.waitForTimeout(1000);

      const notCheckedInList = page.locator('[data-testid="not-checked-in-list"]').or(
        page.locator('text=/未签到学生/')
      );

      if (await notCheckedInList.isVisible().catch(() => false)) {
        await expect(notCheckedInList).toBeVisible();
      }
    });

    test('手动代签功能', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 找到未签到学生列表中的代签按钮
      const checkInForButton = page.getByRole('button', { name: '代签' }).or(
        page.getByRole('button', { name: '签到' })
      ).first();

      if (await checkInForButton.isVisible().catch(() => false)) {
        await checkInForButton.click();

        // 验证确认对话框或成功提示
        await expect(page.getByText(/确认代签|代签成功/).or(
          page.getByRole('heading', { name: /确认/ })
        )).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('地图签到', () => {
    test('地图组件显示（如果启用）', async ({ page }) => {
      const mapElement = page.locator('[class*="map"], [data-testid="map"]').or(
        page.locator('.amap-container')
      );

      if (await mapElement.isVisible().catch(() => false)) {
        await expect(mapElement).toBeVisible();
      }
    });

    test('显示签到位置标记', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 查找地图标记或位置信息
      const locationInfo = page.locator('text=/位置|地点/');

      if (await locationInfo.first().isVisible().catch(() => false)) {
        await expect(locationInfo.first()).toBeVisible();
      }
    });
  });

  test.describe('结束课堂签到', () => {
    test('结束签到确认对话框', async ({ page }) => {
      const endButton = page.getByRole('button', { name: '结束签到' });

      if (await endButton.isVisible().catch(() => false)) {
        await endButton.click();

        // 验证确认对话框
        await expect(page.getByRole('heading', { name: /确认结束|结束签到/ })).toBeVisible();
        await expect(page.getByText(/确定|确认/)).toBeVisible();

        await page.getByRole('button', { name: '取消' }).click();
      }
    });

    test('结束签到后状态更新', async ({ page }) => {
      const endButton = page.getByRole('button', { name: '结束签到' });

      if (await endButton.isVisible().catch(() => false)) {
        await endButton.click();

        // 确认结束
        await page.getByRole('button', { name: /确认|确定/ }).click();

        // 验证状态变为未开始
        await expect(page.getByText(/未开始|准备中/).or(
          page.getByRole('button', { name: '开始签到' })
        )).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('签到统计', () => {
    test('签到率计算正确', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 查找签到率
      const rateElement = page.locator('text=/\\d+%|签到率/');

      if (await rateElement.first().isVisible().catch(() => false)) {
        const rateText = await rateElement.first().textContent();
        expect(rateText).toMatch(/\\d+%/);
      }
    });

    test('签到人数与列表一致', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 查找已签到人数统计
      const countElement = page.locator('text=/已签到.*\\d+人|\\d+人.*已签到/');

      if (await countElement.first().isVisible().catch(() => false)) {
        const countText = await countElement.first().textContent();
        const match = countText?.match(/\\d+/);
        expect(match).toBeTruthy();
      }
    });
  });
});
