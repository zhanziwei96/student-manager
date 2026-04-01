# Alembic 数据库迁移

ClassHub 使用 Alembic 管理数据库 schema 变更。

## 快速开始

```bash
# 切换到后端目录
cd backend

# 升级到最新版本
python migrate.py upgrade

# 查看当前版本
python migrate.py current

# 查看迁移历史
python migrate.py history
```

## 命令参考

### 1. 升级数据库

```bash
# 升级到最新版本
python migrate.py upgrade

# 或直接使用 alembic
ENV=development alembic upgrade head
```

### 2. 降级数据库

```bash
# 降级到上一个版本
python migrate.py downgrade

# 或直接使用 alembic
ENV=development alembic downgrade -1
```

### 3. 创建新迁移

当修改了 SQLModel 模型后，创建新的迁移：

```bash
python migrate.py create "add checkin_location table"

# 或直接使用 alembic
ENV=development alembic revision --autogenerate -m "add checkin_location table"
```

创建后请检查 `alembic/versions/` 下的生成文件，确保变更正确。

### 4. 查看迁移状态

```bash
# 当前版本
python migrate.py current

# 迁移历史
python migrate.py history
```

## 环境配置

- **开发环境**: `ENV=development`
- **生产环境**: `ENV=production`

数据库连接从 `app/core/config.py` 自动获取。

## 注意事项

1. **SQLite 限制**: Alembic 对 SQLite 的 ALTER 操作有限制，批量操作使用 `render_as_batch=True`
2. **自动迁移**: `--autogenerate` 可以检测表结构变更，但无法检测所有变更（如约束改名），请人工检查
3. **生产环境**: 生产环境升级前请备份数据库

## 文件结构

```
alembic/
├── env.py              # 迁移环境配置
├── script.py.mako      # 迁移脚本模板
├── versions/           # 迁移脚本目录
│   └── 5bc3d1e6b181_initial_migration.py
└── README.md           # 本文件
```
