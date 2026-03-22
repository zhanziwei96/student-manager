"""
审计日志 CRUD 操作
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models import AuditLog, SecurityAlert


def create_audit_log(session: Session, **kwargs) -> AuditLog:
    """创建审计日志"""
    audit_log = AuditLog(**kwargs)
    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log


def get_audit_logs(session: Session, limit: int = 100, offset: int = 0) -> List[AuditLog]:
    """获取审计日志列表"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    return session.exec(query).all()


def get_my_logs(session: Session, user_id: int, limit: int = 50) -> List[AuditLog]:
    """获取我的操作日志"""
    query = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(limit)
    return session.exec(query).all()


def create_security_alert(session: Session, alert_type: str, severity: str, 
                          description: str, **kwargs) -> SecurityAlert:
    """创建安全警报"""
    alert = SecurityAlert(
        alert_type=alert_type,
        severity=severity,
        description=description,
        **kwargs
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def get_unresolved_alerts(session: Session) -> List[SecurityAlert]:
    """获取未解决的安全警报"""
    query = select(SecurityAlert).where(SecurityAlert.is_resolved == False).order_by(SecurityAlert.created_at.desc())
    return session.exec(query).all()


def resolve_alert(session: Session, alert_id: int) -> bool:
    """解决安全警报"""
    alert = session.get(SecurityAlert, alert_id)
    if not alert:
        return False
    alert.is_resolved = True
    session.add(alert)
    session.commit()
    return True


def cleanup_old_audit_logs(session: Session, retention_days: int = 90) -> int:
    """清理旧审计日志"""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    query = select(AuditLog).where(AuditLog.created_at < cutoff_date)
    old_logs = session.exec(query).all()
    count = len(old_logs)
    for log in old_logs:
        session.delete(log)
    session.commit()
    return count
