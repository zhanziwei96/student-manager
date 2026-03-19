"""
SQLite 用户仓储实现
"""
from typing import List, Optional
import sqlite3
import json
from domain.entities.user import User, UserRole, UserStatus
from domain.value_objects.password import Password
from domain.repositories.user_repository import UserRepository
from infrastructure.persistence.database import Database


class SQLiteUserRepository(UserRepository):
    """SQLite 用户仓储实现"""
    
    def __init__(self, database: Database):
        self.db = database
    
    def _get_conn(self) -> sqlite3.Connection:
        return self.db.get_connection()
    
    def _row_to_entity(self, row: sqlite3.Row) -> User:
        """将数据行转换为领域实体"""
        # 解析绑定的班级（JSON数组存储）
        assigned_classes = []
        if row['assigned_classes']:
            try:
                assigned_classes = json.loads(row['assigned_classes'])
            except:
                assigned_classes = row['assigned_classes'].split(',') if row['assigned_classes'] else []
        
        return User(
            id=row['id'],
            username=row['username'],
            name=row['name'],
            password=Password(
                hash_value=row['password_hash'],
                salt=row['salt']
            ),
            role=UserRole(row['role']),
            assigned_classes=assigned_classes,
            status=UserStatus(row['status']),
            login_fail_count=row['login_fail_count'],
            locked_until=row['locked_until'],
            last_login_ip=row['last_login_ip'],
            last_login_at=row['last_login_at'],
            created_at=row['created_at']
        )
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    def find_all(self) -> List[User]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entity(row) for row in rows]
    
    def find_by_class(self, class_name: str) -> List[User]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE assigned_classes LIKE ?",
            (f'%"{class_name}"%',)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entity(row) for row in rows]
    
    def save(self, user: User) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 将班级列表转换为JSON
        assigned_classes_json = json.dumps(user.assigned_classes) if user.assigned_classes else '[]'
        
        if user.id:
            # 更新
            cursor.execute('''
                UPDATE users 
                SET username = ?, password_hash = ?, salt = ?, name = ?,
                    role = ?, assigned_classes = ?, status = ?,
                    login_fail_count = ?, locked_until = ?, 
                    last_login_ip = ?, last_login_at = ?
                WHERE id = ?
            ''', (
                user.username,
                user.password.hash_value,
                user.password.salt,
                user.name,
                user.role.value,
                assigned_classes_json,
                user.status.value,
                user.login_fail_count,
                user.locked_until,
                user.last_login_ip,
                user.last_login_at,
                user.id
            ))
        else:
            # 新增
            cursor.execute('''
                INSERT INTO users 
                (username, password_hash, salt, name, role, assigned_classes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.username,
                user.password.hash_value,
                user.password.salt,
                user.name,
                user.role.value,
                assigned_classes_json,
                user.status.value
            ))
            user.id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def delete(self, user_id: int) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def exists(self, username: str) -> bool:
        return self.find_by_username(username) is not None
