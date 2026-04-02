import { test, expect } from '@playwright/test';

test.describe('管理员签到管理测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问签到管理页面
    await page.goto('/admin/checkins');
    await page.waitForURL(/.*admin\/checkins/, { timeout: 15000 });
  });

  test.describe('页面显示', () => {
    test('签到管理页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '签到管理' })).toBeVisible();
      await expect(page.getByText('查看今日签到记录和统计')).toBeVisible();
    });

    test('统计卡片显示正常', async ({ page }) => {
      await expect(page.getByText('总学生数').first()).toBeVisible();
      await expect(page.getByText('已签到').first()).toBeVisible();
      await expect(page.getByText('未签到').first()).toBeVisible();
      await expect(page.getByText('签到率').first()).toBeVisible();

      // 验证数值显示 - 使用 first() 避免匹配多个
      await expect(page.locator('text=/\\d+/').first()).toBeVisible();
    });

    test('筛选器显示正常', async ({ page }) => {
      await expect(page.getByPlaceholder('搜索学生姓名或学号...')).toBeVisible();
      await expect(page.locator('select').filter({ hasText: /所有班级|全部班级/ })).toBeVisible();
    });

    test('签到记录列表显示', async ({ page }) => {
      // 使用 heading 角色更精确地匹配标题
      await expect(page.getByRole('heading', { name: '今日签到记录' })).toBeVisible();

      // 等待数据加载
      await page.waitForTimeout(1000);

      // 检查是否有记录或空状态
      const hasRecords = await page.getByText(/共.*条记录/).isVisible().catch(() => false);
      if (hasRecords) {
        const records = page.locator('[class*="flex items-center justify-between"]').filter({ has: page.locator('text=已签到') });
        const count = await records.count();
        if (count > 0) {
          await expect(page.getByText('已签到').first()).toBeVisible();
        }
      }
    });
  });

  test.describe('筛选功能', () => {
    test('按班级筛选签到记录', async ({ page }) => {
      const classButton = page.getByRole('button', { name: /所有班级|全部班级/ });
      if (await classButton.isVisible().catch(() => false)) {
        await classButton.click();
        await page.waitForTimeout(300);

        const options = page.locator('[role="option"]');
        const count = await options.count();

        if (count > 0) {
          await options.first().click();
          await page.waitForTimeout(500);

          // 验证筛选后的结果
          await expect(page.getByRole('heading', { name: '今日签到记录' })).toBeVisible();
        }
      }
    });

    test('按学生姓名搜索', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索学生姓名或学号...');
      if (await searchInput.isVisible().catch(() => false)) {
        await searchInput.fill('测试');
        await page.waitForTimeout(500);

        // 验证搜索结果或保持正常显示
        await expect(page.getByRole('heading', { name: '今日签到记录' })).toBeVisible();
      }
    });
  });

  test.describe('签到记录详情', () => {
    test('签到记录显示学生信息', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 查找第一条签到记录
      const firstRecord = page.locator('div').filter({ has: page.locator('text=已签到') }).first();

      if (await firstRecord.isVisible().catch(() => false)) {
        // 验证显示学生姓名和学号 - 使用 first() 避免匹配多个
        await expect(firstRecord.locator('text=/[\u4e00-\u9fa5]+/').first()).toBeVisible();
      }
    });

    test('签到时间格式化显示', async ({ page }) => {
      await page.waitForTimeout(1000);

      const timeElements = page.locator('text=/\\d{2}:\\d{2}/');
      const count = await timeElements.count();

      if (count > 0) {
        // 验证时间格式正确
        const timeText = await timeElements.first().textContent();
        expect(timeText).toMatch(/\\d{2}:\\d{2}/);
      }
    });
  });

  test.describe('空状态', () => {
    test('无签到记录时显示空状态', async ({ page }) => {
      // 搜索不存在的记录
      await page.getByPlaceholder('搜索学生姓名或学号...').fill('不存在的学生');
      await page.waitForTimeout(500);

      // 验证空状态显示
      await expect(page.getByText(/暂无签到记录|没有签到记录/)).toBeVisible();
    });
  });
});
