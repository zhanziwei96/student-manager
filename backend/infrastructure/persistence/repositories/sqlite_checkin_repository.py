"""
SQLite签到记录仓储实现
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from domain.entities.checkin import Checkin, CheckinType
from domain.repositories.checkin_repository import CheckinRepository
from infrastructure.persistence.database import Database


class SQLiteCheckinRepository(CheckinRepository):
    """SQLite签到记录仓储实现"""
    
    def __init__(self, db: Database):
        self._db = db
    
    def _row_to_entity(self, row: sqlite3.Row) -> Checkin:
        """将数据库行转换为实体"""
        return Checkin(
            id=row['id'],
            student_id=row['student_id'],
            student_name=row['student_name'],
            class_name=row['class_name'],
            checkin_type=CheckinType(row['checkin_type']) if row['checkin_type'] else CheckinType.SELF,
            checkin_date=row['checkin_date'],
            checkin_time=row['checkin_time'],
            score_delta=row.get('score_delta', 0.0),
            created_by=row.get('created_by')
        )
    
    def find_by_id(self, checkin_id: int) -> Optional[Checkin]:
        """根据ID查找签到记录"""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM checkin_records WHERE id = ?",
                (checkin_id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def find_by_student_and_date(self, student_id: str, date: str) -> Optional[Checkin]:
        """查找学生某天的签到记录"""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM checkin_records 
                   WHERE student_id = ? AND checkin_date = ?
                   ORDER BY checkin_time DESC LIMIT 1""",
                (student_id, date)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def find_by_filters(
        self,
        student_id: Optional[str] = None,
        class_name: Optional[str] = None,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Checkin]:
        """根据条件查询签到记录"""
        query = "SELECT * FROM checkin_records WHERE 1=1"
        params = []
        
        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)
        
        if class_name:
            query += " AND class_name = ?"
            params.append(class_name)
        
        if date:
            query += " AND checkin_date = ?"
            params.append(date)
        
        if start_date:
            query += " AND checkin_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND checkin_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY checkin_date DESC, checkin_time DESC LIMIT ?"
        params.append(limit)
        
        with self._db.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def find_by_class_today(self, class_name: str) -> List[Checkin]:
        """获取班级今日签到记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.find_by_filters(class_name=class_name, date=today)
    
    def save(self, checkin: Checkin) -> Checkin:
        """保存签到记录"""
        with self._db.get_connection() as conn:
            if checkin.id:
                # 更新
                conn.execute(
                    """UPDATE checkin_records SET
                        student_id = ?, student_name = ?, class_name = ?,
                        checkin_type = ?, checkin_date = ?, checkin_time = ?,
                        score_delta = ?, created_by = ?
                       WHERE id = ?""",
                    (
                        checkin.student_id, checkin.student_name, checkin.class_name,
                        checkin.checkin_type.value, checkin.checkin_date, checkin.checkin_time,
                        checkin.score_delta, checkin.created_by, checkin.id
                    )
                )
            else:
                # 插入
                cursor = conn.execute(
                    """INSERT INTO checkin_records
                        (student_id, student_name, class_name, checkin_type,
                         checkin_date, checkin_time, score_delta, created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        checkin.student_id, checkin.student_name, checkin.class_name,
                        checkin.checkin_type.value, checkin.checkin_date, checkin.checkin_time,
                        checkin.score_delta, checkin.created_by
                    )
                )
                checkin.id = cursor.lastrowid
            
            conn.commit()
            return checkin
    
    def count_by_student_and_date_range(
        self,
        student_id: str,
        start_date: str,
        end_date: str
    ) -> int:
        """统计学生在日期范围内的签到次数"""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """SELECT COUNT(*) as count FROM checkin_records
                   WHERE student_id = ? AND checkin_date >= ? AND checkin_date <= ?""",
                (student_id, start_date, end_date)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def count_by_class_and_date(self, class_name: str, date: str) -> int:
        """统计班级某天的签到人数"""
        with self._db.get_connection() as conn:
            cursor = conn.execute(
                """SELECT COUNT(DISTINCT student_id) as count FROM checkin_records
                   WHERE class_name = ? AND checkin_date = ?""",
                (class_name, date)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
