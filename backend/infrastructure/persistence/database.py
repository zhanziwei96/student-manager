"""
数据库连接管理
提供连接池和上下文管理器支持
"""
import sqlite3
import logging
from typing import Optional
from contextlib import contextmanager

from infrastructure.config import get_db_settings
from infrastructure.persistence.connection_pool import get_connection_pool, ConnectionPool

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接上下文管理器
    
    确保连接在使用后被正确关闭，即使在发生异常时也能保证资源释放。
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        """进入上下文，创建并返回数据库连接"""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，确保连接被关闭"""
        if self._conn:
            try:
                if exc_type is None:
                    # 无异常，提交事务
                    self._conn.commit()
                else:
                    # 发生异常，回滚事务
                    self._conn.rollback()
                    logger.warning(f"事务回滚 due to {exc_type.__name__}: {exc_val}")
            finally:
                # 确保连接被关闭
                self._conn.close()
                self._conn = None
        # 不抑制异常，继续传播
        return False


class Database:
    """数据库连接管理器
    
    提供线程安全的数据库连接管理，支持连接池模式。
    """
    
    def __init__(self, db_path: str = None, use_pool: bool = True):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库路径，默认从配置获取
            use_pool: 是否使用连接池，默认 True
        """
        if db_path is None:
            # 从配置获取数据库路径
            settings = get_db_settings()
            self.db_path = settings.path
        else:
            self.db_path = db_path
        
        self.use_pool = use_pool
        self._pool: Optional[ConnectionPool] = None
        
        # 确保目录存在（不适用于内存数据库）
        if self.db_path != ':memory:':
            import os
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        
        logger.debug(f"Database initialized: {self.db_path}, use_pool={use_pool}")
    
    def _get_pool(self) -> ConnectionPool:
        """获取连接池实例"""
        if self._pool is None:
            self._pool = get_connection_pool(self.db_path)
        return self._pool
    
    def get_connection(self) -> sqlite3.Connection:
        """获取原始数据库连接（不推荐直接使用）
        
        警告：使用此方法需要手动管理连接生命周期（调用 close()）。
        推荐使用 connection() 上下文管理器。
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def connection(self):
        """获取数据库连接上下文管理器（推荐）
        
        使用示例：
            with db.connection() as conn:
                cursor = conn.execute("SELECT * FROM students")
                rows = cursor.fetchall()
        
        Returns:
            DatabaseConnection 或 ConnectionPool: 连接上下文管理器
        """
        if self.use_pool:
            return self._get_pool().connection()
        else:
            return DatabaseConnection(self.db_path)
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器
        
        用于需要显式控制事务的场景。
        
        使用示例：
            with db.transaction() as conn:
                conn.execute("INSERT INTO ...")
                conn.execute("UPDATE ...")
                # 事务在退出时自动提交，异常时自动回滚
        """
        if self.use_pool:
            with self._get_pool().connection() as conn:
                yield conn
        else:
            conn = None
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
                logger.debug("Transaction committed")
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Transaction rolled back due to: {e}")
                raise
            finally:
                if conn:
                    conn.close()
    
    def init_tables(self) -> None:
        """初始化数据库表结构"""
        with self.connection() as conn:
            cursor = conn.cursor()
            
            # 学生表 - 使用 student_id 作为主键
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    class_name TEXT DEFAULT '未分班',
                    score REAL DEFAULT 70.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    name TEXT,
                    role TEXT DEFAULT 'teacher',
                    assigned_class TEXT,
                    is_active INTEGER DEFAULT 1,
                    login_fail_count INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    last_login_ip TEXT,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 签到记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkin_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    student_name TEXT,
                    class_name TEXT,
                    checkin_type TEXT DEFAULT 'self',
                    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 分数变更日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS score_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    old_score REAL,
                    new_score REAL,
                    delta REAL,
                    reason TEXT,
                    operator TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("Database tables initialized successfully")
    
    def run_migrations(self) -> None:
        """运行数据库迁移"""
        from infrastructure.persistence.migration_manager import MigrationManager
        
        manager = MigrationManager(self.db_path)
        results = manager.migrate()
        
        if results['applied']:
            logger.info(f"Applied {len(results['applied'])} migrations: {results['applied']}")
        
        if results['failed']:
            logger.error(f"Failed migrations: {results['failed']}")
    
    def init_indexes(self) -> None:
        """初始化数据库索引"""
        from infrastructure.persistence.index_manager import IndexManager, RECOMMENDED_INDEXES
        
        with self.connection() as conn:
            existing_indexes = set()
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type = 'index' AND name LIKE 'idx_%'
            """)
            for row in cursor.fetchall():
                existing_indexes.add(row['name'])
            
            created_count = 0
            failed_indexes = []
            for index_def in RECOMMENDED_INDEXES:
                if index_def.name not in existing_indexes:
                    try:
                        conn.execute(index_def.sql)
                        created_count += 1
                        logger.debug(f"Created index: {index_def.name}")
                    except sqlite3.Error as e:
                        failed_indexes.append((index_def.name, str(e)))
            
            if created_count > 0:
                logger.info(f"Created {created_count} database indexes")
            
            if failed_indexes:
                for name, error in failed_indexes:
                    logger.warning(f"Failed to create index {name}: {error}")
            elif created_count == 0:
                logger.debug("All indexes already exist")
    
    def get_pool_stats(self) -> dict:
        """获取连接池统计信息"""
        if self.use_pool and self._pool:
            return self._pool.get_stats()
        return {'use_pool': self.use_pool}
