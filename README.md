# 📚 班级管理系统

一个简单易用的班级管理系统，支持网页表单签到、班级导入、分数增减功能，所有数据使用 SQLite 数据库存储，管理后台需要老师登录才能访问。

## ✨ 功能特性

- **👥 学生管理**：添加、删除、查看学生信息
- **📁 班级导入**：从 CSV 文件批量导入学生名单
- **📝 网页签到**：学生打开网页输入学号和姓名即可完成签到
- **📊 分数管理**：给学生增减分数，记录变更历史
- **🔐 老师登录**：管理后台需要登录才能访问，支持修改密码
- **📈 数据统计**：查看排行榜、签到记录、分数日志
- **💾 SQLite 存储**：数据保存在 SQLite 数据库中，高效可靠
- **⚡ 并发优化**：支持多学生同时签到，不卡顿

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask
```

### 2. 启动系统

```bash
python app.py
```

### 3. 访问系统

打开浏览器访问：http://127.0.0.1:5000

## 🗄️ 测试环境与生产环境

系统支持两个独立的数据库环境，方便测试和正式使用分离。

### 环境说明

| 环境 | 数据库文件 | 用途 |
|------|-----------|------|
| 生产环境 | `data/class_system.db` | 正式使用，保存真实数据 |
| 测试环境 | `data/test_class_system.db` | 测试功能，可随意操作 |

### 启动方式

**Windows (PowerShell):**
```powershell
# 启动生产环境（默认）
.\start_server.ps1

# 启动测试环境
.\start_server.ps1 -Test
```

**Windows (CMD):**
```cmd
# 生产环境
start_prod.bat

# 测试环境
start_test.bat
```

**Linux / Mac:**
```bash
# 首次使用需要添加执行权限
chmod +x start_server.sh start_prod.sh start_test.sh

# 启动生产环境（默认）
./start_server.sh
# 或
./start_prod.sh

# 启动测试环境
./start_server.sh test
# 或
./start_test.sh
```

**命令行方式:**
```bash
# 生产环境（默认）
python app.py

# 或显式指定
set FLASK_ENV=production  # Windows
export FLASK_ENV=production  # Linux/Mac
python app.py

# 测试环境
set FLASK_ENV=testing  # Windows
export FLASK_ENV=testing  # Linux/Mac
python app.py
```

### 环境标识

在管理后台右上角会显示当前环境标识：
- 🟢 **绿色**：生产环境
- 🟡 **黄色**：测试环境

鼠标悬停在标识上可查看具体的数据库文件路径。

## 📖 使用指南

### 老师登录

**登录地址**：http://127.0.0.1:5000/login

**默认账户**：
- 用户名：`admin`
- 密码：`admin123`

首次登录后建议修改密码。

### 上课模式

1. 在管理后台选择要上课的班级，点击"开始上课"
2. 系统会实时显示该班级的签到统计
3. 学生打开签到页面后，可以看到班级所有学生的签到状态：
   - 红色：未签到
   - 绿色：已签到
4. 学生签到后，名单会实时更新（每 3 秒自动刷新）
5. 上课结束后点击"结束上课"

### 管理后台

访问 http://127.0.0.1:5000/admin（需要登录）

- **添加学生**：填写学号、姓名、班级，添加单个学生
- **导入班级**：上传 Excel 文件（.xlsx/.xls），支持按列名自动识别
- **删除班级**：一键删除整个班级的所有学生
- **分数管理**：点击学生列表中的「分数」按钮，调整学生分数
- **查看记录**：查看签到记录和分数变更日志
- **修改密码**：点击右上角「修改密码」按钮
- **退出登录**：点击右上角「退出登录」按钮

### 学生签到

**签到地址**：http://127.0.0.1:5000/checkin

**签到流程**：
1. 学生打开手机或电脑浏览器
2. 访问签到页面
3. 输入自己的**学号**和**姓名**
4. 点击「立即签到」按钮
5. 签到成功！

**一机一签限制**：
- 每台电脑/浏览器**今天只能签到一次**
- 签到成功后页面会显示「已完成签到」
- 刷新页面也无法再次签到
- 如需让其他学生签到，需要点击「重置签到状态」并输入管理员密码
- 每天凌晨自动重置，学生可以重新签到

**注意事项**：
- 学号和姓名必须与系统中登记的一致
- 支持多台设备同时签到（但每台设备限签一人）
- 签到成功后会显示在最近的签到记录中

### 导入 Excel 格式

支持 .xlsx 和 .xls 格式的 Excel 文件，按表头列名自动识别：

**必须包含的列（不固定顺序）：**
- **学号** - 支持关键词：学号/学生号/id/编号/studentid
- **姓名** - 支持关键词：姓名/名字/学生姓名/name

**可选的列：**
- **班级** - 支持关键词：班级/班级名称/class/classname

**示例：**

| 学号 | 姓名 | 班级 |
|------|------|------|
| 2024001 | 张三 | 一班 |
| 2024002 | 李四 | 一班 |
| 2024003 | 王五 | 二班 |

**也可以这样（列顺序不固定）：**

| 姓名 | 班级 | 学号 |
|------|------|------|
| 张三 | 一班 | 2024001 |
| 李四 | 一班 | 2024002 |
| 王五 | 二班 | 2024003 |

**注意：**
- 第一行必须是表头，系统会根据关键词自动识别
- 如果没有班级列，可以在导入时设置默认班级
- 不支持合并单元格

## 🔐 登录功能说明

### 安全特性

1. **密码加密存储**：使用 PBKDF2 算法对密码进行哈希加密
2. **Session 管理**：使用 Flask session 管理登录状态，有效期 1 小时
3. **访问控制**：管理后台相关 API 需要登录才能访问
4. **姓名验证**：签到时验证学号和姓名是否匹配，防止误签

### 修改密码

1. 登录后进入管理后台
2. 点击右上角「修改密码」按钮
3. 输入原密码和新密码
4. 修改成功后需要重新登录

## 🔧 并发优化说明

为了支持多学生同时签到，系统做了以下优化：

### 1. SQLite WAL 模式
- 启用 Write-Ahead Logging 模式
- 支持读写并发，写入不阻塞读取
- 大大提高并发写入性能

### 2. 数据库连接优化
- 每个线程独立的数据库连接
- 10 秒超时等待锁释放
- 64MB 缓存提高查询速度

### 3. 前端请求队列
- 签到请求排队处理，避免同时发送过多请求
- 请求间隔 100ms，减轻服务器压力
- 10 秒请求超时处理

### 4. 多线程服务器
- Flask 启用 threaded=True
- 每个请求独立线程处理
- 支持并发处理多个签到请求

## 📁 数据存储

所有数据存储在项目目录的 `data/` 文件夹中：

| 文件 | 说明 |
|------|------|
| `class_system.db` | SQLite 数据库文件，包含所有数据 |
| `class_system.db-shm` | WAL 模式共享内存文件（自动生成） |
| `class_system.db-wal` | WAL 模式日志文件（自动生成） |

### 数据库表结构

**users 表** - 老师账户
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,   -- 用户名
    password_hash TEXT NOT NULL,      -- 密码哈希
    salt TEXT NOT NULL,               -- 密码盐值
    name TEXT NOT NULL,               -- 显示名称
    is_admin INTEGER DEFAULT 1,       -- 是否管理员
    created_at TIMESTAMP,             -- 创建时间
    last_login TIMESTAMP              -- 最后登录时间
);
```

**students 表** - 学生信息
```sql
CREATE TABLE students (
    student_id TEXT PRIMARY KEY,      -- 学号
    name TEXT NOT NULL,                -- 姓名
    class_name TEXT DEFAULT '未分班',  -- 班级
    score INTEGER DEFAULT 0,           -- 当前分数
    created_at TIMESTAMP               -- 创建时间
);
```

**checkin_records 表** - 签到记录
```sql
CREATE TABLE checkin_records (
    record_id TEXT PRIMARY KEY,       -- 记录ID
    student_id TEXT NOT NULL,         -- 学号（外键）
    checkin_time TIMESTAMP,           -- 签到时间
    checkin_type TEXT                 -- 签到类型（网页签到）
);
```

**score_logs 表** - 分数变更日志
```sql
CREATE TABLE score_logs (
    log_id TEXT PRIMARY KEY,          -- 日志ID
    student_id TEXT NOT NULL,         -- 学号（外键）
    score_change INTEGER NOT NULL,    -- 分数变更
    reason TEXT,                      -- 变更原因
    operation_time TIMESTAMP          -- 操作时间
);
```

## 💾 数据备份

直接复制 `data/class_system.db` 文件即可备份。

如需导出为 CSV：
```bash
# 使用 sqlite3 命令行工具
sqlite3 data/class_system.db
.mode csv
.output students.csv
SELECT * FROM students;
.output stdout
.exit
```

## 🛠️ 技术栈

- **后端**：Python Flask
- **数据库**：SQLite（Python 内置）
- **前端**：原生 HTML + JavaScript
- **安全**：PBKDF2 密码哈希，Session 管理
- **并发优化**：SQLite WAL 模式 + 多线程

## 📱 使用场景

1. **课堂签到**：老师在教室屏幕上展示签到页面地址，学生用手机访问并签到
2. **活动签到**：活动开始前导入参与人员名单，现场签到统计人数
3. **考勤管理**：结合分数系统，对迟到、早退等情况进行扣分

## 🔒 安全说明

1. **密码安全**：使用 PBKDF2 算法进行 100000 次迭代哈希
2. **Session 安全**：24 字节随机密钥，1 小时有效期
3. **数据持久化**：SQLite 数据库自动持久化，程序重启数据不丢失
4. **并发安全**：WAL 模式保证多用户同时写入数据一致性

## 📄 许可

MIT License
