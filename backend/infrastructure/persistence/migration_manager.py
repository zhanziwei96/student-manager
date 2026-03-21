"""
数据库迁移管理器
管理数据库表结构的版本控制和迁移
"""
import sqlite3
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from infrastructure.logging import logger


@dataclass
class Migration:
    """迁移定义"""
    version: int
    name: str
    description: str
    up_sql: str
    down_sql: Optional[str] = None


class MigrationManager:
    """数据库迁移管理器"""
    
    # 当前数据库版本
    CURRENT_VERSION = 1
    
    # 迁移历史记录
    MIGRATIONS: List[Migration] = [
        # 可以根据需要添加更多迁移
        # 注意：SQLite 的 ALTER TABLE 功能有限，某些修改可能需要重建表
    ]
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_migration_table()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_migration_table(self) -> None:
        """初始化迁移历史表"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get_current_version(self) -> int:
        """获取当前数据库版本"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT MAX(version) as version FROM schema_migrations"
            )
            row = cursor.fetchone()
            return row['version'] or 0
    
    def get_applied_migrations(self) -> List[Dict]:
        """获取已应用的迁移列表"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM schema_migrations ORDER BY version"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def is_migration_applied(self, version: int) -> bool:
        """检查迁移是否已应用"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,)
            )
            return cursor.fetchone() is not None
    
    def apply_migration(self, migration: Migration) -> bool:
        """应用单个迁移"""
        if self.is_migration_applied(migration.version):
            logger.debug(f"Migration {migration.version} already applied")
            return True
        
        try:
            with self.get_connection() as conn:
                # 执行迁移 SQL
                conn.executescript(migration.up_sql)
                
                # 记录迁移
                conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (migration.version, migration.name)
                )
                
                conn.commit()
                
                logger.info(f"Applied migration {migration.version}: {migration.name}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            return False
    
    def migrate(self) -> Dict[str, List]:
        """执行所有待处理的迁移"""
        results = {
            'applied': [],
            'skipped': [],
            'failed': []
        }
        
        current_version = self.get_current_version()
        
        for migration in self.MIGRATIONS:
            if migration.version <= current_version:
                results['skipped'].append(migration.version)
                continue
            
            if self.apply_migration(migration):
                results['applied'].append(migration.version)
            else:
                results['failed'].append(migration.version)
                # 失败后停止
                break
        
        return results
    
    def rollback(self, version: int) -> bool:
        """回滚到指定版本"""
        # 查找对应迁移
        migration = None
        for m in self.MIGRATIONS:
            if m.version == version:
                migration = m
                break
        
        if not migration:
            logger.error(f"Migration version {version} not found")
            return False
        
        if not migration.down_sql:
            logger.error(f"Migration {version} has no rollback script")
            return False
        
        try:
            with self.get_connection() as conn:
                conn.executescript(migration.down_sql)
                conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?",
                    (version,)
                )
                conn.commit()
                
                logger.info(f"Rolled back migration {version}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
    
    def get_migration_status(self) -> Dict:
        """获取迁移状态"""
        current_version = self.get_current_version()
        applied = self.get_applied_migrations()
        
        pending = [
            m for m in self.MIGRATIONS 
            if m.version > current_version
        ]
        
        return {
            'current_version': current_version,
            'latest_version': max(m.version for m in self.MIGRATIONS) if self.MIGRATIONS else 0,
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied': [dict(version=m['version'], name=m['name'], applied_at=m['applied_at']) 
                       for m in applied],
            'pending': [dict(version=m.version, name=m.name) for m in pending]
        }
    
    def validate_schema(self) -> Dict[str, List[str]]:
        """验证数据库结构完整性"""
        issues = {
            'missing_tables': [],
            'missing_columns': [],
            'warnings': []
        }
        
        # 根据实际数据库结构定义必需的表和列
        required_tables = {
            'students': ['student_id', 'name', 'class_name', 'score', 'created_at'],
            'users': ['id', 'username', 'password_hash', 'salt', 'name', 'role', 'assigned_class', 'is_active', 'created_at'],
            'checkin_records': ['id', 'student_id', 'student_name', 'class_name', 'checkin_type', 'checkin_time'],
            'score_logs': ['id', 'student_id', 'old_score', 'new_score', 'delta', 'reason', 'operator', 'created_at'],
        }
        
        with self.get_connection() as conn:
            for table, columns in required_tables.items():
                # 检查表是否存在
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if not cursor.fetchone():
                    issues['missing_tables'].append(table)
                    continue
                
                # 检查列是否存在
                cursor = conn.execute(f"PRAGMA table_info({table})")
                existing_columns = {row['name'] for row in cursor.fetchall()}
                
                for col in columns:
                    if col not in existing_columns:
                        issues['missing_columns'].append(f"{table}.{col}")
        
        return issues


def run_migrations(db_path: str) -> Dict:
    """便捷函数：运行所有迁移"""
    manager = MigrationManager(db_path)
    return manager.migrate()


def get_migration_report(db_path: str) -> Dict:
    """获取迁移报告"""
    manager = MigrationManager(db_path)
    return {
        'status': manager.get_migration_status(),
        'schema_issues': manager.validate_schema()
    }
