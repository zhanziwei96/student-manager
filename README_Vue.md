# 班级管理系统 - Vue 3 + Element Plus 版本

项目已改造为前后端分离架构，前端使用 Vue 3 + Element Plus，后端使用 Flask 提供 API。

## 项目结构

```
student-manage/
├── backend/              # Flask 后端
│   ├── app.py           # 主应用入口
│   ├── data_manager.py  # 数据管理模块
│   ├── requirements.txt # Python 依赖
│   └── data/            # 数据库文件
│
└── frontend/            # Vue 3 前端
    ├── src/
    │   ├── api/         # API 请求封装
    │   ├── components/  # 公共组件
    │   ├── router/      # 路由配置
    │   ├── views/       # 页面组件
    │   │   ├── Login.vue    # 登录页
    │   │   ├── Admin.vue    # 管理后台
    │   │   ├── Checkin.vue  # 签到页面
    │   │   └── Home.vue     # 首页
    │   ├── App.vue
    │   └── main.js
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行后端
python app.py
```

后端将在 http://localhost:5000 运行

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式运行
npm run dev
```

前端将在 http://localhost:3000 运行

### 3. 访问应用

- 首页：http://localhost:3000
- 登录页：http://localhost:3000/login
- 管理后台：http://localhost:3000/admin
- 签到页面：http://localhost:3000/checkin

## 功能特性

### 前端 (Vue 3 + Element Plus)

- **响应式设计**：适配桌面和移动设备
- **组件化架构**：使用 Element Plus 组件库
- **状态管理**：使用 Vue 响应式系统
- **路由管理**：Vue Router 实现页面跳转
- **HTTP 请求**：Axios 封装 API 请求

### 后端 (Flask)

- **RESTful API**：提供标准化接口
- **CORS 支持**：允许跨域访问
- **Session 管理**：用户登录状态
- **数据持久化**：SQLite 数据库

## 默认账号

- 用户名：admin
- 密码：admin123

## API 接口

### 用户相关
- `POST /api/login` - 登录
- `POST /api/logout` - 登出
- `GET /api/me` - 获取当前用户信息
- `POST /api/change-password` - 修改密码

### 学生管理
- `GET /api/students` - 获取所有学生
- `POST /api/students` - 添加学生
- `DELETE /api/students/:id` - 删除学生
- `POST /api/students/:id/score` - 更新分数
- `POST /api/students/import` - 批量导入

### 班级管理
- `DELETE /api/class/:name` - 删除班级

### 签到相关
- `POST /api/checkin` - 学生签到
- `GET /api/checkin/records` - 获取签到记录
- `POST /api/teacher-checkin` - 老师代签

### 上课状态
- `GET /api/class-session` - 获取当前上课状态
- `POST /api/class-session` - 设置上课状态
- `GET /api/class-session/students` - 获取班级学生签到状态

## 开发说明

### 前端开发

```bash
cd frontend
npm run dev      # 开发模式
npm run build    # 构建生产版本
```

### 后端开发

```bash
cd backend
python app.py    # 运行开发服务器
```

## 部署说明

### 前端构建

```bash
cd frontend
npm run build
```

构建后的文件在 `frontend/dist` 目录，可以部署到任何静态服务器。

### 后端部署

使用 Gunicorn 部署 Flask 应用：

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 技术栈

### 前端
- Vue 3 (Composition API)
- Element Plus (UI 组件库)
- Vue Router (路由)
- Axios (HTTP 请求)
- Vite (构建工具)

### 后端
- Flask (Web 框架)
- Flask-CORS (跨域支持)
- SQLite (数据库)
- OpenPyXL (Excel 处理)
