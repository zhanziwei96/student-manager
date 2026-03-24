import { test, expect } from '@playwright/test';

test.describe('登录模块测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('首页显示正常', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/ClassHub/);
    
    // 验证导航栏
    await expect(page.getByText('智慧课堂')).toBeVisible();
    await expect(page.getByRole('button', { name: '开始使用' })).toBeVisible();
    
    // 验证 Hero 区域
    await expect(page.getByRole('heading', { name: '智慧管理课堂' })).toBeVisible();
    await expect(page.getByText('一个现代化的平台')).toBeVisible();
    
    // 验证功能卡片
    await expect(page.getByText('学生管理')).toBeVisible();
    await expect(page.getByText('实时分析')).toBeVisible();
    await expect(page.getByText('课堂签到')).toBeVisible();
  });

  test('点击开始使用跳转到登录页', async ({ page }) => {
    await page.getByRole('button', { name: '开始使用' }).first().click();
    
    // 验证跳转到登录页
    await expect(page).toHaveURL(/.*login/);
    await expect(page.getByRole('heading', { name: '欢迎使用智慧课堂' })).toBeVisible();
  });

  test('登录页显示正常', async ({ page }) => {
    await page.goto('/login');
    
    // 验证角色选择按钮
    await expect(page.getByRole('button', { name: '管理员' })).toBeVisible();
    await expect(page.getByRole('button', { name: '教师' })).toBeVisible();
    await expect(page.getByRole('button', { name: '学生' })).toBeVisible();
    
    // 验证输入框
    await expect(page.getByPlaceholder('请输入用户名')).toBeVisible();
    await expect(page.getByPlaceholder('请输入密码')).toBeVisible();
    
    // 验证登录按钮
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
  });

  test('管理员登录成功', async ({ page, context }) => {
    await page.goto('/login');
    
    // 选择管理员角色
    await page.getByRole('button', { name: '管理员' }).click();
    
    // 填写登录信息
    await page.getByPlaceholder('请输入用户名').fill('admin');
    await page.getByPlaceholder('请输入密码').fill('admin123');
    
    // 点击登录
    await page.getByRole('button', { name: '登录' }).click();
    
    // 等待登录请求完成
    await page.waitForResponse(response => 
      response.url().includes('/api/login') && response.status() === 200
    );
    
    // 验证跳转到 admin 页面
    await expect(page).toHaveURL(/.*admin/);
    
    // 验证管理员页面内容
    await expect(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
    await expect(page.getByText('欢迎回来，管理员')).toBeVisible();
  });

  test('空用户名密码显示错误提示', async ({ page }) => {
    await page.goto('/login');
    
    // 直接点击登录
    await page.getByRole('button', { name: '登录' }).click();
    
    // 验证错误提示（浏览器原生验证或自定义提示）
    const usernameInput = page.getByPlaceholder('请输入用户名');
    await expect(usernameInput).toHaveAttribute('required');
  });

  test('错误密码登录失败', async ({ page }) => {
    await page.goto('/login');
    
    // 选择管理员角色
    await page.getByRole('button', { name: '管理员' }).click();
    
    // 填写错误的密码
    await page.getByPlaceholder('请输入用户名').fill('admin');
    await page.getByPlaceholder('请输入密码').fill('wrongpassword');
    
    // 点击登录
    await page.getByRole('button', { name: '登录' }).click();
    
    // 等待错误提示
    await expect(page.getByText('用户名或密码错误')).toBeVisible({ timeout: 5000 });
  });

  test('角色选择切换正常', async ({ page }) => {
    await page.goto('/login');
    
    // 点击管理员
    await page.getByRole('button', { name: '管理员' }).click();
    await expect(page.getByRole('button', { name: '管理员' })).toHaveAttribute('active', '');
    
    // 点击教师
    await page.getByRole('button', { name: '教师' }).click();
    await expect(page.getByRole('button', { name: '教师' })).toHaveAttribute('active', '');
    
    // 点击学生
    await page.getByRole('button', { name: '学生' }).click();
    await expect(page.getByRole('button', { name: '学生' })).toHaveAttribute('active', '');
  });
});
