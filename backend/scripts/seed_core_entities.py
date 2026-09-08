"""
核心实体初始化脚本 - semesters / cohorts（幂等可重跑）

用法:
    cd backend
    DATABASE__URL="postgresql+psycopg2://..." python scripts/seed_core_entities.py

流程:
    1. 从配置读当前学期（TERM 配置的 label/start_date/total_weeks）
    2. upsert semesters 当前学期行（label 冲突则跳过，is_current=true）
    3. upsert cohorts 当前届行（year=学期 label 前 4 位），绑定 entry_semester_id

说明:
    迁移 20260908_add_student_class_fields 已按「导入年份即届」回填 cohorts/classes；
    本脚本补充当前学期记录（迁移不读应用配置），并保证幂等。
"""
import os
import sys

# 保证以 backend 为工作目录运行时能 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.db import engine
from app.models.semester import Semester
from app.models.cohort import Cohort


def main() -> None:
    settings = get_settings()
    term = settings.term
    cohort_year = term.label.split("-")[0]

    with Session(engine) as session:
        # 1. upsert 当前学期（label 冲突跳过，保持幂等）
        stmt = insert(Semester).values(
            label=term.label,
            start_date=term.start_date,
            total_weeks=term.total_weeks,
            is_current=True,
            status="active",
        )
        session.execute(stmt.on_conflict_do_nothing(index_elements=["label"]))
        session.commit()

        # 2. upsert 当前届 + 绑定入学学期
        sem = session.exec(
            select(Semester).where(Semester.label == term.label)
        ).first()
        if sem is None:
            raise RuntimeError(f"学期 {term.label} 未写入 semesters 表")

        stmt = insert(Cohort).values(
            year=cohort_year,
            label=f"{cohort_year}届",
            entry_semester_id=sem.id,
            status="active",
        )
        session.execute(stmt.on_conflict_do_nothing(index_elements=["year"]))
        session.commit()

        semesters_count = len(session.exec(select(Semester)).all())
        cohorts_count = len(session.exec(select(Cohort)).all())
        print(f"种子数据就绪: semesters={semesters_count} 行, cohorts={cohorts_count} 行")


if __name__ == "__main__":
    main()
