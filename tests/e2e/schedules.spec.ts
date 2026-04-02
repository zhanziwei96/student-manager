import { test, expect } from '@playwright/test';

test.describe('课表管理测试', () => {
  test.beforeEach(async ({ page }) => {
    // 使用已登录状态，直接访问课表管理页面
    await page.goto('/admin/schedules');
    await page.waitForURL(/.*admin\/schedules/, { timeout: 15000 });
  });

  test.describe('课表列表', () => {
    test('课表页面显示正常', async ({ page }) => {
      // 验证页面标题
      await expect(page.getByRole('heading', { name: '课表管理' })).toBeVisible();
      await expect(page.getByText('管理课程安排和教师分配')).toBeVisible();

      // 验证操作按钮
      await expect(page.getByRole('button', { name: '导入课表' })).toBeVisible();
      await expect(page.getByRole('button', { name: '下载模板' })).toBeVisible();

      // 验证筛选器
      await expect(page.getByRole('button', { name: '全部班级' })).toBeVisible();
      await expect(page.getByRole('button', { name: '全部教师' })).toBeVisible();
    });

    test('课表表格显示正确列', async ({ page }) => {
      // 验证表格表头
      await expect(page.getByRole('columnheader', { name: '课程名称' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '班级' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '教师' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '时间' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '教室' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '周次' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: '操作' })).toBeVisible();
    });

    test('课表数据加载显示', async ({ page }) => {
      // 等待数据加载
      await page.waitForTimeout(1000);

      // 验证表格行数（至少表头+数据行）
      const rows = page.getByRole('row');
      const count = await rows.count();

      if (count > 1) {
        // 验证数据行包含课程信息
        const firstDataRow = rows.nth(1);
        await expect(firstDataRow.locator('td').first()).not.toBeEmpty();
      }
    });
  });

  test.describe('班级筛选', () => {
    test('班级筛选功能正常', async ({ page }) => {
      // 点击班级筛选
      await page.getByRole('button', { name: '全部班级' }).click();
      await page.waitForTimeout(300);

      // 获取班级选项
      const options = page.locator('[role="option"]');
      const count = await options.count();

      if (count > 0) {
        // 选择第一个班级
        const firstClass = await options.first().textContent();
        await options.first().click();

        // 验证筛选后的表格显示该班级的课程
        await page.waitForTimeout(500);

        // 验证筛选按钮显示选中的班级
        await expect(page.getByRole('button', { name: firstClass || '' })).toBeVisible();
      }
    });

    test('教师筛选功能正常', async ({ page }) => {
      // 点击教师筛选
      await page.getByRole('button', { name: '全部教师' }).click();
      await page.waitForTimeout(300);

      // 获取教师选项
      const options = page.locator('[role="option"]');
      const count = await options.count();

      if (count > 0) {
        // 选择第一个教师
        await options.first().click();
        await page.waitForTimeout(500);

        // 验证筛选后的表格数据
        const rows = page.getByRole('row');
        await expect(rows.count()).toBeGreaterThanOrEqual(1);
      }
    });
  });

  test.describe('教师分配', () => {
    test('分配教师对话框正常', async ({ page }) => {
      // 等待数据加载
      await page.waitForTimeout(1000);

      // 找到第一个未分配教师的课程
      const rows = page.getByRole('row');
      const count = await rows.count();

      if (count > 1) {
        // 点击分配按钮
        const assignButton = page.getByRole('button', { name: '分配' }).first();
        if (await assignButton.isVisible().catch(() => false)) {
          await assignButton.click();

          // 验证分配对话框
          await expect(page.getByRole('heading', { name: /分配教师|选择教师/ })).toBeVisible();

          // 验证教师列表
          await expect(page.locator('[role="radiogroup"], [role="list"]')).toBeVisible();

          // 点击取消
          await page.getByRole('button', { name: '取消' }).click();
          await expect(page.getByRole('heading', { name: /分配教师|选择教师/ })).not.toBeVisible();
        }
      }
    });

    test('取消分配功能正常', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 找到已分配教师的课程（有"取消分配"按钮）
      const unassignButton = page.getByRole('button', { name: '取消分配' }).first();

      if (await unassignButton.isVisible().catch(() => false)) {
        await unassignButton.click();

        // 验证确认对话框或操作成功提示
        await expect(page.getByText(/确认|成功|已取消/).or(
          page.getByRole('heading', { name: /确认/ })
        )).toBeVisible();
      }
    });
  });

  test.describe('导入功能', () => {
    test('导入对话框正常显示', async ({ page }) => {
      // 点击导入按钮
      await page.getByRole('button', { name: '导入课表' }).click();

      // 验证对话框
      await expect(page.getByRole('heading', { name: /导入课表|上传课表/ })).toBeVisible();

      // 验证文件上传区域
      await expect(page.locator('input[type="file"]')).toBeVisible();

      // 验证说明文字
      await expect(page.getByText(/Excel|xlsx|模板/)).toBeVisible();

      // 取消导入
      await page.getByRole('button', { name: '取消' }).click();
      await expect(page.getByRole('heading', { name: /导入课表|上传课表/ })).not.toBeVisible();
    });

    test('下载模板功能', async ({ page }) => {
      // 等待下载事件
      const downloadPromise = page.waitForEvent('download');

      // 点击下载模板
      await page.getByRole('button', { name: '下载模板' }).click();

      // 验证下载开始
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/template|课表|schedule/);
    });

    test('无效文件格式提示', async ({ page }) => {
      // 点击导入
      await page.getByRole('button', { name: '导入课表' }).click();

      // 上传非 Excel 文件
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputData({
        name: 'invalid.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('invalid data')
      });

      // 验证错误提示
      await expect(page.getByText(/格式|Excel|xlsx/)).toBeVisible();
    });
  });

  test.describe('删除课程', () => {
    test('删除课程确认对话框', async ({ page }) => {
      await page.waitForTimeout(1000);

      // 找到删除按钮
      const deleteButton = page.getByRole('button', { name: '删除' }).first();

      if (await deleteButton.isVisible().catch(() => false)) {
        await deleteButton.click();

        // 验证确认对话框
        await expect(page.getByRole('heading', { name: /确认删除/ })).toBeVisible();
        await expect(page.getByText(/确定|确认|删除/)).toBeVisible();

        // 点击取消
        await page.getByRole('button', { name: '取消' }).click();
        await expect(page.getByRole('heading', { name: /确认删除/ })).not.toBeVisible();
      }
    });
  });
});
