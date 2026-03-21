"""
SQLite分数日志仓储实现
"""
import sqlite3
from typing import List, Optional
from datetime import datetime

from infrastructure.config import PaginationConfig

from domain.entities.score_log import ScoreLog
from infrastructure.persistence.database import Database


class SQLiteScoreLogRepository:
    """SQLite分数日志仓储"""
    
    def __init__(self, db: Database):
        self._db = db
    
    def _row_to_entity(self, row: sqlite3.Row) -> ScoreLog:
        """行转实体"""
        return ScoreLog(
            id=row['id'],
            student_id=row['student_id'],
            student_name='',  # 数据库中没有此列，从应用层填充
            class_name='',     # 数据库中没有此列，从应用层填充
            delta=row['delta'] if row['delta'] is not None else 0.0,
            reason=row['reason'] or '',
            operator_id=None,  # 数据库中没有此列
            operator_name=row['operator'] or '系统',
            created_at=row['created_at']
        )
    
    def save(self, log: ScoreLog) -> ScoreLog:
        """保存日志"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO score_logs
                    (student_id, old_score, new_score, delta, reason, operator, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    log.student_id, None, None, log.delta, log.reason,
                    log.operator_name, log.created_at
                )
            )
            log.id = cursor.lastrowid
            return log
    
    def find_by_student(
        self,
        student_id: str,
        limit: int = PaginationConfig.SCORE_LOG_DEFAULT_LIMIT
    ) -> List[ScoreLog]:
        """查询学生的分数日志"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM score_logs
                   WHERE student_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (student_id, limit)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def find_by_filters(
        self,
        student_id: Optional[str] = None,
        class_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = PaginationConfig.SCORE_LOG_MAX_LIMIT
    ) -> List[ScoreLog]:
        """条件查询日志"""
        query = "SELECT * FROM score_logs WHERE 1=1"
        params = []
        
        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)
        
        if start_date:
            query += " AND date(created_at) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date(created_at) <= ?"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with self._db.connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
