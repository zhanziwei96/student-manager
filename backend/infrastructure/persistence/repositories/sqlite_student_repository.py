"""
SQLite 学生仓储实现
"""
from typing import List, Optional
import sqlite3
from domain.entities.student import Student
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from domain.repositories.student_repository import StudentRepository
from infrastructure.persistence.database import Database


class SQLiteStudentRepository(StudentRepository):
    """SQLite 学生仓储实现"""
    
    def __init__(self, database: Database):
        self.db = database
    
    def _row_to_entity(self, row: sqlite3.Row) -> Student:
        """将数据行转换为领域实体"""
        return Student(
            id=None,  # 学生表使用 student_id 作为主键，没有自增ID
            student_id=StudentId(row['student_id']),
            name=row['name'],
            class_name=row['class_name'] or '未分班',
            score=Score(float(row['score']) if row['score'] is not None else 70.0),
            created_at=row['created_at']
        )
    
    def find_by_id(self, student_id: StudentId) -> Optional[Student]:
        """根据StudentId值对象查找"""
        return self.find_by_id_str(str(student_id))
    
    def find_by_id_str(self, student_id: str) -> Optional[Student]:
        """根据学号字符串查找"""
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE student_id = ?",
                (student_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    def find_all(self) -> List[Student]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            # 按 created_at 降序，相同时间按 student_id 升序确保稳定排序
            cursor.execute("SELECT * FROM students ORDER BY created_at DESC, student_id ASC")
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def find_by_class(self, class_name: str) -> List[Student]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE class_name = ? ORDER BY student_id",
                (class_name,)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def find_by_name(self, name: str) -> List[Student]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE name LIKE ?",
                (f"%{name}%",)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def save(self, student: Student) -> None:
        from datetime import datetime
        
        with self.db.connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (str(student.student_id),))
            exists = cursor.fetchone() is not None
            
            if exists:
                # 更新
                cursor.execute('''
                    UPDATE students 
                    SET name = ?, class_name = ?, score = ?
                    WHERE student_id = ?
                ''', (
                    student.name,
                    student.class_name,
                    float(student.score),
                    str(student.student_id)
                ))
            else:
                # 新增 - 使用微秒级时间戳确保排序稳定
                created_at = datetime.now().isoformat(timespec='microseconds')
                cursor.execute('''
                    INSERT INTO students (student_id, name, class_name, score, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    str(student.student_id),
                    student.name,
                    student.class_name,
                    float(student.score),
                    created_at
                ))
    
    def delete(self, student_id: StudentId) -> None:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM students WHERE student_id = ?",
                (str(student_id),)
            )
    
    def exists(self, student_id: StudentId) -> bool:
        return self.find_by_id(student_id) is not None
    
    def set_password(self, student_id: str, password_hash: str, salt: str) -> None:
        """设置学生密码"""
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE students 
                SET password_hash = ?, salt = ?
                WHERE student_id = ?
            ''', (password_hash, salt, student_id))
    
    def reset_password(self, student_id: str, new_password: str) -> bool:
        """重置学生密码，返回是否成功"""
        import hashlib
        import secrets
        
        # 检查学生是否存在
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
            if not cursor.fetchone():
                return False
            
            # 生成新密码
            salt = secrets.token_hex(16)
            password_hash = hashlib.sha256(f"{new_password}{salt}".encode()).hexdigest()
            
            cursor.execute('''
                UPDATE students 
                SET password_hash = ?, salt = ?
                WHERE student_id = ?
            ''', (password_hash, salt, student_id))
            
            return True
    
    def verify_password(self, student_id: str, password: str) -> bool:
        """验证学生密码"""
        import hashlib
        
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, salt FROM students WHERE student_id = ?",
                (student_id,)
            )
            row = cursor.fetchone()
            
            if not row or not row['password_hash']:
                return False
            
            password_hash = hashlib.sha256(f"{password}{row['salt']}".encode()).hexdigest()
            return password_hash == row['password_hash']
