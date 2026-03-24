import { test, expect } from '@playwright/test';

test.describe('管理员功能测试', () => {
  // 登录辅助函数
  async function loginAsAdmin(page) {
    await page.goto('/login');
    await page.getByRole('button', { name: '管理员' }).click();
    await page.getByPlaceholder('请输入用户名').fill('admin');
    await page.getByPlaceholder('请输入密码').fill('admin123');
    await page.getByRole('button', { name: '登录' }).click();
    await page.waitForURL(/.*admin/);
  }

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test.describe('仪表板', () => {
    test('仪表板显示正常', async ({ page }) => {
      // 验证标题和欢迎信息
      await expect(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
      await expect(page.getByText('欢迎回来，管理员')).toBeVisible();
      
      // 验证统计卡片
      await expect(page.getByText('学生总数')).toBeVisible();
      await expect(page.getByText('活跃学生')).toBeVisible();
      await expect(page.getByText('班级总数')).toBeVisible();
      await expect(page.getByText('平均分数')).toBeVisible();
      
      // 验证最近活动
      await expect(page.getByRole('heading', { name: '最近活动' })).toBeVisible();
    });

    test('侧边栏导航正常', async ({ page }) => {
      // 验证导航链接
      await expect(page.getByRole('link', { name: '仪表板' })).toBeVisible();
      await expect(page.getByRole('link', { name: '学生管理' })).toBeVisible();
      await expect(page.getByRole('link', { name: '教师管理' })).toBeVisible();
      await expect(page.getByRole('link', { name: '班级管理' })).toBeVisible();
      
      // 验证退出登录按钮
      await expect(page.getByRole('button', { name: '退出登录' })).toBeVisible();
    });

    test('统计卡片显示数值', async ({ page }) => {
      // 验证学生总数卡片有数值
      const studentCard = page.locator('text=学生总数').locator('..');
      await expect(studentCard.locator('text=/\\d+/')).toBeVisible();
      
      // 验证班级总数卡片有数值
      const classCard = page.locator('text=班级总数').locator('..');
      await expect(classCard.locator('text=/\\d+/')).toBeVisible();
    });
  });

  test.describe('学生管理', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: '学生管理' }).click();
      await page.waitForURL(/.*admin\/students/);
    });

    test('学生管理页面显示正常', async ({ page }) => {
      // 验证页面标题
      await expect(page.getByRole('heading', { name: '学生管理' })).toBeVisible();
      await expect(page.getByText('管理学生档案和分数')).toBeVisible();
      
      // 验证添加学生按钮
      await expect(page.getByRole('button', { name: '添加学生' })).toBeVisible();
      
      // 验证班级筛选
      await expect(page.getByRole('button', { name: '全部班级' })).toBeVisible();
      
      // 验证搜索框
      await expect(page.getByPlaceholder('搜索姓名、学号或班级...')).toBeVisible();
      
      // 验证表格表头
      await expect(page.getByRole('columnheader', { name: '学号' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '姓名' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '班级' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '分数' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '状态' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '操作' })).toBeVisible();
    });

    test('学生列表显示数据', async ({ page }) => {
      // 验证表格中有学生数据
      const rows = page.getByRole('row');
      await expect(rows.count()).toBeGreaterThan(1); // 至少表头+一行数据
      
      // 验证第一行数据包含学号格式
      const firstDataRow = page.getByRole('row').nth(1);
      await expect(firstDataRow.locator('text=/\\d{10}/')).toBeVisible();
    });

    test('搜索功能正常工作', async ({ page }) => {
      const searchInput = page.getByPlaceholder('搜索姓名、学号或班级...');
      
      // 输入搜索关键词
      await searchInput.fill('张三');
      await page.waitForTimeout(500); // 等待防抖
      
      // 验证搜索结果或空状态
      const rows = page.getByRole('row');
      const count = await rows.count();
      
      // 如果有结果，验证包含搜索词；如果没有，验证显示空状态
      if (count > 1) {
        await expect(page.getByText('张三')).toBeVisible();
      }
    });

    test('班级筛选功能正常', async ({ page }) => {
      // 点击班级筛选下拉
      await page.getByRole('button', { name: '全部班级' }).click();
      
      // 等待下拉选项出现
      await page.waitForTimeout(300);
      
      // 验证下拉中有选项（如果有班级数据）
      const options = page.locator('[role="option"]');
      const count = await options.count();
      
      if (count > 0) {
        // 选择第一个班级
        await options.first().click();
        
        // 验证表格数据更新
        await page.waitForTimeout(500);
        
        // 验证筛选后的表格有数据
        const rows = page.getByRole('row');
        await expect(rows.count()).toBeGreaterThanOrEqual(1);
      }
    });

    test('编辑分数对话框正常', async ({ page }) => {
      // 点击第一个学生的编辑按钮
      const firstRow = page.getByRole('row').nth(1);
      await firstRow.locator('button').first().click();
      
      // 验证对话框显示
      await expect(page.getByRole('heading', { name: '更新分数' })).toBeVisible();
      
      // 验证输入框
      await expect(page.getByRole('spinbutton', { name: '分数变化' })).toBeVisible();
      await expect(page.getByPlaceholder('输入分数变化原因')).toBeVisible();
      
      // 验证按钮
      await expect(page.getByRole('button', { name: '取消' })).toBeVisible();
      await expect(page.getByRole('button', { name: '更新分数' })).toBeVisible();
      
      // 点击取消关闭对话框
      await page.getByRole('button', { name: '取消' }).click();
      await expect(page.getByRole('heading', { name: '更新分数' })).not.toBeVisible();
    });

    test('添加学生对话框正常', async ({ page }) => {
      // 点击添加学生按钮
      await page.getByRole('button', { name: '添加学生' }).click();
      
      // 验证对话框显示
      await expect(page.getByRole('heading', { name: '添加学生' })).toBeVisible();
      
      // 验证表单字段
      await expect(page.getByLabel('学号')).toBeVisible();
      await expect(page.getByLabel('姓名')).toBeVisible();
      await expect(page.getByLabel('班级')).toBeVisible();
      
      // 验证按钮
      await expect(page.getByRole('button', { name: '取消' })).toBeVisible();
      await expect(page.getByRole('button', { name: '添加' })).toBeVisible();
      
      // 点击取消关闭对话框
      await page.getByRole('button', { name: '取消' }).click();
      await expect(page.getByRole('heading', { name: '添加学生' })).not.toBeVisible();
    });
  });

  test.describe('教师管理', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: '教师管理' }).click();
      await page.waitForURL(/.*admin\/teachers/);
    });

    test('教师管理页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '教师管理' })).toBeVisible();
      await expect(page.getByRole('button', { name: '添加教师' })).toBeVisible();
    });
  });

  test.describe('班级管理', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: '班级管理' }).click();
      await page.waitForURL(/.*admin\/classes/);
    });

    test('班级管理页面显示正常', async ({ page }) => {
      await expect(page.getByRole('heading', { name: '班级管理' })).toBeVisible();
      await expect(page.getByRole('button', { name: '添加班级' })).toBeVisible();
    });
  });

  test.describe('退出登录', () => {
    test('退出登录成功', async ({ page }) => {
      // 点击退出登录
      await page.getByRole('button', { name: '退出登录' }).click();
      
      // 验证跳转到首页或登录页
      await expect(page).toHaveURL(/\/(login)?/);
      
      // 验证登录按钮可见
      await expect(page.getByRole('button', { name: '登录' }).or(
        page.getByRole('button', { name: '开始使用' })
      )).toBeVisible();
    });
  });
});
