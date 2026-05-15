"""
CRUD 导出
"""
from app.crud.student import (
    get_student, get_students, get_students_by_class, get_students_by_classes,
    create_student, update_student_score, delete_student, get_all_classes,
    reset_student_password, count_students
)
from app.crud.user import (
    get_user, get_user_by_username, get_users, create_user,
    update_user, update_user_info, record_login_success, record_login_failure,
    reset_password, update_user_password, delete_user
)
from app.crud.checkin import (
    get_today_checkins, create_checkin, has_checked_in_today,
    get_student_score_logs, count_today_checkins, is_device_checked_in_session,
)
from app.crud.schedule import (
    get_schedule, get_schedules, delete_schedule,
    create_schedule, import_schedules
)
from app.crud.course_session import (
    get_course_session,
    get_active_course_session_by_class_name,
    get_teacher_active_course_sessions,
    get_course_sessions_by_schedule_and_week,
    start_course_session,
    end_course_session,
    get_teacher_course_sessions,
)
from app.crud.schedule_adjustment import (
    get_adjustment,
    get_adjustments,
    create_adjustment,
    has_active_session,
    has_ended_session,
)
from app.crud.audit import (
    create_audit_log, get_audit_logs, get_my_logs,
    create_security_alert, get_unresolved_alerts, resolve_alert, cleanup_old_audit_logs
)
from app.crud.leaderboard import get_leaderboard
from app.crud.group import (
    get_group, get_groups_by_class, get_student_active_group,
    get_group_members, create_group, create_membership_request,
    get_pending_membership_requests, approve_membership_request,
    reject_membership_request, create_dissolution_request,
    get_pending_dissolution_requests, approve_dissolution_request,
    reject_dissolution_request, transfer_group_leader,
    auto_assign_unassigned_students,
    get_class_group_settings, get_or_create_class_group_settings,
    update_class_group_settings,
    get_group_with_members, remove_group_member, dissolve_group,
)
from app.crud.group_task import (
    create_group_task, get_group_task, get_group_tasks_by_class,
    get_task_dimensions, start_group_task, close_group_task,
    get_evaluation_assignments, submit_teacher_score,
    submit_student_scores, get_task_results, clone_group_task,
    delete_group_task,
)
from app.crud.question import (
    create_question, get_question, get_questions_by_teacher,
    get_questions_by_class, close_question, count_answers,
    create_answer, get_answer, get_answers_by_question,
    update_answer, star_answer, delete_answer,
)
from app.crud.lost_found import (
    create_lost_found_item, get_lost_found_item, get_lost_found_items,
    update_lost_found_item, delete_lost_found_item, count_claims_by_status,
    create_comment, get_comments_by_item,
    create_claim, get_claims_by_item, get_claim, get_student_claim,
    confirm_claim, reject_claim,
    DuplicateClaimError, ItemNotClaimableError,
)

__all__ = [
    # Student
    "get_student", "get_students", "get_students_by_class", "get_students_by_classes",
    "create_student", "update_student_score", "delete_student", "get_all_classes",
    "reset_student_password", "count_students",
    # User
    "get_user", "get_user_by_username", "get_users", "create_user",
    "update_user", "update_user_info", "record_login_success", "record_login_failure",
    "reset_password", "update_user_password", "delete_user",
    # Checkin
    "get_today_checkins", "create_checkin", "has_checked_in_today",
    "get_student_score_logs", "count_today_checkins", "is_device_checked_in_session",
    # Schedule
    "get_schedule", "get_schedules", "delete_schedule",
    "create_schedule", "import_schedules",
    # CourseSession
    "get_course_session", "get_active_course_session_by_class_name",
    "get_teacher_active_course_sessions", "get_course_sessions_by_schedule_and_week",
    "start_course_session", "end_course_session", "get_teacher_course_sessions",
    # Audit
    "create_audit_log", "get_audit_logs", "get_my_logs",
    "create_security_alert", "get_unresolved_alerts", "resolve_alert", "cleanup_old_audit_logs",
    # ScheduleAdjustment
    "get_adjustment", "get_adjustments", "create_adjustment",
    "has_active_session", "has_ended_session",
    # Leaderboard
    "get_leaderboard",
    # Group
    "get_group", "get_groups_by_class", "get_student_active_group",
    "get_group_members", "create_group", "create_membership_request",
    "get_pending_membership_requests", "approve_membership_request",
    "reject_membership_request", "create_dissolution_request",
    "get_pending_dissolution_requests", "approve_dissolution_request",
    "reject_dissolution_request", "transfer_group_leader",
    "auto_assign_unassigned_students",
    "get_class_group_settings", "get_or_create_class_group_settings",
    "update_class_group_settings",
    "get_group_with_members", "remove_group_member", "dissolve_group",
    # GroupTask
    "create_group_task", "get_group_task", "get_group_tasks_by_class",
    "get_task_dimensions", "start_group_task", "close_group_task",
    "get_evaluation_assignments", "submit_teacher_score",
    "submit_student_scores", "get_task_results", "clone_group_task",
    "delete_group_task",
    # Question
    "create_question", "get_question", "get_questions_by_teacher",
    "get_questions_by_class", "close_question", "count_answers",
    "create_answer", "get_answer", "get_answers_by_question",
    "update_answer", "star_answer", "delete_answer",
    # LostFound
    "create_lost_found_item", "get_lost_found_item", "get_lost_found_items",
    "update_lost_found_item", "delete_lost_found_item", "count_claims_by_status",
    "create_comment", "get_comments_by_item",
    "create_claim", "get_claims_by_item", "get_claim", "get_student_claim",
    "confirm_claim", "reject_claim",
    "DuplicateClaimError", "ItemNotClaimableError",
]
