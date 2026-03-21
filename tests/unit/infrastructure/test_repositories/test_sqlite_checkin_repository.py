"""
SQLite 签到仓储测试
使用内存数据库，无需外部依赖
"""
import pytest
from datetime import datetime
from domain.entities.checkin import Checkin, CheckinType


class TestSQLiteCheckinRepository:
    """SQLite 签到仓储测试类"""
    
    @pytest.fixture
    def sample_checkin(self):
        """示例签到记录"""
        return Checkin(
            student_id="2024001",
            student_name="张三",
            class_name="软件1班",
            checkin_type=CheckinType.SELF,
            checkin_date="2025-03-21",
            checkin_time="09:00:00",
            score_delta=0.5
        )
    
    # ========== 保存测试 ==========
    
    def test_save_new_checkin(self, checkin_repo):
        """保存新签到记录"""
        checkin = Checkin(
            student_id="2024001",
            student_name="张三",
            class_name="软件1班",
            checkin_type=CheckinType.SELF
        )
        
        saved = checkin_repo.save(checkin)
        
        assert saved.id is not None
        assert saved.student_id == "2024001"
    
    def test_save_checkin_with_created_by(self, checkin_repo):
        """保存老师代签记录"""
        checkin = Checkin(
            student_id="2024001",
            student_name="张三",
            class_name="软件1班",
            checkin_type=CheckinType.TEACHER,
            created_by=1  # 老师ID
        )
        
        saved = checkin_repo.save(checkin)
        
        assert saved.id is not None
        # 代签记录可以由老师创建
    
    # ========== 查询测试 ==========
    
    def test_find_by_id_exists(self, checkin_repo, sample_checkin):
        """通过ID查找签到记录"""
        saved = checkin_repo.save(sample_checkin)
        checkin_id = saved.id
        
        found = checkin_repo.find_by_id(checkin_id)
        
        assert found is not None
        assert found.student_id == "2024001"
        assert found.student_name == "张三"
    
    def test_find_by_id_not_exists(self, checkin_repo):
        """通过ID查找不存在的记录"""
        found = checkin_repo.find_by_id(99999)
        
        assert found is None
    
    def test_find_by_student_and_date_exists(self, checkin_repo):
        """查找学生某天的签到记录"""
        checkin = Checkin(
            student_id="2024001",
            student_name="张三",
            class_name="软件1班",
            checkin_type=CheckinType.SELF,
            checkin_date="2025-03-21"
        )
        checkin_repo.save(checkin)
        
        found = checkin_repo.find_by_student_and_date("2024001", "2025-03-21")
        
        assert found is not None
        assert found.student_id == "2024001"
    
    def test_find_by_student_and_date_not_exists(self, checkin_repo):
        """查找学生某天未签到"""
        found = checkin_repo.find_by_student_and_date("2024001", "2025-03-21")
        
        assert found is None
    
    def test_find_by_filters_all(self, checkin_repo):
        """查询所有签到记录"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024002", "李四", "软件1班", CheckinType.SELF, "2025-03-21"))
        
        records = checkin_repo.find_by_filters()
        
        assert len(records) == 2
    
    def test_find_by_filters_by_student(self, checkin_repo):
        """按学生查询签到记录"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024002", "李四", "软件1班", CheckinType.SELF, "2025-03-21"))
        
        records = checkin_repo.find_by_filters(student_id="2024001")
        
        assert len(records) == 1
        assert records[0].student_id == "2024001"
    
    def test_find_by_filters_by_class(self, checkin_repo):
        """按班级查询签到记录"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024002", "李四", "软件2班", CheckinType.SELF, "2025-03-21"))
        
        records = checkin_repo.find_by_filters(class_name="软件1班")
        
        assert len(records) == 1
        assert records[0].class_name == "软件1班"
    
    def test_find_by_filters_by_date(self, checkin_repo):
        """按日期查询签到记录"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-22"))
        
        records = checkin_repo.find_by_filters(date="2025-03-21")
        
        assert len(records) == 1
        assert records[0].checkin_date == "2025-03-21"
    
    def test_find_by_filters_date_range(self, checkin_repo):
        """按日期范围查询签到记录"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-20"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-22"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-23"))
        
        records = checkin_repo.find_by_filters(
            student_id="2024001",
            start_date="2025-03-21",
            end_date="2025-03-22"
        )
        
        assert len(records) == 2
    
    def test_find_by_filters_limit(self, checkin_repo):
        """查询限制返回数量"""
        for i in range(10):
            checkin_repo.save(Checkin(f"2024{i:03d}", f"学生{i}", "软件1班", CheckinType.SELF, "2025-03-21"))
        
        records = checkin_repo.find_by_filters(limit=5)
        
        assert len(records) == 5
    
    def test_find_by_class_today(self, checkin_repo):
        """查询班级今日签到"""
        today = datetime.now().strftime('%Y-%m-%d')
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, today))
        checkin_repo.save(Checkin("2024002", "李四", "软件1班", CheckinType.SELF, today))
        checkin_repo.save(Checkin("2024003", "王五", "软件2班", CheckinType.SELF, today))
        
        records = checkin_repo.find_by_class_today("软件1班")
        
        assert len(records) == 2
    
    # ========== 统计测试 ==========
    
    def test_count_by_student_and_date_range(self, checkin_repo):
        """统计学生日期范围内签到次数"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-20"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-22"))
        
        count = checkin_repo.count_by_student_and_date_range(
            "2024001", "2025-03-20", "2025-03-22"
        )
        
        assert count == 3
    
    def test_count_by_class_and_date(self, checkin_repo):
        """统计班级某天签到人数"""
        checkin_repo.save(Checkin("2024001", "张三", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024002", "李四", "软件1班", CheckinType.SELF, "2025-03-21"))
        checkin_repo.save(Checkin("2024003", "王五", "软件1班", CheckinType.SELF, "2025-03-21"))
        # 同一人重复签到不算
        
        count = checkin_repo.count_by_class_and_date("软件1班", "2025-03-21")
        
        assert count == 3
    
    # ========== 更新测试 ==========
    
    def test_update_checkin(self, checkin_repo, sample_checkin):
        """更新签到记录"""
        saved = checkin_repo.save(sample_checkin)
        checkin_id = saved.id
        
        # 修改并更新
        saved.student_name = "张三丰"
        saved.score_delta = 1.0
        checkin_repo.save(saved)
        
        found = checkin_repo.find_by_id(checkin_id)
        assert found.student_name == "张三丰"
