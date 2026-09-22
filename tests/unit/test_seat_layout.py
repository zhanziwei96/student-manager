# tests/unit/test_seat_layout.py
from app.core.seat_layout import build_seat_rows, generate_seat_no


class TestGenerateSeatNo:
    def test_format(self):
        assert generate_seat_no(2, 3) == "P23"

    def test_row_col_start_at_1(self):
        assert generate_seat_no(1, 1) == "P11"

    def test_two_digit(self):
        assert generate_seat_no(10, 12) == "P1012"


class TestBuildSeatRows:
    def test_count(self):
        seats = build_seat_rows(classroom_id=1, rows=4, cols=6)
        assert len(seats) == 24

    def test_first_and_last(self):
        seats = build_seat_rows(classroom_id=1, rows=2, cols=3)
        assert seats[0] == {"classroom_id": 1, "seat_no": "P11", "row": 1, "col": 1}
        assert seats[-1] == {"classroom_id": 1, "seat_no": "P23", "row": 2, "col": 3}

    def test_unique_positions(self):
        seats = build_seat_rows(classroom_id=1, rows=5, cols=5)
        assert len({(s["row"], s["col"]) for s in seats}) == 25
