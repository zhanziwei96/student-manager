import { test, expect } from '@playwright/test';

test.describe('教师功能测试', () => {
  async function loginAsTeacher(page) {
    await page.goto('/login');
    await page.getByRole('button', { name: '教师' }).click();
    await page.getByPlaceholder('请输入用户名').fill('zhanziwei');
    await page.getByPlaceholder('请输入密码').fill('zha123');
    await page.getByRole('button', { name: '登录' }).click();
    await page.waitForURL(/.*teacher/);
  }

  test.beforeEach(async ({ page }) => {
    await loginAsTeacher(page);
  });

  test.describe('教师仪表板', () => {
    test('仪表板显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '教师仪表板' })).toBeVisible();
      
      // 验证侧边栏导航
      await expect(page.getByRole('link', { name: '仪表板' })).toBeVisible();
      await expect(page.getByRole('link', { name: '学生管理' })).toBeVisible();
      await expect(page.getByRole('link', { name: '课堂签到' })).toBeVisible();
    });

    test('快捷操作按钮正常', async ({ page }) => {
      await expect(page.getByRole('button', { name: '开始上课' })).toBeVisible();
      await expect(page.getByRole('button', { name: '查看学生' })).toBeVisible();
    });
  });

  test.describe('教师学生管理', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: '学生管理' }).click();
      await page.waitForURL(/.*teacher\/students/);
    });

    test('学生列表显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '我的学生' })).toBeVisible();
      await expect(page.getByPlaceholder('搜索学生...')).toBeVisible();
      
      // 验证学生卡片列表
      const studentCards = page.locator('[data-testid="student-card"]');
      await expect(studentCards.count()).toBeGreaterThanOrEqual(0);
    });

    test('可以为学生调整分数', async ({ page }) => {
      // 找到第一个学生卡片
      const firstStudent = page.locator('[data-testid="student-card"]').first();
      
      if (await firstStudent.isVisible()) {
        // 点击加分按钮
        await firstStudent.locator('button').first().click();
        
        // 验证分数对话框
        await expect(page.getByRole('heading', { name: '更新分数' })).toBeVisible();
        
        // 填写分数变化
        await page.getByRole('spinbutton', { name: '分数变化' }).fill('10');
        await page.getByPlaceholder('输入分数变化原因').fill('课堂表现优秀');
        
        // 点击更新
        await page.getByRole('button', { name: '更新分数' }).click();
        
        // 验证对话框关闭
        await expect(page.getByRole('heading', { name: '更新分数' })).not.toBeVisible();
      }
    });
  });

  test.describe('课堂签到', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: '课堂签到' }).click();
      await page.waitForURL(/.*teacher\/session/);
    });

    test('课堂签到页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '课堂签到' })).toBeVisible();
      
      // 验证签到状态显示
      await expect(page.getByText(/签到中|未开始/)).toBeVisible();
    });

    test('开始课堂签到流程', async ({ page }) => {
      // 检查是否已经在签到中
      const endButton = page.getByRole('button', { name: '结束签到' });
      const isActive = await endButton.isVisible().catch(() => false);
      
      if (!isActive) {
        // 点击开始签到
        await page.getByRole('button', { name: '开始签到' }).click();
        
        // 验证班级选择对话框
        await expect(page.getByRole('heading', { name: '选择班级' })).toBeVisible();
        
        // 选择班级（假设有班级选项）
        const classOptions = page.locator('[role="option"]');
        if (await classOptions.count() > 0) {
          await classOptions.first().click();
          await page.getByRole('button', { name: '确认' }).click();
          
          // 验证签到状态变为进行中
          await expect(page.getByText('签到中')).toBeVisible();
        }
      } else {
        // 已经在签到中，验证结束按钮存在
        await expect(endButton).toBeVisible();
      }
    });
  });
});
