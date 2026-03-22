# 班级管理系统前端

基于 Vue 3 + Vite + Naive UI 的前端应用。

## 技术栈

- **Vue**: 3.5+
- **构建工具**: Vite 8+
- **UI 框架**: Naive UI 2.44+
- **状态管理**: Pinia 3.0+
- **路由**: Vue Router 4.5+
- **HTTP 客户端**: Axios 1.8+
- **图标**: @vicons/ionicons5

## 项目结构

```
src/
├── api/              # API 请求
│   ├── index.js      # API 方法
│   └── request.js    # Axios 配置
├── components/       # 公共组件
├── router/           # 路由配置
│   └── index.js
├── stores/           # Pinia 状态管理
│   ├── user.js       # 用户状态
│   └── app.js        # 应用状态
├── utils/            # 工具函数
│   └── index.js
├── views/            # 页面视图
│   ├── Admin.vue     # 管理后台
│   ├── Checkin.vue   # 签到页面
│   ├── Home.vue      # 首页
│   ├── Login.vue     # 登录页
│   └── Student.vue   # 学生页面
├── App.vue
└── main.js
```

## 安装依赖

```bash
pnpm install  # 推荐
# 或
npm install
```

## 启动开发服务器

```bash
pnpm dev      # 推荐
# 或
npm run dev
```

访问 http://localhost:3000

## 构建生产版本

```bash
pnpm build    # 推荐
# 或
npm run build
```

## 开发规范

### UI 组件

项目使用 **Naive UI** 组件库，非 Element Plus：

```vue
<!-- 正确 -->
<n-button type="primary">确定</n-button>
<n-input v-model:value="form.name" placeholder="请输入" />
<n-select v-model:value="form.role" :options="roleOptions" />

<!-- 错误 -->
<el-button type="primary">确定</el-button>
<el-input v-model="form.name" />
```

### API 响应处理

后端统一返回格式：

```javascript
// 成功
{ success: true, data: {...}, message: "..." }

// 失败
{ success: false, message: "错误信息" }
```

前端处理：

```javascript
import { getStudents } from '@/api'

const res = await getStudents()
if (res.success) {
  // 处理 res.data
} else {
  // 处理错误 res.message
}
```

### 路由权限

路由守卫自动检查登录状态，未登录跳转到登录页。

## 相关文档

- [后端 API 文档](../backend/README.md)
- [AI 助手速查手册](../.agents/AGENTS.md)
