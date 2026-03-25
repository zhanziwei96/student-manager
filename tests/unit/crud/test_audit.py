"""
审计日志 CRUD 单元测试
"""
import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.crud.audit import (
    create_audit_log, get_audit_logs, get_my_logs,
    create_security_alert, get_unresolved_alerts, resolve_alert,
    cleanup_old_audit_logs
)
from app.models import AuditLog, SecurityAlert


class TestAuditLogCRUD:
    """测试审计日志 CRUD"""
    
    def test_create_audit_log(self, session: Session):
        """测试创建审计日志"""
        log = create_audit_log(
            session,
            user_id=1,
            user_name="admin",
            role="admin",
            action="登录",
            resource="系统",
            method="POST",
            ip_address="127.0.0.1",
            status_code=200
        )
        
        assert log.id is not None
        assert log.user_id == 1
        assert log.user_name == "admin"
        assert log.action == "登录"
        assert log.resource == "系统"
    
    def test_get_audit_logs(self, session: Session):
        """测试获取审计日志列表"""
        # 创建多条日志
        for i in range(5):
            create_audit_log(
                session,
                user_id=i + 1,
                user_name=f"user{i}",
                role="admin",
                action="登录",
                resource="系统",
                method="POST",
                ip_address="127.0.0.1",
                status_code=200
            )
        
        logs = get_audit_logs(session, limit=3)
        assert len(logs) == 3
    
    def test_get_my_logs(self, session: Session):
        """测试获取我的操作日志"""
        # 创建用户 1 的日志
        create_audit_log(
            session,
            user_id=1,
            user_name="user1",
            role="admin",
            action="登录",
            resource="系统",
            method="POST",
            ip_address="127.0.0.1",
            status_code=200
        )
        
        # 创建用户 2 的日志
        create_audit_log(
            session,
            user_id=2,
            user_name="user2",
            role="teacher",
            action="登录",
            resource="系统",
            method="POST",
            ip_address="127.0.0.1",
            status_code=200
        )
        
        logs = get_my_logs(session, user_id=1)
        assert len(logs) == 1
        assert logs[0].user_id == 1


class TestSecurityAlertCRUD:
    """测试安全警报表 CRUD"""
    
    def test_create_security_alert(self, session: Session):
        """测试创建安全警报"""
        alert = create_security_alert(
            session,
            alert_type="brute_force",
            severity="high",
            description="多次登录失败",
            related_user_id=1,
            related_ip="192.168.1.1"
        )
        
        assert alert.id is not None
        assert alert.alert_type == "brute_force"
        assert alert.severity == "high"
        assert alert.is_resolved is False
    
    def test_get_unresolved_alerts(self, session: Session):
        """测试获取未解决的安全警报"""
        # 创建未解决警报
        create_security_alert(
            session,
            alert_type="brute_force",
            severity="high",
            description="多次登录失败"
        )
        
        # 创建已解决警报
        resolved_alert = create_security_alert(
            session,
            alert_type="suspicious_activity",
            severity="medium",
            description="可疑活动"
        )
        resolved_alert.is_resolved = True
        session.add(resolved_alert)
        session.commit()
        
        unresolved = get_unresolved_alerts(session)
        assert len(unresolved) == 1
        assert unresolved[0].alert_type == "brute_force"
    
    def test_resolve_alert(self, session: Session):
        """测试解决安全警报"""
        alert = create_security_alert(
            session,
            alert_type="brute_force",
            severity="high",
            description="多次登录失败"
        )
        
        assert alert.is_resolved is False
        
        result = resolve_alert(session, alert.id)
        assert result is True
        
        # 验证已解决
        resolved_alert = session.get(SecurityAlert, alert.id)
        assert resolved_alert.is_resolved is True
    
    def test_resolve_alert_not_found(self, session: Session):
        """测试解决不存在的警报"""
        result = resolve_alert(session, 99999)
        assert result is False
    
    def test_cleanup_old_audit_logs(self, session: Session):
        """测试清理旧审计日志"""
        # 创建旧日志
        old_log = AuditLog(
            user_id=1,
            user_name="admin",
            role="admin",
            action="登录",
            resource="系统",
            created_at=datetime.now() - timedelta(days=100)
        )
        session.add(old_log)
        
        # 创建新日志
        new_log = AuditLog(
            user_id=1,
            user_name="admin",
            role="admin",
            action="登录",
            resource="系统",
            created_at=datetime.now()
        )
        session.add(new_log)
        session.commit()
        
        # 清理 90 天前的日志
        count = cleanup_old_audit_logs(session, retention_days=90)
        assert count == 1
        
        # 验证只剩新日志
        remaining = session.exec(select(AuditLog)).all()
        assert len(remaining) == 1
