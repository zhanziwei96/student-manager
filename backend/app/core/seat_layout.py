# backend/app/core/seat_layout.py
"""座位编号与布局生成（纯函数，不碰数据库）。"""


def generate_seat_no(row: int, col: int) -> str:
    """P{row}{col}：P23 = 第 2 排第 3 列。row/col 均从 1 起。"""
    return f"P{row}{col}"


def build_seat_rows(classroom_id: int, rows: int, cols: int) -> list[dict]:
    """按 rows×cols 生成整间教室的座位行数据（row 主序）。"""
    return [
        {
            "classroom_id": classroom_id,
            "seat_no": generate_seat_no(r, c),
            "row": r,
            "col": c,
        }
        for r in range(1, rows + 1)
        for c in range(1, cols + 1)
    ]
