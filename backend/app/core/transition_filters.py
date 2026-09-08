"""
双写过渡期查询过滤器（方案 2.4 冗余字段策略）

FK 优先、未回填行回退字符串匹配：
- 已回填行（FK 非空）：按 FK 精确过滤（跨届同名班不混淆）
- 未回填行（FK 为空，测试直接构造/历史数据）：按字符串回退匹配
- FK 未解析（无 classes/semesters 行）：整体退化为字符串过滤

Phase 4 删除旧字段后，过滤器退化为纯 FK 条件。
"""
from sqlalchemy import and_, or_


def class_filter(class_id_column, class_name_column, class_id, class_name: str):
    """班级过滤：class_id 精确匹配，未回填行回退 class_name；
    class_id 未解析（班级不存在）时退化为纯字符串过滤"""
    if class_id is None:
        return class_name_column == class_name
    return or_(
        class_id_column == class_id,
        and_(class_id_column.is_(None), class_name_column == class_name),
    )


def semester_filter(semester_id_column, semester_column, semester_id, term_label: str):
    """学期过滤：semester_id 精确匹配，未回填行回退 semester 字符串；
    semester_id 未解析（当前学期无 DB 行）时退化为纯字符串过滤"""
    if semester_id is None:
        return semester_column == term_label
    return or_(
        semester_id_column == semester_id,
        and_(semester_id_column.is_(None), semester_column == term_label),
    )
