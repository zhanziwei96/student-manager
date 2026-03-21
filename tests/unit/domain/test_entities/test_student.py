"""
学生实体测试
纯内存测试，无需数据库
"""
import pytest
from datetime import datetime
from domain.entities.student import Student
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from domain.events.score_changed import ScoreChangedEvent
from domain.events.student_checked_in import StudentCheckedInEvent


class TestStudent:
    """学生实体测试类"""
    
    @pytest.fixture
    def student(self):
        """创建测试学生"""
        return Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)
        )
    
    # ========== 构造测试 ==========
    
    def test_create_student(self):
        """成功创建学生"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)
        )
        
        assert str(student.student_id) == "2024001"
        assert student.name == "张三"
        assert student.class_name == "软件1班"
        assert float(student.score) == 70
        assert student.created_at is not None
    
    def test_create_student_default_created_at(self):
        """创建时间默认为当前时间"""
        before = datetime.now()
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)
        )
        after = datetime.now()
        
        assert before <= student.created_at <= after
    
    def test_create_student_with_db_id(self):
        """创建学生带数据库ID"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70),
            id=123
        )
        
        assert student.id == 123
    
    # ========== 分数变更测试 ==========
    
    def test_change_score_add(self, student):
        """加分操作"""
        student.change_score(5, "课堂回答", "teacher1")
        
        assert float(student.score) == 75
    
    def test_change_score_subtract(self, student):
        """扣分操作"""
        student.change_score(-5, "迟到", "teacher1")
        
        assert float(student.score) == 65
    
    def test_change_score_creates_event(self, student):
        """分数变更创建领域事件"""
        student.change_score(5, "课堂回答", "teacher1")
        
        assert len(student.events) == 1
        event = student.events[0]
        assert isinstance(event, ScoreChangedEvent)
        assert str(event.student_id) == "2024001"
        assert event.student_name == "张三"
        assert event.old_score == 70
        assert event.new_score == 75
        assert event.delta == 5
        assert event.reason == "课堂回答"
        assert event.operator == "teacher1"
        assert event.timestamp is not None
    
    def test_change_score_multiple_events(self, student):
        """多次分数变更创建多个事件"""
        student.change_score(5, "回答问题", "teacher1")
        student.change_score(-3, "迟到", "teacher1")
        
        assert len(student.events) == 2
        assert student.events[0].delta == 5
        assert student.events[1].delta == -3
    
    def test_change_score_boundary_max(self, student):
        """加分到上限"""
        student.score = Score(98)
        
        student.change_score(5, "奖励", "teacher1")
        
        assert float(student.score) == 100  # 被截断
    
    def test_change_score_boundary_min(self, student):
        """扣分到下限"""
        student.score = Score(5)
        
        student.change_score(-10, "严重违纪", "teacher1")
        
        assert float(student.score) == 0  # 被截断
    
    def test_change_score_zero_delta(self, student):
        """分数变化为0"""
        student.change_score(0, "测试", "teacher1")
        
        assert float(student.score) == 70
        assert len(student.events) == 1
        assert student.events[0].delta == 0
    
    # ========== 领域事件测试 ==========
    
    def test_clear_events(self, student):
        """清空领域事件"""
        student.change_score(5, "测试", "teacher1")
        assert len(student.events) == 1
        
        student.clear_events()
        
        assert len(student.events) == 0
    
    def test_events_is_readonly_via_property(self, student):
        """通过property获取事件列表"""
        student.change_score(5, "测试", "teacher1")
        
        events = student.events
        assert len(events) == 1
    
    # ========== 签到测试 ==========
    
    def test_checkin_creates_event(self, student):
        """签到创建领域事件"""
        student.checkin()
        
        assert len(student.events) == 1
        event = student.events[0]
        assert isinstance(event, StudentCheckedInEvent)
        assert str(event.student_id) == "2024001"
        assert event.student_name == "张三"
        assert event.class_name == "软件1班"
        assert event.timestamp is not None
    
    def test_checkin_multiple_times(self, student):
        """多次签到创建多个事件"""
        student.checkin()
        student.checkin()
        
        assert len(student.events) == 2
    
    def test_checkin_and_score_change_events(self, student):
        """签到和分数变更都创建事件"""
        student.checkin()
        student.change_score(5, "奖励", "teacher1")
        
        assert len(student.events) == 2
        assert isinstance(student.events[0], StudentCheckedInEvent)
        assert isinstance(student.events[1], ScoreChangedEvent)
    
    # ========== to_dict 测试 ==========
    
    def test_to_dict(self, student):
        """转换为字典"""
        data = student.to_dict()
        
        assert data['student_id'] == "2024001"
        assert data['name'] == "张三"
        assert data['class_name'] == "软件1班"
        assert data['score'] == 70.0
        assert 'created_at' in data
    
    def test_to_dict_score_type(self, student):
        """to_dict中score是float类型"""
        data = student.to_dict()
        
        assert isinstance(data['score'], float)
    
    # ========== 不可变性测试（通过行为验证） ==========
    
    def test_score_change_returns_new_score(self, student):
        """分数变更后score引用改变"""
        old_score = student.score
        
        student.change_score(5, "奖励", "teacher1")
        
        # Score值对象不可变，但student.score引用会改变
        assert student.score is not old_score
