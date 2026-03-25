import sqlite3

def fix_score_logs():
    conn = sqlite3.connect('backend/data/class_system.db')
    cursor = conn.cursor()
    
    updated = 0
    
    # 获取所有有分数日志的学生
    students = cursor.execute(
        "SELECT DISTINCT s.student_id, s.score FROM students s "
        "WHERE EXISTS (SELECT 1 FROM score_logs sl WHERE sl.student_id = s.student_id)"
    ).fetchall()
    
    print(f"找到 {len(students)} 个有分数日志的学生")
    
    for student_id, current_score in students:
        # 获取该学生的所有分数日志（按时间排序）
        logs = cursor.execute(
            "SELECT id, delta FROM score_logs WHERE student_id = ? ORDER BY created_at",
            (student_id,)
        ).fetchall()
        
        if not logs:
            continue
        
        # 计算初始分数
        total_delta = sum(log[1] for log in logs)
        base_score = current_score - total_delta
        
        # 逐条计算 old_score 和 new_score，并设置 operator
        running_score = base_score
        for log_id, delta in logs:
            old_score = running_score
            new_score = running_score + delta
            
            cursor.execute(
                "UPDATE score_logs SET old_score = ?, new_score = ?, operator = '占孜伟' WHERE id = ?",
                (old_score, new_score, log_id)
            )
            updated += 1
            
            running_score = new_score
    
    conn.commit()
    conn.close()
    print(f"更新了 {updated} 条记录")

if __name__ == '__main__':
    fix_score_logs()
