"""
领域事件基础设施单元测试
"""
import pytest
from datetime import datetime
from app.core.events import Event, ScoreUpdated, StudentCreated, event_bus


class TestEventBus:
    """测试事件总线"""
    
    def setup_method(self):
        """每个测试前清理事件总线"""
        event_bus.clear()
    
    def teardown_method(self):
        """每个测试后清理事件总线"""
        event_bus.clear()
    
    def test_subscribe_and_publish(self):
        """测试订阅和发布事件"""
        events_captured = []
        
        def handler(event):
            events_captured.append(event)
        
        event_bus.subscribe(ScoreUpdated, handler)
        
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        event_bus.publish(event)
        
        assert len(events_captured) == 1
        assert events_captured[0].student_id == "S001"
        assert events_captured[0].old_score == 70.0
        assert events_captured[0].new_score == 75.0
    
    def test_multiple_handlers(self):
        """测试多个处理器订阅同一事件"""
        events_1 = []
        events_2 = []
        
        def handler1(event):
            events_1.append(event)
        
        def handler2(event):
            events_2.append(event)
        
        event_bus.subscribe(ScoreUpdated, handler1)
        event_bus.subscribe(ScoreUpdated, handler2)
        
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        event_bus.publish(event)
        
        assert len(events_1) == 1
        assert len(events_2) == 1
    
    def test_no_handler(self):
        """测试没有处理器时发布事件"""
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        # 不应该抛出异常
        event_bus.publish(event)
    
    def test_clear_handlers(self):
        """测试清理处理器"""
        events_captured = []
        
        def handler(event):
            events_captured.append(event)
        
        event_bus.subscribe(ScoreUpdated, handler)
        event_bus.clear()
        
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        event_bus.publish(event)
        
        assert len(events_captured) == 0
    
    def test_different_event_types(self):
        """测试不同事件类型互不影响"""
        score_events = []
        student_events = []
        
        def score_handler(event):
            score_events.append(event)
        
        def student_handler(event):
            student_events.append(event)
        
        event_bus.subscribe(ScoreUpdated, score_handler)
        event_bus.subscribe(StudentCreated, student_handler)
        
        score_event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        student_event = StudentCreated(
            student_id="S002",
            name="李四",
            class_name="软件2班"
        )
        
        event_bus.publish(score_event)
        
        assert len(score_events) == 1
        assert len(student_events) == 0
        
        event_bus.publish(student_event)
        
        assert len(score_events) == 1
        assert len(student_events) == 1


class TestScoreUpdatedEvent:
    """测试分数更新事件"""
    
    def test_event_creation(self):
        """测试事件创建"""
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        assert event.student_id == "S001"
        assert event.old_score == 70.0
        assert event.new_score == 75.0
        assert event.delta == 5.0
        assert event.reason == "奖励"
        assert event.operator == "老师"
        assert isinstance(event.occurred_at, datetime)
    
    def test_event_inheritance(self):
        """测试事件继承"""
        event = ScoreUpdated(
            student_id="S001",
            old_score=70.0,
            new_score=75.0,
            delta=5.0,
            reason="奖励",
            operator="老师"
        )
        
        assert isinstance(event, Event)


class TestStudentCreatedEvent:
    """测试学生创建事件"""
    
    def test_event_creation(self):
        """测试事件创建"""
        event = StudentCreated(
            student_id="S001",
            name="张三",
            class_name="软件1班"
        )
        
        assert event.student_id == "S001"
        assert event.name == "张三"
        assert event.class_name == "软件1班"
        assert isinstance(event.occurred_at, datetime)
