import { test, expect } from '@playwright/test';

test.describe('跨角色权限测试', () => {
  test.describe('未登录访问', () => {
    test('未登录访问管理员页面重定向到登录', async ({ page }) => {
      await page.goto('/admin');
      await expect(page).toHaveURL(/.*login/);
    });

    test('未登录访问教师页面重定向到登录', async ({ page }) => {
      await page.goto('/teacher');
      await expect(page).toHaveURL(/.*login/);
    });

    test('未登录访问学生页面重定向到登录', async ({ page }) => {
      await page.goto('/student');
      await expect(page).toHaveURL(/.*login/);
    });
  });

  test.describe('学生权限限制', () => {
    async function loginAsStudent(page) {
      await page.goto('/login');
      await page.getByRole('button', { name: '学生' }).click();
      await page.getByPlaceholder('请输入用户名').fill('2513070102');
      await page.getByPlaceholder('请输入密码').fill('2513070102');
      await page.getByRole('button', { name: '登录' }).click();
      await page.waitForURL(/.*student/, { timeout: 15000 });
    }

    test('学生访问管理员页面被拒绝', async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/admin');

      // 应被重定向到学生首页
      await expect(page).toHaveURL(/.*student/);
    });

    test('学生访问教师页面被拒绝', async ({ page }) => {
      await loginAsStudent(page);
      await page.goto('/teacher');

      // 应被重定向到学生首页
      await expect(page).toHaveURL(/.*student/);
    });
  });

  test.describe('教师权限限制', () => {
    async function loginAsTeacher(page) {
      await page.goto('/login');
      await page.getByRole('button', { name: '教师' }).click();
      await page.getByPlaceholder('请输入用户名').fill('zhanziwei');
      await page.getByPlaceholder('请输入密码').fill('zha123');
      await page.getByRole('button', { name: '登录' }).click();
      await page.waitForURL(/.*teacher/, { timeout: 15000 });
    }

    test('教师访问管理员页面被拒绝', async ({ page }) => {
      await loginAsTeacher(page);
      await page.goto('/admin');

      // 应被重定向到教师首页
      await expect(page).toHaveURL(/.*teacher/);
    });

    test('教师访问学生页面', async ({ page }) => {
      await loginAsTeacher(page);
      await page.goto('/student');

      // 教师访问学生页面应被重定向到教师首页
      await expect(page).toHaveURL(/.*teacher/);
    });
  });

  test.describe('管理员权限', () => {
    async function loginAsAdmin(page) {
      await page.goto('/login');
      await page.getByRole('button', { name: '管理员' }).click();
      await page.getByPlaceholder('请输入用户名').fill('admin');
      await page.getByPlaceholder('请输入密码').fill('admin123');
      await page.getByRole('button', { name: '登录' }).click();
      await page.waitForURL(/.*admin/, { timeout: 15000 });
    }

    test('管理员访问教师页面', async ({ page }) => {
      await loginAsAdmin(page);
      await page.goto('/teacher');

      // 管理员访问教师页面应被重定向到管理员首页
      await expect(page).toHaveURL(/.*admin/);
    });

    test('管理员访问学生页面', async ({ page }) => {
      await loginAsAdmin(page);
      await page.goto('/student');

      // 管理员访问学生页面应被重定向到管理员首页
      await expect(page).toHaveURL(/.*admin/);
    });
  });

  test.describe('API权限验证', () => {
    test('未登录访问API返回401', async ({ page }) => {
      // 直接访问API端点
      const response = await page.request.get('http://localhost:8000/api/v1/users');
      expect(response.status()).toBe(401);
    });

    test('学生访问管理员API被拒绝', async ({ page }) => {
      // 先登录为学生
      await page.goto('/login');
      await page.getByRole('button', { name: '学生' }).click();
      await page.getByPlaceholder('请输入用户名').fill('2513070102');
      await page.getByPlaceholder('请输入密码').fill('2513070102');
      await page.getByRole('button', { name: '登录' }).click();
      await page.waitForURL(/.*student/, { timeout: 15000 });

      // 尝试访问管理员API
      const response = await page.request.get('http://localhost:8000/api/v1/users');
      expect(response.status()).toBe(403);
    });
  });
});
