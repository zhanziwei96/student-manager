"""
SQLite签到记录仓储实现
"""
import sqlite3
from datetime import datetime
from typing import List, Optional

from infrastructure.config import ScoreConfig

from domain.entities.checkin import Checkin, CheckinType
from domain.repositories.checkin_repository import CheckinRepository
from infrastructure.persistence.database import Database
from infrastructure.config import PaginationConfig


class SQLiteCheckinRepository(CheckinRepository):
    """SQLite签到记录仓储实现"""
    
    def __init__(self, db: Database):
        self._db = db
    
    def _row_to_entity(self, row: sqlite3.Row) -> Checkin:
        """将数据库行转换为实体"""
        # 从 checkin_time 解析日期和时间
        checkin_time_str = row['checkin_time']
        if checkin_time_str:
            try:
                dt = datetime.fromisoformat(str(checkin_time_str).replace('Z', '+00:00'))
                checkin_date = dt.strftime('%Y-%m-%d')
                checkin_time = dt.strftime('%H:%M:%S')
            except:
                checkin_date = str(checkin_time_str)[:10]
                checkin_time = str(checkin_time_str)[11:19] if len(str(checkin_time_str)) > 10 else '00:00:00'
        else:
            now = datetime.now()
            checkin_date = now.strftime('%Y-%m-%d')
            checkin_time = now.strftime('%H:%M:%S')
        
        # 处理 checkin_type
        checkin_type_val = row['checkin_type'] or 'self'
        if checkin_type_val == 'self':
            checkin_type = CheckinType.SELF
        elif checkin_type_val == 'teacher':
            checkin_type = CheckinType.TEACHER
        else:
            checkin_type = CheckinType.SELF
        
        return Checkin(
            id=row['id'],
            student_id=row['student_id'],
            student_name=row['student_name'] or '',
            class_name=row['class_name'] or '',
            checkin_type=checkin_type,
            checkin_date=checkin_date,
            checkin_time=checkin_time,
            score_delta=ScoreConfig.CHECKIN_SCORE_DELTA,
            created_by=None
        )
    
    def find_by_id(self, checkin_id: int) -> Optional[Checkin]:
        """根据ID查找签到记录"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM checkin_records WHERE id = ?",
                (checkin_id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def find_by_student_and_date(self, student_id: str, date: str) -> Optional[Checkin]:
        """查找学生某天的签到记录"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM checkin_records 
                   WHERE student_id = ? AND date(checkin_time) = ?
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
        limit: int = PaginationConfig.MAX_CHECKIN_RECORDS
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
            query += " AND date(checkin_time) = ?"
            params.append(date)
        
        if start_date:
            query += " AND date(checkin_time) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date(checkin_time) <= ?"
            params.append(end_date)
        
        query += " ORDER BY checkin_time DESC LIMIT ?"
        params.append(limit)
        
        with self._db.connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def find_by_class_today(self, class_name: str) -> List[Checkin]:
        """获取班级今日签到记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.find_by_filters(class_name=class_name, date=today)
    
    def save(self, checkin: Checkin) -> Checkin:
        """保存签到记录"""
        with self._db.connection() as conn:
            # 组合日期和时间
            checkin_datetime = f"{checkin.checkin_date} {checkin.checkin_time}"
            
            if checkin.id:
                # 更新
                conn.execute(
                    """UPDATE checkin_records SET
                        student_id = ?, student_name = ?, class_name = ?,
                        checkin_type = ?, checkin_time = ?
                       WHERE id = ?""",
                    (
                        checkin.student_id, checkin.student_name, checkin.class_name,
                        checkin.checkin_type.value, checkin_datetime, checkin.id
                    )
                )
            else:
                # 插入
                cursor = conn.execute(
                    """INSERT INTO checkin_records
                        (student_id, student_name, class_name, checkin_type, checkin_time)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        checkin.student_id, checkin.student_name, checkin.class_name,
                        checkin.checkin_type.value, checkin_datetime
                    )
                )
                checkin.id = cursor.lastrowid
            
            return checkin
    
    def count_by_student_and_date_range(
        self,
        student_id: str,
        start_date: str,
        end_date: str
    ) -> int:
        """统计学生在日期范围内的签到次数"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """SELECT COUNT(*) as count FROM checkin_records
                   WHERE student_id = ? AND date(checkin_time) >= ? AND date(checkin_time) <= ?""",
                (student_id, start_date, end_date)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def count_by_class_and_date(self, class_name: str, date: str) -> int:
        """统计班级某天的签到人数"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """SELECT COUNT(DISTINCT student_id) as count FROM checkin_records
                   WHERE class_name = ? AND date(checkin_time) = ?""",
                (class_name, date)
            )
            row = cursor.fetchone()
            return row['count'] if row else 0
