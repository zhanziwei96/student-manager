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
    
    def _get_conn(self) -> sqlite3.Connection:
        return self.db.get_connection()
    
    def _row_to_entity(self, row: sqlite3.Row) -> Student:
        """将数据行转换为领域实体"""
        return Student(
            id=row['id'],
            student_id=StudentId(row['student_id']),
            name=row['name'],
            class_name=row['class_name'],
            score=Score(row['score']),
            created_at=row['created_at']
        )
    
    def find_by_id(self, student_id: StudentId) -> Optional[Student]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE student_id = ?",
            (str(student_id),)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    def find_all(self) -> List[Student]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entity(row) for row in rows]
    
    def find_by_class(self, class_name: str) -> List[Student]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE class_name = ? ORDER BY student_id",
            (class_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entity(row) for row in rows]
    
    def find_by_name(self, name: str) -> List[Student]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE name LIKE ?",
            (f"%{name}%",)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entity(row) for row in rows]
    
    def save(self, student: Student) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if student.id:
            # 更新
            cursor.execute('''
                UPDATE students 
                SET name = ?, class_name = ?, score = ?
                WHERE id = ?
            ''', (
                student.name,
                student.class_name,
                float(student.score),
                student.id
            ))
        else:
            # 新增
            cursor.execute('''
                INSERT INTO students (student_id, name, class_name, score)
                VALUES (?, ?, ?, ?)
            ''', (
                str(student.student_id),
                student.name,
                student.class_name,
                float(student.score)
            ))
            student.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def delete(self, student_id: StudentId) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM students WHERE student_id = ?",
            (str(student_id),)
        )
        conn.commit()
        conn.close()
    
    def exists(self, student_id: StudentId) -> bool:
        return self.find_by_id(student_id) is not None
