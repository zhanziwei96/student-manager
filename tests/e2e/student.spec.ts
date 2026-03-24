import { test, expect } from '@playwright/test';

test.describe('学生功能测试', () => {
  async function loginAsStudent(page) {
    await page.goto('/login');
    await page.getByRole('button', { name: '学生' }).click();
    await page.getByPlaceholder('请输入用户名').fill('2513070102');
    await page.getByPlaceholder('请输入密码').fill('2513070102');
    await page.getByRole('button', { name: '登录' }).click();
    await page.waitForURL(/.*student/);
  }

  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test.describe('学生仪表板', () => {
    test('学生仪表板显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '学生仪表板' })).toBeVisible();
      
      // 验证个人信息卡片
      await expect(page.getByText('个人信息')).toBeVisible();
      await expect(page.getByText('学号')).toBeVisible();
      await expect(page.getByText('班级')).toBeVisible();
      await expect(page.getByText('当前分数')).toBeVisible();
    });

    test('显示当前分数', async ({ page }) => {
      // 验证分数显示区域
      const scoreElement = page.locator('text=/\\d+\\.?\\d*/').filter({ hasText: /^[0-9]/ });
      await expect(scoreElement.first()).toBeVisible();
    });

    test('显示签到状态', async ({ page }) => {
      // 验证签到状态
      await expect(page.getByText(/已签到|未签到|签到中/)).toBeVisible();
    });
  });

  test.describe('签到功能', () => {
    test('签到按钮状态正确', async ({ page }) => {
      // 检查是否在签到中
      const checkInButton = page.getByRole('button', { name: '立即签到' });
      const alreadyCheckedIn = page.getByText('今日已签到');
      
      // 两者之一应该可见
      const isCheckInVisible = await checkInButton.isVisible().catch(() => false);
      const isAlreadyCheckedIn = await alreadyCheckedIn.isVisible().catch(() => false);
      
      expect(isCheckInVisible || isAlreadyCheckedIn).toBeTruthy();
    });

    test('成功签到', async ({ page }) => {
      const checkInButton = page.getByRole('button', { name: '立即签到' });
      
      // 如果签到按钮可见，点击签到
      if (await checkInButton.isVisible().catch(() => false)) {
        await checkInButton.click();
        
        // 等待签到请求完成
        await page.waitForResponse(response => 
          response.url().includes('/api/checkin') && response.status() === 200
        );
        
        // 验证显示已签到
        await expect(page.getByText('今日已签到')).toBeVisible();
      }
    });
  });

  test.describe('分数历史', () => {
    test('分数历史显示正常', async ({ page }) => {
      // 滚动到分数历史区域
      await page.getByText('分数变化历史').scrollIntoViewIfNeeded();
      
      // 验证分数历史标题
      await expect(page.getByText('分数变化历史')).toBeVisible();
      
      // 验证历史记录列表（如果有记录）
      const historyItems = page.locator('[data-testid="score-history-item"]');
      const count = await historyItems.count();
      
      if (count > 0) {
        // 验证第一条记录包含分数变化
        await expect(historyItems.first().locator('text=/[+-]\\d+/')).toBeVisible();
      }
    });

    test('分数历史按时间倒序排列', async ({ page }) => {
      await page.getByText('分数变化历史').scrollIntoViewIfNeeded();
      
      const historyItems = page.locator('[data-testid="score-history-item"]');
      const count = await historyItems.count();
      
      if (count >= 2) {
        // 获取第一条和第二条的时间
        const firstTime = await historyItems.nth(0).locator('time').getAttribute('datetime');
        const secondTime = await historyItems.nth(1).locator('time').getAttribute('datetime');
        
        // 验证第一条时间晚于第二条（倒序排列）
        if (firstTime && secondTime) {
          expect(new Date(firstTime) >= new Date(secondTime)).toBeTruthy();
        }
      }
    });
  });

  test.describe('修改密码', () => {
    test('修改密码对话框正常', async ({ page }) => {
      // 点击修改密码按钮
      await page.getByRole('button', { name: '修改密码' }).click();
      
      // 验证对话框显示
      await expect(page.getByRole('heading', { name: '修改密码' })).toBeVisible();
      
      // 验证输入框
      await expect(page.getByLabel('旧密码')).toBeVisible();
      await expect(page.getByLabel('新密码')).toBeVisible();
      await expect(page.getByLabel('确认新密码')).toBeVisible();
      
      // 验证按钮
      await expect(page.getByRole('button', { name: '取消' })).toBeVisible();
      await expect(page.getByRole('button', { name: '确认修改' })).toBeVisible();
      
      // 点击取消
      await page.getByRole('button', { name: '取消' }).click();
      await expect(page.getByRole('heading', { name: '修改密码' })).not.toBeVisible();
    });

    test('旧密码错误提示', async ({ page }) => {
      await page.getByRole('button', { name: '修改密码' }).click();
      
      // 填写错误的旧密码
      await page.getByLabel('旧密码').fill('wrongpassword');
      await page.getByLabel('新密码').fill('newpassword123');
      await page.getByLabel('确认新密码').fill('newpassword123');
      
      // 点击确认
      await page.getByRole('button', { name: '确认修改' }).click();
      
      // 验证错误提示
      await expect(page.getByText('旧密码错误')).toBeVisible();
    });

    test('新密码不一致提示', async ({ page }) => {
      await page.getByRole('button', { name: '修改密码' }).click();
      
      // 填写不匹配的新密码
      await page.getByLabel('旧密码').fill('2513070102');
      await page.getByLabel('新密码').fill('newpassword123');
      await page.getByLabel('确认新密码').fill('differentpassword');
      
      // 点击确认
      await page.getByRole('button', { name: '确认修改' }).click();
      
      // 验证错误提示
      await expect(page.getByText('两次输入的新密码不一致')).toBeVisible();
    });
  });
});
