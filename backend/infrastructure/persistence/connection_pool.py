"""
SQLite 数据库连接池
提供线程安全的连接复用机制
"""
import sqlite3
import threading
import queue
import logging
from typing import Optional
from contextlib import contextmanager

from infrastructure.config import get_db_settings

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    SQLite 数据库连接池
    
    特性：
    - 线程安全的连接获取和释放
    - 连接复用，减少创建开销
    - 自动连接健康检查
    - 支持上下文管理器
    """
    
    def __init__(
        self,
        db_path: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        timeout: int = 30
    ):
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        
        # 连接池队列
        self._pool = queue.Queue(maxsize=pool_size)
        self._overflow_count = 0
        self._lock = threading.Lock()
        self._closed = False
        
        # 初始化连接池
        self._init_pool()
    
    def _init_pool(self) -> None:
        """初始化连接池，创建基础连接"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
        logger.info(f"Connection pool initialized: {self.db_path}, size={self.pool_size}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """创建新连接"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                check_same_thread=False  # 允许跨线程使用
            )
            conn.row_factory = sqlite3.Row
            # 启用 WAL 模式提高并发性能
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """检查连接是否有效"""
        try:
            conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """
        从连接池获取连接
        
        Returns:
            sqlite3.Connection: 数据库连接，如果池已满则返回 None
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        try:
            # 尝试从池中获取连接
            conn = self._pool.get(timeout=self.timeout)
            
            # 检查连接是否有效
            if not self._is_connection_valid(conn):
                logger.debug("Connection invalid, creating new one")
                conn = self._create_connection()
            
            return conn
            
        except queue.Empty:
            # 池已空，尝试创建溢出连接
            with self._lock:
                if self._overflow_count < self.max_overflow:
                    conn = self._create_connection()
                    if conn:
                        self._overflow_count += 1
                        logger.debug(f"Created overflow connection: {self._overflow_count}/{self.max_overflow}")
                        return conn
            
            logger.warning("Connection pool exhausted")
            return None
    
    def release_connection(self, conn: sqlite3.Connection) -> None:
        """
        释放连接回连接池
        
        Args:
            conn: 要释放的数据库连接
        """
        if self._closed:
            conn.close()
            return
        
        if not self._is_connection_valid(conn):
            conn.close()
            with self._lock:
                if self._overflow_count > 0:
                    self._overflow_count -= 1
            return
        
        try:
            # 尝试放回池中
            self._pool.put(conn, block=False)
        except queue.Full:
            # 池已满，关闭连接
            conn.close()
            with self._lock:
                if self._overflow_count > 0:
                    self._overflow_count -= 1
    
    @contextmanager
    def connection(self):
        """
        连接上下文管理器
        
        使用示例：
            with pool.connection() as conn:
                cursor = conn.execute("SELECT * FROM students")
                rows = cursor.fetchall()
        """
        conn = self.get_connection()
        if conn is None:
            raise RuntimeError("Failed to get connection from pool")
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.release_connection(conn)
    
    def close(self) -> None:
        """关闭连接池，释放所有连接"""
        self._closed = True
        
        # 关闭池中的所有连接
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except (queue.Empty, sqlite3.Error):
                pass
        
        logger.info("Connection pool closed")
    
    def get_stats(self) -> dict:
        """获取连接池统计信息"""
        return {
            'pool_size': self.pool_size,
            'available': self._pool.qsize(),
            'max_overflow': self.max_overflow,
            'current_overflow': self._overflow_count,
            'closed': self._closed
        }


# 全局连接池实例
_pool_instance: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(db_path: str = None) -> ConnectionPool:
    """
    获取全局连接池实例（单例）
    
    Args:
        db_path: 数据库路径，默认从配置获取
        
    Returns:
        ConnectionPool: 连接池实例
    """
    global _pool_instance
    
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                settings = get_db_settings()
                if db_path is None:
                    db_path = settings.path
                
                _pool_instance = ConnectionPool(
                    db_path=db_path,
                    pool_size=settings.pool_size,
                    max_overflow=settings.max_overflow,
                    timeout=settings.timeout
                )
    
    return _pool_instance


def close_connection_pool() -> None:
    """关闭全局连接池"""
    global _pool_instance
    
    if _pool_instance is not None:
        _pool_instance.close()
        _pool_instance = None


def reset_connection_pool() -> ConnectionPool:
    """重置连接池（用于配置变更后）"""
    close_connection_pool()
    return get_connection_pool()
