# ClassHub E2E 功能测试方案

## 测试环境

- **前端地址**: http://localhost:5175
- **后端地址**: http://localhost:8000
- **测试框架**: Playwright

## 已探索功能

### 1. 首页 (Landing Page)
- 导航栏：Logo、登录按钮、开始使用按钮
- Hero 区域：标题、描述、CTA 按钮
- 功能卡片：学生管理、实时分析、课堂签到

### 2. 登录页 (Login Page)
- 角色选择：管理员/教师/学生
- 表单：用户名、密码输入
- 登录按钮

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

## 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | zhanziwei | zha123 |
| 学生 | 2513070102 | 2513070102 |

## 测试脚本

详见以下测试文件：
- `login.spec.ts` - 登录模块测试
- `admin.spec.ts` - 管理员功能测试
- `teacher.spec.ts` - 教师功能测试
- `student.spec.ts` - 学生功能测试

## 运行测试

```bash
# 安装依赖
npm install -D @playwright/test

# 安装浏览器
npx playwright install

# 运行所有测试
npx playwright test

# 运行特定测试
npx playwright test login.spec.ts

# 带 UI 模式
npx playwright test --ui
```

## 截图记录

测试过程中会生成以下截图：
- `screenshots/01-homepage.png` - 首页
- `screenshots/02-login-page.png` - 登录页
- `screenshots/03-admin-dashboard.png` - 管理仪表板
- `screenshots/04-admin-students.png` - 学生管理页
