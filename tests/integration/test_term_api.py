"""term API 集成测试"""
from datetime import date


def test_get_current_term_info(client):
    """返回当前学期标识、开始日期、当前周次、总周数"""
    resp = client.get("/api/v1/term/current")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["term"] == "2026-2027-1"
    assert data["start_date"] == "2026-09-07"
    assert data["total_weeks"] == 20
    # current_week: 0..total_weeks 范围内（取决于运行当天，不再要求具体值）
    assert 0 <= data["current_week"] <= 20
