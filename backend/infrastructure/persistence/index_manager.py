"""
数据库索引管理器
管理数据库索引的创建、删除和优化
"""
import sqlite3
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from infrastructure.logging import logger


class IndexType(Enum):
    """索引类型"""
    SINGLE = "单列索引"
    COMPOSITE = "复合索引"
    UNIQUE = "唯一索引"


@dataclass
class IndexDefinition:
    """索引定义"""
    name: str
    table: str
    columns: List[str]
    index_type: IndexType = IndexType.SINGLE
    where_clause: Optional[str] = None
    
    @property
    def sql(self) -> str:
        """生成创建索引的 SQL"""
        columns_str = ", ".join(self.columns)
        unique = "UNIQUE " if self.index_type == IndexType.UNIQUE else ""
        
        sql = f"CREATE {unique}INDEX IF NOT EXISTS {self.name} ON {self.table} ({columns_str})"
        
        if self.where_clause:
            sql += f" WHERE {self.where_clause}"
        
        return sql
    
    @property
    def drop_sql(self) -> str:
        """生成删除索引的 SQL"""
        return f"DROP INDEX IF EXISTS {self.name}"


# 推荐的索引配置
# 基于查询模式分析定义
RECOMMENDED_INDEXES: List[IndexDefinition] = [
    # ========== students 表索引 ==========
    # 班级查询（高频：获取某班级学生列表）
    IndexDefinition(
        name="idx_students_class_name",
        table="students",
        columns=["class_name"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 姓名查询（学生搜索功能）
    IndexDefinition(
        name="idx_students_name",
        table="students",
        columns=["name"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 创建时间排序（获取最新学生列表）
    IndexDefinition(
        name="idx_students_created_at",
        table="students",
        columns=["created_at DESC"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 复合索引：班级+创建时间（班级内排序）
    IndexDefinition(
        name="idx_students_class_created",
        table="students",
        columns=["class_name", "created_at DESC"],
        index_type=IndexType.COMPOSITE,
        where_clause=None
    ),
    
    # ========== users 表索引 ==========
    # 角色查询（区分管理员和教师）
    IndexDefinition(
        name="idx_users_role",
        table="users",
        columns=["role"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 活跃状态查询
    IndexDefinition(
        name="idx_users_status",
        table="users",
        columns=["is_active"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 登录时间索引（清理过期会话）
    IndexDefinition(
        name="idx_users_last_login_at",
        table="users",
        columns=["last_login DESC"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 复合索引：角色+活跃状态
    IndexDefinition(
        name="idx_users_role_status",
        table="users",
        columns=["role", "is_active"],
        index_type=IndexType.COMPOSITE,
        where_clause=None
    ),
    
    # ========== checkin_records 表索引 ==========
    # 学生签到查询（高频：查询某学生签到记录）
    IndexDefinition(
        name="idx_checkin_student",
        table="checkin_records",
        columns=["student_id"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 签到时间排序（获取最近签到记录）
    IndexDefinition(
        name="idx_checkin_time",
        table="checkin_records",
        columns=["checkin_time DESC"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 复合索引：学生+签到时间（查询某学生的签到历史）
    IndexDefinition(
        name="idx_checkin_student_time",
        table="checkin_records",
        columns=["student_id", "checkin_time DESC"],
        index_type=IndexType.COMPOSITE,
        where_clause=None
    ),
    
    # ========== score_logs 表索引 ==========
    # 学生分数查询（高频：查询某学生分数变更历史）
    IndexDefinition(
        name="idx_score_logs_student",
        table="score_logs",
        columns=["student_id"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 操作人索引（查询某教师操作记录）
    IndexDefinition(
        name="idx_score_logs_operator",
        table="score_logs",
        columns=["operator"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 创建时间排序（获取最新分数日志）- 支持不同的列名
    IndexDefinition(
        name="idx_score_logs_created_at",
        table="score_logs",
        columns=["created_at DESC"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
    # 复合索引：学生+时间（学生分数历史查询优化）
    IndexDefinition(
        name="idx_score_logs_student_created",
        table="score_logs",
        columns=["student_id", "created_at DESC"],
        index_type=IndexType.COMPOSITE,
        where_clause=None
    ),
    # 兼容旧表结构的索引
    IndexDefinition(
        name="idx_score_logs_operation_time",
        table="score_logs",
        columns=["created_at DESC"],
        index_type=IndexType.SINGLE,
        where_clause=None
    ),
]


class IndexManager:
    """索引管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_existing_indexes(self) -> List[Dict]:
        """获取现有索引列表"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    name,
                    tbl_name as table_name,
                    sql
                FROM sqlite_master
                WHERE type = 'index'
                AND name LIKE 'idx_%'
                ORDER BY tbl_name, name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def analyze_query(self, query: str) -> Dict:
        """分析查询执行计划"""
        with self.get_connection() as conn:
            cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}")
            rows = cursor.fetchall()
            return {
                'plan': [dict(row) for row in rows],
                'uses_index': any('USING INDEX' in str(row) for row in rows)
            }
    
    def create_index(self, index_def: IndexDefinition) -> bool:
        """创建单个索引"""
        try:
            with self.get_connection() as conn:
                conn.execute(index_def.sql)
                conn.commit()
                logger.info(f"Created index: {index_def.name} on {index_def.table}({', '.join(index_def.columns)})")
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to create index {index_def.name}: {e}")
            return False
    
    def drop_index(self, index_name: str) -> bool:
        """删除索引"""
        try:
            with self.get_connection() as conn:
                conn.execute(f"DROP INDEX IF EXISTS {index_name}")
                conn.commit()
                logger.info(f"Dropped index: {index_name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    def create_recommended_indexes(self) -> Dict[str, List[str]]:
        """创建所有推荐的索引"""
        results = {
            'created': [],
            'failed': [],
            'skipped': []
        }
        
        existing_indexes = {idx['name'] for idx in self.get_existing_indexes()}
        
        for index_def in RECOMMENDED_INDEXES:
            if index_def.name in existing_indexes:
                results['skipped'].append(index_def.name)
                continue
            
            if self.create_index(index_def):
                results['created'].append(index_def.name)
            else:
                results['failed'].append(index_def.name)
        
        return results
    
    def drop_all_custom_indexes(self) -> Dict[str, List[str]]:
        """删除所有自定义索引（保留系统自动创建的索引）"""
        results = {
            'dropped': [],
            'failed': []
        }
        
        indexes = self.get_existing_indexes()
        for idx in indexes:
            if self.drop_index(idx['name']):
                results['dropped'].append(idx['name'])
            else:
                results['failed'].append(idx['name'])
        
        return results
    
    def analyze_table(self, table_name: str) -> Dict:
        """分析表统计信息"""
        with self.get_connection() as conn:
            # 获取表行数
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            
            # 获取表索引
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type = 'index' AND tbl_name = ?
            """, (table_name,))
            indexes = [dict(row) for row in cursor.fetchall()]
            
            return {
                'table': table_name,
                'row_count': row_count,
                'indexes': indexes
            }
    
    def optimize_database(self) -> Dict:
        """优化数据库（运行 VACUUM 和 ANALYZE）"""
        results = {}
        
        try:
            with self.get_connection() as conn:
                # 分析表以优化查询计划
                logger.info("Running ANALYZE...")
                conn.execute("ANALYZE")
                results['analyze'] = 'success'
                
                # 整理数据库文件（释放空间）
                logger.info("Running VACUUM...")
                conn.execute("VACUUM")
                results['vacuum'] = 'success'
                
        except sqlite3.Error as e:
            logger.error(f"Database optimization failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_index_usage_stats(self) -> List[Dict]:
        """获取索引使用情况统计（SQLite 3.16+）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        name,
                        path,
                        pageno
                    FROM dbstat
                    WHERE name LIKE 'idx_%'
                    ORDER BY pageno DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            # dbstat 扩展可能未启用
            return []
    
    def get_table_stats(self) -> List[Dict]:
        """获取所有表的统计信息"""
        tables = ['students', 'users', 'checkin_records', 'score_logs']
        return [self.analyze_table(table) for table in tables]


def init_indexes(db_path: str) -> Dict:
    """便捷函数：初始化所有推荐索引"""
    manager = IndexManager(db_path)
    return manager.create_recommended_indexes()


def get_index_report(db_path: str) -> Dict:
    """获取索引报告"""
    manager = IndexManager(db_path)
    
    return {
        'existing_indexes': manager.get_existing_indexes(),
        'table_stats': manager.get_table_stats(),
        'recommended_indexes_count': len(RECOMMENDED_INDEXES)
    }
