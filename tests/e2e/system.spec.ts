import { test, expect } from '@playwright/test';

test.describe('系统健康检查测试', () => {
  test.describe('前端应用', () => {
    test('首页可访问', async ({ page }) => {
      await page.goto('/');
      await expect(page).toHaveTitle(/ClassHub|智慧课堂/);
      await expect(page.getByText('智慧课堂')).toBeVisible();
    });

    test('登录页可访问', async ({ page }) => {
      await page.goto('/login');
      await expect(page.getByRole('heading', { name: /欢迎/ })).toBeVisible();
      await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
    });

    test('404页面显示正常', async ({ page }) => {
      await page.goto('/non-existent-page');
      await expect(page.getByText(/404|页面不存在|Not Found/)).toBeVisible();
    });

    test('静态资源加载正常', async ({ page }) => {
      await page.goto('/');

      // 检查CSS是否加载
      const styles = await page.evaluate(() => {
        const styleSheets = Array.from(document.styleSheets);
        return styleSheets.length > 0;
      });
      expect(styles).toBe(true);

      // 检查字体是否加载
      await expect(page.getByText('智慧课堂')).toBeVisible();
    });
  });

  test.describe('后端API', () => {
    test('健康检查端点正常', async ({ request }) => {
      const response = await request.get('http://localhost:8000/api/v1/health');
      expect(response.status()).toBe(200);

      const body = await response.json();
      expect(body.status).toBe('healthy');
      expect(body.version).toBeDefined();
    });

    test('API文档可访问', async ({ page }) => {
      await page.goto('http://localhost:8000/docs');
      await expect(page.getByText('FastAPI')).toBeVisible({ timeout: 10000 });
    });

    test('登录API正常工作', async ({ request }) => {
      const response = await request.post('http://localhost:8000/api/v1/login', {
        data: {
          username: 'admin',
          password: 'admin123',
          role: 'admin'
        }
      });

      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.success).toBe(true);
      expect(body.data.token).toBeDefined();
    });

    test('错误密码返回401', async ({ request }) => {
      const response = await request.post('http://localhost:8000/api/v1/login', {
        data: {
          username: 'admin',
          password: 'wrongpassword',
          role: 'admin'
        }
      });

      expect(response.status()).toBe(401);
    });
  });

  test.describe('数据库连接', () => {
    test('学生列表API返回数据', async ({ request }) => {
      // 先登录获取token
      const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
        data: {
          username: 'admin',
          password: 'admin123',
          role: 'admin'
        }
      });

      const loginBody = await loginResponse.json();
      const token = loginBody.data.token;

      // 使用token访问受保护端点
      const response = await request.get('http://localhost:8000/api/v1/students', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.success).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
    });
  });

  test.describe('前端与后端集成', () => {
    test('前端能成功调用后端API', async ({ page }) => {
      await page.goto('/login');

      // 监听API请求
      const apiResponsePromise = page.waitForResponse(response =>
        response.url().includes('/api/v1/login')
      );

      await page.getByRole('button', { name: '管理员' }).click();
      await page.getByPlaceholder('请输入用户名').fill('admin');
      await page.getByPlaceholder('请输入密码').fill('admin123');
      await page.getByRole('button', { name: '登录' }).click();

      const apiResponse = await apiResponsePromise;
      expect(apiResponse.status()).toBe(200);

      const body = await apiResponse.json();
      expect(body.success).toBe(true);
    });

    test('后端返回的数据格式正确', async ({ page }) => {
      await page.goto('/login');
      await page.getByRole('button', { name: '管理员' }).click();
      await page.getByPlaceholder('请输入用户名').fill('admin');
      await page.getByPlaceholder('请输入密码').fill('admin123');
      await page.getByRole('button', { name: '登录' }).click();

      await page.waitForURL(/.*admin/);

      // 验证仪表板数据加载
      await expect(page.getByText('学生总数')).toBeVisible();
      await expect(page.getByText(/\d+/).first()).toBeVisible();
    });
  });
});
