# ClassHub E2E 功能测试套件

> 最后更新时间：2026-04-02

## 测试环境

- **前端地址**: http://localhost:5173
- **后端地址**: http://localhost:8000
- **测试框架**: Playwright

## 测试文件结构

```
tests/e2e/
├── playwright.config.ts      # Playwright 配置
├── README.md                 # 本文档
├── login.spec.ts            # 登录模块测试
├── admin.spec.ts            # 管理员功能测试（基础）
├── admin-teachers.spec.ts   # 教师管理完整测试
├── admin-classes.spec.ts    # 班级管理完整测试
├── admin-checkins.spec.ts   # 签到记录查看测试
├── admin-schedules.spec.ts  # 课表管理完整测试
├── admin-audit.spec.ts      # 审计日志测试
├── teacher.spec.ts          # 教师功能测试（基础）
├── teacher-session.spec.ts  # 课堂签到完整测试
├── teacher-schedules.spec.ts # 教师课表查看测试
├── student.spec.ts          # 学生功能测试（基础）
├── student-checkin.spec.ts  # 学生签到完整测试
├── cross-role.spec.ts       # 跨角色权限测试
└── system.spec.ts           # 系统健康检查
```

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 系统管理 |
| 教师 | zhanziwei | zha123 | 教师功能测试 |
| 学生 | 2513070102 | 2513070102 | 学生功能测试 |

## 测试覆盖功能

### 登录模块 (login.spec.ts)
- [x] 首页显示正常
- [x] 跳转到登录页
- [x] 登录页显示正常
- [x] 管理员登录成功
- [x] 空用户名密码验证
- [x] 错误密码登录失败
- [x] 角色选择切换正常

### 管理员功能 - 基础 (admin.spec.ts)
- [x] 仪表板显示正常
- [x] 侧边栏导航正常
- [x] 统计卡片显示数值
- [x] 学生管理页面显示
- [x] 学生列表显示数据
- [x] 搜索功能正常
- [x] 班级筛选功能
- [x] 编辑分数对话框
- [x] 添加学生对话框
- [x] 退出登录成功

### 管理员功能 - 教师管理 (admin-teachers.spec.ts)
- [x] 教师列表显示
- [x] 添加新教师
- [x] 添加重复用户名提示
- [x] 编辑教师信息
- [x] 管理班级分配
- [x] 重置教师密码
- [x] 启用/禁用教师账户
- [x] 删除教师确认
- [x] 禁用后无法登录

### 管理员功能 - 班级管理 (admin-classes.spec.ts)
- [x] 班级列表显示
- [x] 添加新班级
- [x] 添加班级表单验证
- [x] 编辑班级信息
- [x] 删除班级确认
- [x] 查看班级学生

### 管理员功能 - 签到管理 (admin-checkins.spec.ts)
- [x] 签到管理页面显示
- [x] 统计卡片显示（总学生/已签到/未签到/签到率）
- [x] 筛选器显示
- [x] 按班级筛选
- [x] 按学生搜索
- [x] 签到记录显示学生信息
- [x] 签到时间格式化
- [x] 空状态显示

### 管理员功能 - 课表管理 (admin-schedules.spec.ts)
- [x] 课表页面显示
- [x] 课表表格列显示
- [x] 按班级筛选
- [x] 按教师筛选
- [x] 分配教师对话框
- [x] 取消教师分配
- [x] 导入课表对话框
- [x] 下载模板功能
- [x] 无效文件格式提示
- [x] 删除课程确认

### 教师功能 - 基础 (teacher.spec.ts)
- [x] 教师仪表板显示
- [x] 快捷操作按钮
- [x] 学生列表显示
- [x] 调整学生分数

### 教师功能 - 课堂签到 (teacher-session.spec.ts)
- [x] 课堂签到页面显示
- [x] 签到状态显示
- [x] 开始签到选择班级
- [x] 签到后统计信息显示
- [x] 已签到学生列表
- [x] 未签到学生列表
- [x] 手动代签功能
- [x] 地图组件显示
- [x] 签到位置标记
- [x] 结束签到确认
- [x] 结束签到后状态更新
- [x] 签到率计算
- [x] 签到人数统计

### 教师功能 - 课表查看 (teacher-schedules.spec.ts)
- [x] 课表页面显示
- [x] 按星期显示
- [x] 课程卡片信息
- [x] 今日课表显示

### 学生功能 - 基础 (student.spec.ts)
- [x] 学生仪表板显示
- [x] 个人信息卡片
- [x] 当前分数显示
- [x] 签到状态显示
- [x] 签到按钮状态
- [x] 成功签到
- [x] 分数历史显示
- [x] 修改密码对话框
- [x] 旧密码错误提示
- [x] 新密码不一致提示

### 学生功能 - 签到 (student-checkin.spec.ts)
- [x] 签到页面显示
- [x] 签到状态显示
- [x] 签到按钮状态
- [x] 成功签到
- [x] 重复签到提示
- [x] 签到后分数更新
- [x] 分数历史显示
- [x] 分数变化格式

### 跨角色权限 (cross-role.spec.ts)
- [x] 未登录访问管理员页面重定向
- [x] 未登录访问教师页面重定向
- [x] 未登录访问学生页面重定向
- [x] 学生访问管理员页面被拒绝
- [x] 学生访问教师页面被拒绝
- [x] 教师访问管理员页面被拒绝
- [x] 管理员访问教师页面重定向
- [x] API未登录返回401
- [x] API权限不足返回403

### 系统健康检查 (system.spec.ts)
- [x] 首页可访问
- [x] 登录页可访问
- [x] 404页面显示
- [x] 静态资源加载
- [x] 后端健康检查端点
- [x] API文档可访问
- [x] 登录API工作正常
- [x] 错误密码返回401
- [x] 数据库连接正常
- [x] 前后端集成正常

## 运行测试

### 前置条件
确保前后端服务已启动：

```bash
# 终端1: 启动后端
cd backend && conda run -n student-manage python main.py

# 终端2: 启动前端
cd frontend-v3 && pnpm dev
```

### 安装依赖

```bash
cd tests/e2e
npm install
npx playwright install chromium
```

### 运行所有测试

```bash
npx playwright test
```

### 运行特定测试文件

```bash
npx playwright test login.spec.ts
npx playwright test admin-teachers.spec.ts
npx playwright test teacher-session.spec.ts
```

### 按标签运行

```bash
# 运行管理员相关测试
npx playwright test --grep "admin"

# 运行教师相关测试
npx playwright test --grep "teacher"
```

### 调试模式

```bash
# UI模式（可视化）
npx playwright test --ui

# headed模式（显示浏览器）
npx playwright test --headed

# 调试模式
npx playwright test --debug

# 单步调试
npx playwright test --debug --headed
```

### 生成报告

```bash
# 运行测试并生成HTML报告
npx playwright test --reporter=html

# 查看报告
npx playwright show-report
```

## 测试配置

### playwright.config.ts 关键配置

```typescript
export default defineConfig({
  testDir: '.',
  timeout: 60000,              // 测试超时60秒
  retries: 2,                  // 失败重试2次
  workers: 1,                  // CI环境单worker
  use: {
    baseURL: 'http://localhost:5173',
    actionTimeout: 10000,      // 操作超时10秒
    navigationTimeout: 30000,  // 导航超时30秒
    trace: 'on-first-retry',   // 失败时记录trace
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

## 测试编写指南

### 1. 使用Page Object模式

```typescript
// 创建辅助函数
async function loginAsAdmin(page) {
  await page.goto('/login');
  await page.getByRole('button', { name: '管理员' }).click();
  await page.getByPlaceholder('请输入用户名').fill('admin');
  await page.getByPlaceholder('请输入密码').fill('admin123');
  await page.getByRole('button', { name: '登录' }).click();
  await page.waitForURL(/.*admin/);
}
```

### 2. 条件测试

```typescript
test('条件功能测试', async ({ page }) => {
  const button = page.getByRole('button', { name: '特定按钮' });

  // 检查元素是否存在
  if (await button.isVisible().catch(() => false)) {
    await button.click();
    // 验证结果
  }
});
```

### 3. 等待策略

```typescript
// 等待API响应
const responsePromise = page.waitForResponse(response =>
  response.url().includes('/api/v1/login') && response.status() === 200
);
await page.getByRole('button', { name: '登录' }).click();
const response = await responsePromise;

// 等待URL变化
await page.waitForURL(/.*admin/);

// 固定等待（少用）
await page.waitForTimeout(1000);
```

### 4. 断言最佳实践

```typescript
// 验证元素可见
await expect(page.getByRole('heading', { name: '标题' })).toBeVisible();

// 验证文本内容
await expect(page.getByText(/成功|完成/)).toBeVisible();

// 验证URL
await expect(page).toHaveURL(/.*admin/);

// 多条件断言
await expect(page.getByText('A').or(page.getByText('B'))).toBeVisible();
```

## CI/CD集成

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
        run: cd tests/e2e && npm ci
      - name: Install Playwright
        run: cd tests/e2e && npx playwright install --with-deps chromium
      - name: Start backend
        run: cd backend && conda run -n student-manage python main.py &
      - name: Start frontend
        run: cd frontend-v3 && pnpm dev &
      - name: Wait for services
        run: npx wait-on http://localhost:8000/api/v1/health http://localhost:5173
      - name: Run E2E tests
        run: cd tests/e2e && npx playwright test
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

## 常见问题

### Q1: 测试超时
**解决**: 增加超时时间或检查服务是否正常
```typescript
// playwright.config.ts
use: {
  actionTimeout: 15000,
  navigationTimeout: 45000,
}
```

### Q2: 元素找不到
**解决**: 使用更宽松的选择器或添加等待
```typescript
// 使用正则匹配
page.getByText(/部分文本/)

// 使用or组合
page.getByRole('button', { name: 'A' }).or(
  page.getByRole('button', { name: 'B' })
)
```

### Q3: 测试数据依赖
**解决**: 使用动态生成的测试数据
```typescript
const testTeacher = {
  username: `teacher_${Date.now()}`,
  name: `测试教师_${Date.now()}`,
};
```

---

**测试框架**: Playwright v1.40+  
**浏览器**: Chromium  
**最后更新**: 2026-04-02
