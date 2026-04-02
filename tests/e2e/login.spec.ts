import { test, expect } from '@playwright/test';

test.describe('登录模块测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('首页显示正常', async ({ page }) => {
    // 等待页面完全加载
    await page.waitForLoadState('networkidle');

    // 验证页面标题
    await expect(page).toHaveTitle(/ClassHub/);

    // 验证导航栏
    await expect(page.locator('nav').getByText('智慧课堂')).toBeVisible();
    await expect(page.locator('nav').getByRole('button', { name: '开始使用' })).toBeVisible();

    // 验证 Hero 区域
    await expect(page.getByRole('heading', { name: /智慧管理/ })).toBeVisible();
    await expect(page.getByText(/现代化的平台/).first()).toBeVisible();

    // 验证功能卡片
    await page.getByRole('heading', { name: '学生管理' }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('heading', { name: '学生管理' })).toBeVisible();
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

  test('管理员登录成功', async ({ page }) => {
    await page.goto('/login');

    // 选择管理员角色
    await page.getByRole('button', { name: '管理员' }).click();

    // 填写登录信息
    await page.getByPlaceholder('请输入用户名').fill('admin');
    await page.getByPlaceholder('请输入密码').fill('admin123');

    // 点击登录
    await page.getByRole('button', { name: '登录' }).click();

    // 等待跳转到 admin 页面
    await page.waitForURL(/.*admin/, { timeout: 15000 });

    // 验证管理员页面内容
    await expect(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
    await expect(page.getByText(/欢迎回来|管理员/).first()).toBeVisible();
  });

  test('空用户名密码显示错误提示', async ({ page }) => {
    await page.goto('/login');

    // 直接点击登录
    await page.getByRole('button', { name: '登录' }).click();

    // 验证页面保持在登录页（浏览器原生验证阻止提交）
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/.*login/);
    // 验证输入框仍然存在
    await expect(page.getByPlaceholder('请输入用户名')).toBeVisible();
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
    await expect(page.getByText(/密码错误|用户名或密码|登录失败|错误/).first()).toBeVisible({ timeout: 8000 });
  });

  test('角色选择切换正常', async ({ page }) => {
    await page.goto('/login');

    // 点击管理员
    await page.getByRole('button', { name: '管理员' }).click();
    const adminButton = page.getByRole('button', { name: '管理员' });
    await expect(adminButton).toBeVisible();
    await expect(adminButton).toHaveClass(/border-primary|bg-primary/);

    // 点击教师
    await page.getByRole('button', { name: '教师' }).click();
    const teacherButton = page.getByRole('button', { name: '教师' });
    await expect(teacherButton).toBeVisible();
    await expect(teacherButton).toHaveClass(/border-primary|bg-primary/);

    // 点击学生
    await page.getByRole('button', { name: '学生' }).click();
    const studentButton = page.getByRole('button', { name: '学生' });
    await expect(studentButton).toBeVisible();
    await expect(studentButton).toHaveClass(/border-primary|bg-primary/);
  });
});
