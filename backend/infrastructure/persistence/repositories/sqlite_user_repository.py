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
        from datetime import datetime
        
        # 解析绑定的班级
        assigned_classes = []
        assigned_class_value = row['assigned_class']
        if assigned_class_value:
            try:
                assigned_classes = json.loads(assigned_class_value)
            except:
                assigned_classes = [c.strip() for c in assigned_class_value.split(',') if c.strip()]
        
        # 时间字段转换（字符串 -> datetime）
        def parse_datetime(value):
            if value:
                try:
                    return datetime.fromisoformat(str(value).replace('Z', '+00:00').replace('+00:00', ''))
                except:
                    return None
            return None
        
        locked_until = parse_datetime(row['locked_until'])
        last_login_at = parse_datetime(row['last_login'])
        created_at = parse_datetime(row['created_at'])
        
        # 状态字段处理
        if locked_until and locked_until > datetime.now():
            status = UserStatus.LOCKED
        else:
            status = UserStatus.ACTIVE if row['is_active'] else UserStatus.INACTIVE
        
        return User(
            id=row['id'],
            username=row['username'],
            name=row['name'] or row['username'],
            password=Password.from_hash(
                hash_value=row['password_hash'],
                salt=row['salt']
            ) if row['password_hash'] else None,
            role=UserRole(row['role'] or 'teacher'),
            assigned_classes=assigned_classes,
            status=status,
            login_fail_count=row['login_fail_count'] or 0,
            locked_until=locked_until,
            last_login_ip=row['last_login_ip'],
            last_login_at=last_login_at,
            created_at=created_at
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
                (f'%{class_name}%',)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def save(self, user: User) -> None:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            
            # 将班级列表转换为逗号分隔字符串
            assigned_class_str = ','.join(user.assigned_classes) if user.assigned_classes else None
            
            # 状态值转换为整数
            is_active = 1 if user.status == UserStatus.ACTIVE else 0
            
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
                    user.password.hash,
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
                # 新增 - 保存所有字段
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, salt, name, role, assigned_class, is_active,
                     login_fail_count, locked_until, last_login_ip, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.username,
                    user.password.hash,
                    user.password.salt,
                    user.name,
                    user.role.value,
                    assigned_class_str,
                    is_active,
                    user.login_fail_count,
                    user.locked_until,
                    user.last_login_ip,
                    user.last_login_at
                ))
                user.id = cursor.lastrowid
    
    def delete(self, user_id: int) -> None:
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    def exists(self, username: str) -> bool:
        return self.find_by_username(username) is not None
