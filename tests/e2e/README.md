# ClassHub E2E 功能测试方案

> 最后更新时间：2026-03-27

## 测试环境

- **前端地址**: http://localhost:5173
- **后端地址**: http://localhost:8000
- **测试框架**: Playwright

## E2E 测试结构

```
tests/e2e/
├── README.md              # 本文件
├── playwright.config.ts   # Playwright 配置
├── login.spec.ts         # 登录模块测试
├── admin.spec.ts         # 管理员功能测试
├── teacher.spec.ts       # 教师功能测试
└── student.spec.ts       # 学生功能测试
```

## 已探索功能

### 1. 首页 (Landing Page)
- 导航栏：Logo、登录按钮、开始使用按钮
- Hero 区域：标题、描述、CTA 按钮
- 功能卡片：学生管理、实时分析、课堂签到

### 2. 登录页 (Login Page)
- 角色选择：管理员/教师/学生
- 表单：用户名、密码输入
- 登录按钮
- 错误提示

### 3. Admin Dashboard
- 侧边栏导航：仪表板、学生管理、教师管理、班级管理
- 统计卡片：学生总数、活跃学生、班级总数、平均分数
- 最近活动列表

### 4. 学生管理 (Admin)
- 班级筛选下拉框
- 搜索框（姓名、学号、班级）
- 学生列表表格：学号、姓名、班级、分数、状态、操作
- 编辑分数对话框
- 删除学生按钮
- Excel 导入功能

## 测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理员 |
| 教师 | zhanziwei | zha123 | 账号为姓名拼音首字母，密码为账号+123 |
| 学生 | 2513070102 | 2513070102 | 学号作为账号和密码 |

## Playwright 测试指南

### 安装依赖

```bash
# 安装 Playwright
npm install -D @playwright/test

# 安装浏览器
npx playwright install

# 安装依赖（项目根目录）
npm install
```

### 运行测试

```bash
# 运行所有 E2E 测试
npx playwright test

# 运行特定测试文件
npx playwright test login.spec.ts
npx playwright test admin.spec.ts

# 带 UI 模式（可视化调试）
npx playwright test --ui

#  headed 模式（显示浏览器）
npx playwright test --headed

# 特定浏览器
npx playwright test --project=chromium
npx playwright test --project=firefox

# 调试模式
npx playwright test --debug
```

### 测试配置

**playwright.config.ts**:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 测试示例

```typescript
// login.spec.ts
import { test, expect } from '@playwright/test';

test('admin can login', async ({ page }) => {
  await page.goto('/login');
  
  // 选择管理员角色
  await page.click('text=管理员');
  
  // 输入凭据
  await page.fill('[name="username"]', 'admin');
  await page.fill('[name="password"]', 'admin123');
  
  // 点击登录
  await page.click('button[type="submit"]');
  
  // 验证跳转
  await expect(page).toHaveURL('/admin');
  await expect(page.locator('text=管理仪表板')).toBeVisible();
});
```

## 测试场景清单

### 登录模块
- [x] 管理员登录成功
- [x] 教师登录成功
- [x] 学生登录成功
- [x] 错误密码提示
- [x] 空表单验证

### 学生管理
- [x] 查看学生列表
- [x] 搜索学生
- [x] 添加学生
- [x] 编辑学生分数
- [x] 删除学生
- [x] Excel 导入学生

### 签到功能
- [x] 学生签到
- [x] 重复签到提示
- [x] 教师代签

### 用户管理
- [x] 创建教师用户
- [x] 重置密码
- [x] 删除用户

## 截图记录

测试过程中会生成以下截图：
- `screenshots/01-homepage.png` - 首页
- `screenshots/02-login-page.png` - 登录页
- `screenshots/03-admin-dashboard.png` - 管理仪表板
- `screenshots/04-admin-students.png` - 学生管理页

## 调试技巧

### 1. 使用 Playwright Inspector
```bash
npx playwright test --debug
```

### 2. 添加断点
```typescript
await page.pause();  // 测试执行到此暂停
```

### 3. 查看测试报告
```bash
npx playwright show-report
```

### 4. 录制测试
```bash
npx playwright codegen http://localhost:5173
```

## CI/CD 集成

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npx playwright test
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## 常见问题

### Q1: 测试找不到页面
**解决**: 确保前后端服务都已启动
```bash
# 终端1: 启动后端
cd backend && python main.py

# 终端2: 启动前端
cd frontend-v3 && pnpm dev
```

### Q2: 登录测试失败
**解决**: 检查测试账号是否正确，数据库是否有测试数据

### Q3: 测试超时
**解决**: 增加超时时间或检查网络连接
```typescript
// playwright.config.ts
use: {
  actionTimeout: 10000,
  navigationTimeout: 30000,
}
```

---

**测试框架**: Playwright  
**浏览器支持**: Chromium, Firefox, WebKit  
**最后更新**: 2026-03-27
