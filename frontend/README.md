# 班级管理系统前端

## 项目结构

```
src/
├── api/           # API 请求
│   ├── index.js
│   └── request.js
├── components/    # 公共组件
├── router/        # 路由配置
│   └── index.js
├── utils/         # 工具函数
│   └── index.js
├── views/         # 页面视图
│   ├── Admin.vue      # 管理后台
│   ├── Checkin.vue    # 签到页面
│   ├── Home.vue       # 首页
│   └── Login.vue      # 登录页
├── App.vue
└── main.js
```

## 安装依赖

```bash
npm install
```

## 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 构建生产版本

```bash
npm run build
```

## 主要修复内容

1. **main.js** - 移除了中文语言包导入（使用默认英文）
2. **router/index.js** - 移除了路由守卫中的 ElMessage 调用
3. **图标引用** - 修复为字符串形式（如 `prefix-icon="User"`）
4. **组件导入** - 从 main.js 全局注册所有图标组件

## 依赖说明

- Vue 3.4+
- Element Plus 2.5+
- Vue Router 4.2+
- Axios 1.6+
- js-cookie 3.0+
