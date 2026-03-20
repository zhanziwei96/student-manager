"""
数据库连接管理
"""
import sqlite3
import os
from typing import Optional


class Database:
    """数据库连接管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认路径：项目根目录/data/class_system.db
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.db_path = os.path.join(base_dir, 'data', 'class_system.db')
        else:
            self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self) -> None:
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 学生表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_name TEXT DEFAULT '未分班',
                score REAL DEFAULT 70,
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
                name TEXT NOT NULL,
                role TEXT DEFAULT 'teacher',
                assigned_classes TEXT,
                status TEXT DEFAULT 'active',
                login_fail_count INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                last_login_ip TEXT,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 签到记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
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
        
        conn.commit()
        conn.close()
