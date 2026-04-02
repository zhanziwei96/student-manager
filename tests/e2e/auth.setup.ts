import { test as setup, expect } from '@playwright/test';

const adminAuthFile = '.auth/admin.json';
const teacherAuthFile = '.auth/teacher.json';
const studentAuthFile = '.auth/student.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: '管理员' }).click();
  await page.getByPlaceholder('请输入用户名').fill('admin');
  await page.getByPlaceholder('请输入密码').fill('admin123');
  await page.getByText('登录', { exact: true }).click();
  await page.waitForURL(/.*admin/, { timeout: 15000 });

  await page.context().storageState({ path: adminAuthFile });
});

setup('authenticate as teacher', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: '教师' }).click();
  await page.getByPlaceholder('请输入用户名').fill('zhanziwei');
  await page.getByPlaceholder('请输入密码').fill('zha123');
  await page.getByText('登录', { exact: true }).click();
  await page.waitForURL(/.*teacher/, { timeout: 15000 });

  await page.context().storageState({ path: teacherAuthFile });
});

setup('authenticate as student', async ({ page }) => {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: '学生' }).click();
  await page.getByPlaceholder('请输入用户名').fill('2513070102');
  await page.getByPlaceholder('请输入密码').fill('2513070102');
  await page.getByText('登录', { exact: true }).click();
  await page.waitForURL(/.*student/, { timeout: 15000 });

  await page.context().storageState({ path: studentAuthFile });
});
