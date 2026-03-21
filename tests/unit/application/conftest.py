"""
Application 层测试配置
提供 Mock Repository Fixtures
"""
import sys
import os

# 添加 backend 到 Python 路径
backend_path = "/home/yufeng/student-manager/backend"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
from datetime import datetime
from typing import List, Optional, Dict, Any

from domain.entities.student import Student
from domain.entities.user import User, UserRole, UserStatus
from domain.entities.score_log import ScoreLog
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from domain.value_objects.password import Password


class MockStudentRepository:
    """Mock 学生仓储"""
    
    def __init__(self):
        self._students: Dict[str, Student] = {}
        self._next_id = 1
    
    def find_by_id(self, student_id: StudentId) -> Optional[Student]:
        return self._students.get(str(student_id))
    
    def find_by_id_str(self, student_id: str) -> Optional[Student]:
        return self._students.get(student_id)
    
    def find_all(self) -> List[Student]:
        return list(self._students.values())
    
    def find_by_class(self, class_name: str) -> List[Student]:
        return [s for s in self._students.values() if s.class_name == class_name]
    
    def find_by_name(self, name: str) -> List[Student]:
        return [s for s in self._students.values() if name in s.name]
    
    def save(self, student: Student) -> None:
        self._students[str(student.student_id)] = student
    
    def delete(self, student_id: StudentId) -> None:
        if str(student_id) in self._students:
            del self._students[str(student_id)]
    
    def exists(self, student_id: StudentId) -> bool:
        return str(student_id) in self._students
    
    def clear(self):
        self._students.clear()


class MockUserRepository:
    """Mock 用户仓储"""
    
    def __init__(self):
        self._users: Dict[int, User] = {}
        self._users_by_username: Dict[str, int] = {}
        self._next_id = 1
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
    
    def find_by_username(self, username: str) -> Optional[User]:
        user_id = self._users_by_username.get(username)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def find_all(self) -> List[User]:
        return list(self._users.values())
    
    def find_by_class(self, class_name: str) -> List[User]:
        return [u for u in self._users.values() 
                if any(class_name in c for c in u.assigned_classes)]
    
    def save(self, user: User) -> None:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
        self._users[user.id] = user
        self._users_by_username[user.username] = user.id
    
    def delete(self, user_id: int) -> None:
        if user_id in self._users:
            user = self._users[user_id]
            del self._users_by_username[user.username]
            del self._users[user_id]
    
    def exists(self, username: str) -> bool:
        return username in self._users_by_username
    
    def clear(self):
        self._users.clear()
        self._users_by_username.clear()


class MockScoreLogRepository:
    """Mock 分数日志仓储"""
    
    def __init__(self):
        self._logs: List[ScoreLog] = []
        self._next_id = 1
    
    def save(self, log: ScoreLog) -> None:
        if log.id is None:
            log.id = self._next_id
            self._next_id += 1
        self._logs.append(log)
    
    def find_by_student(self, student_id: str, limit: int = 100) -> List[ScoreLog]:
        logs = [l for l in self._logs if l.student_id == student_id]
        return logs[-limit:]
    
    def clear(self):
        self._logs.clear()


@pytest.fixture
def mock_student_repo():
    """Mock 学生仓储 fixture"""
    repo = MockStudentRepository()
    yield repo
    repo.clear()


@pytest.fixture
def mock_user_repo():
    """Mock 用户仓储 fixture"""
    repo = MockUserRepository()
    yield repo
    repo.clear()


@pytest.fixture
def mock_score_log_repo():
    """Mock 分数日志仓储 fixture"""
    repo = MockScoreLogRepository()
    yield repo
    repo.clear()


@pytest.fixture
def student_app_service(mock_student_repo, mock_score_log_repo):
    """学生应用服务 fixture"""
    from application.services.student_app_service import StudentAppService
    return StudentAppService(mock_student_repo, mock_score_log_repo)


@pytest.fixture
def user_app_service(mock_user_repo):
    """用户应用服务 fixture"""
    from application.services.user_app_service import UserAppService
    return UserAppService(mock_user_repo)
