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
    
    def _row_to_entity(self, row: sqlite3.Row) -> User:
        """将数据行转换为领域实体"""
        # 解析绑定的班级（JSON数组存储）
        assigned_classes = []
        assigned_class_value = row['assigned_class'] if 'assigned_class' in row.keys() else None
        if assigned_class_value:
            try:
                assigned_classes = json.loads(assigned_class_value)
            except:
                assigned_classes = assigned_class_value.split(',') if assigned_class_value else []
        
        # 状态字段兼容性处理
        is_active = row['is_active'] if 'is_active' in row.keys() else 1
        status_value = 'active' if is_active == 1 else 'inactive'
        
        # 角色字段
        role_value = row['role'] if 'role' in row.keys() else 'teacher'
        
        return User(
            id=row['id'],
            username=row['username'],
            name=row['name'],
            password=Password(
                hash_value=row['password_hash'],
                salt=row['salt']
            ),
            role=UserRole(role_value),
            assigned_classes=assigned_classes,
            status=UserStatus(status_value),
            login_fail_count=row['login_fail_count'] if 'login_fail_count' in row.keys() else 0,
            locked_until=row['locked_until'] if 'locked_until' in row.keys() else None,
            last_login_ip=row['last_login_ip'] if 'last_login_ip' in row.keys() else None,
            last_login_at=row['last_login'] if 'last_login' in row.keys() else None,
            created_at=row['created_at']
        )
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    def find_by_username(self, username: str) -> Optional[User]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    def find_all(self) -> List[User]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id")
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def find_by_class(self, class_name: str) -> List[User]:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE assigned_class LIKE ?",
                (f'%"{class_name}"%',)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def save(self, user: User) -> None:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            
            # 将班级列表转换为JSON字符串
            assigned_class_str = json.dumps(user.assigned_classes) if user.assigned_classes else ''
            
            # 状态转换为整数
            is_active = 1 if user.status.value == 'active' else 0
            
            if user.id:
                # 更新
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, salt = ?, name = ?,
                        role = ?, assigned_class = ?, is_active = ?,
                        login_fail_count = ?, locked_until = ?, 
                        last_login_ip = ?, last_login = ?
                    WHERE id = ?
                ''', (
                    user.password.hash_value,
                    user.password.salt,
                    user.name,
                    user.role.value,
                    assigned_class_str,
                    is_active,
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
                    (username, password_hash, salt, name, role, assigned_class, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.username,
                    user.password.hash_value,
                    user.password.salt,
                    user.name,
                    user.role.value,
                    assigned_class_str,
                    is_active
                ))
                user.id = cursor.lastrowid
    
    def delete(self, user_id: int) -> None:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    def exists(self, username: str) -> bool:
        return self.find_by_username(username) is not None
