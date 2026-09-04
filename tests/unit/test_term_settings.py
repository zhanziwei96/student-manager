"""TermSettings 配置测试"""
from datetime import date
from app.core.config import TermSettings, Settings


def test_term_settings_defaults():
    """默认值为第二学期 2026-2027-1（2026-09-07 开学，20 周）"""
    settings = TermSettings()
    assert settings.label == "2026-2027-1"
    assert settings.start_date == date(2026, 9, 7)
    assert settings.total_weeks == 20


def test_term_settings_env_override(monkeypatch):
    """环境变量 TERM_CFG__LABEL 等可覆盖嵌套配置（经主 Settings 验证）"""
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.setenv("TERM_CFG__LABEL", "2027-2028-1")
    monkeypatch.setenv("TERM_CFG__START_DATE", "2027-09-06")
    monkeypatch.setenv("TERM_CFG__TOTAL_WEEKS", "21")
    settings = Settings()
    assert settings.term.label == "2027-2028-1"
    assert settings.term.start_date == date(2027, 9, 6)
    assert settings.term.total_weeks == 21


def test_bare_term_env_does_not_crash_settings(monkeypatch):
    """回归守卫：bash 通用 TERM 环境变量不得影响 Settings 构造"""
    monkeypatch.setenv("TERM", "xterm-256color")
    settings = Settings()
    assert settings.term.label == "2026-2027-1"
