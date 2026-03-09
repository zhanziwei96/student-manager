"""
班级管理系统 - 数据管理模块
使用 SQLite 数据库进行数据存储，优化并发处理
支持测试环境和生产环境分离
"""

import sqlite3
import os
import threading
import hashlib
import secrets
from datetime import datetime
from openpyxl import load_workbook

# 根据环境变量选择数据库
# 设置环境变量 FLASK_ENV=testing 或 DB_ENV=testing 使用测试数据库
# 默认使用生产数据库
ENV = os.environ.get('FLASK_ENV') or os.environ.get('DB_ENV', 'production')

if ENV == 'testing' or ENV == 'test':
    DB_FILE = 'data/test_class_system.db'
    DB_ENV_NAME = '测试环境'
else:
    DB_FILE = 'data/class_system.db'
    DB_ENV_NAME = '生产环境'

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

# 线程本地存储
thread_local = threading.local()

# 全局上课状态（由于只有一个老师使用，用内存存储即可）
current_class_session = {
    'class_name': None,
    'start_time': None,
    'active': False
}


def get_db_info():
    """获取当前数据库环境信息"""
    return {
        'env': ENV,
        'name': DB_ENV_NAME,
        'file': DB_FILE
    }


def get_db_connection():
    """获取数据库连接（每个线程一个连接）"""
    if not hasattr(thread_local, 'conn') or thread_local.conn is None:
        # 增加连接超时时间为 20 秒，避免并发时超时
        thread_local.conn = sqlite3.connect(
            DB_FILE, 
            check_same_thread=False,
            timeout=20.0
        )
        thread_local.conn.row_factory = sqlite3.Row
        # 设置 busy_timeout 为 10 秒，等待锁释放
        thread_local.conn.execute("PRAGMA busy_timeout = 10000")
        # 启用外键约束
        thread_local.conn.execute("PRAGMA foreign_keys = ON")
    return thread_local.conn


def close_db_connection():
    """关闭当前线程的数据库连接"""
    try:
        if hasattr(thread_local, 'conn') and thread_local.conn is not None:
            thread_local.conn.close()
            thread_local.conn = None
    except Exception:
        # 忽略关闭时的错误
        thread_local.conn = None


def hash_password(password, salt=None):
    """密码哈希，使用 PBKDF2"""
    if salt is None:
        salt = secrets.token_hex(16)
    # 使用 PBKDF2 进行密码哈希
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt, pwdhash.hex()


def verify_password(password, salt, hashed):
    """验证密码"""
    _, pwdhash = hash_password(password, salt)
    return pwdhash == hashed


def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 启用 WAL 模式，提高并发写入性能
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA cache_size = -64000")  # 64MB 缓存
    cursor.execute("PRAGMA temp_store = MEMORY")
    cursor.execute("PRAGMA mmap_size = 30000000000")
    
    # 用户表（老师账户）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # 学生表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_name TEXT DEFAULT '未分班',
            score INTEGER DEFAULT 70,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 签到记录表（移除外键约束，允许删除学生时自动清空关联记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_records (
            record_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checkin_type TEXT DEFAULT '网页签到'
        )
    ''')
    
    # 分数变更日志表（移除外键约束，允许删除学生时自动清空关联记录）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_logs (
            log_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            score_change INTEGER NOT NULL,
            reason TEXT,
            operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引，提高查询性能
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_checkin_time 
        ON checkin_records(checkin_time)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_checkin_student 
        ON checkin_records(student_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_score_log_time 
        ON score_logs(operation_time)
    ''')
    
    conn.commit()
    conn.close()
    
    # 创建默认管理员账户
    create_default_admin()


def create_default_admin():
    """创建默认管理员账户（如果不存在）"""
    # 检查是否已存在用户
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM users')
    result = cursor.fetchone()
    
    if result and result['count'] == 0:
        # 创建默认管理员账户 admin/admin123
        salt, password_hash = hash_password('admin123')
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, name, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, salt, '管理员', 1))
        conn.commit()
        print("=" * 50)
        print("默认管理员账户已创建")
        print("用户名: admin")
        print("密码: admin123")
        print("=" * 50)
    
    conn.close()


def authenticate_user(username, password):
    """验证用户登录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, password_hash, salt, name, is_admin
        FROM users
        WHERE username = ?
    ''', (username,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    if verify_password(password, row['salt'], row['password_hash']):
        # 更新最后登录时间
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (row['id'],))
        conn.commit()
        
        return {
            'id': row['id'],
            'username': row['username'],
            'name': row['name'],
            'is_admin': row['is_admin']
        }
    
    return None


def change_password(user_id, old_password, new_password):
    """修改密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证旧密码
    cursor.execute('SELECT password_hash, salt FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not row:
        return False, "用户不存在"
    
    if not verify_password(old_password, row['salt'], row['password_hash']):
        return False, "原密码错误"
    
    # 更新密码
    salt, password_hash = hash_password(new_password)
    cursor.execute('''
        UPDATE users SET password_hash = ?, salt = ?
        WHERE id = ?
    ''', (password_hash, salt, user_id))
    conn.commit()
    
    return True, "密码修改成功"


def get_user_by_id(user_id):
    """根据ID获取用户信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, name, is_admin, created_at, last_login
        FROM users
        WHERE id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'name': row['name'],
            'is_admin': row['is_admin'],
            'created_at': row['created_at'],
            'last_login': row['last_login']
        }
    return None


# ========== 学生相关操作 ==========

def get_all_students():
    """获取所有学生信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, name, class_name, score 
        FROM students 
        ORDER BY student_id
    ''')
    rows = cursor.fetchall()
    return [
        {
            'student_id': row['student_id'],
            'name': row['name'],
            'class_name': row['class_name'],
            'score': row['score'] if row['score'] else 0
        }
        for row in rows
    ]


def get_student_by_id(student_id):
    """根据学号获取学生信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, name, class_name, score 
        FROM students 
        WHERE student_id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    
    if row:
        return {
            'student_id': row['student_id'],
            'name': row['name'],
            'class_name': row['class_name'],
            'score': row['score'] if row['score'] else 0
        }
    return None


def get_students_by_name(name):
    """根据姓名获取学生列表（支持同名学生）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT student_id, name, class_name, score 
        FROM students 
        WHERE name LIKE ?
        ORDER BY class_name, student_id
    ''', (f'%{name}%',))
    rows = cursor.fetchall()
    
    return [
        {
            'student_id': row['student_id'],
            'name': row['name'],
            'class_name': row['class_name'],
            'score': row['score'] if row['score'] else 0
        }
        for row in rows
    ]


def add_student(student_id, name, class_name, score=70):
    """添加单个学生"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO students (student_id, name, class_name, score)
            VALUES (?, ?, ?, ?)
        ''', (student_id, name, class_name or '未分班', score))
        conn.commit()
        return True, "添加成功"
    except sqlite3.IntegrityError:
        return False, "学号已存在"
    except Exception as e:
        return False, f"添加失败: {str(e)}"


def import_students_from_xlsx(file_path, default_class=None):
    """从 Excel 文件导入学生（班级导入功能）
    支持按列名识别：学号/姓名/班级（不区分顺序，班级可选）
    支持 .xlsx 格式
    """
    imported_count = 0
    errors = []
    
    # 列名映射（支持多种常见命名）
    column_mapping = {
        'student_id': ['学号', '学生号', 'id', '编号', '学号id', 'studentid', 'student_id'],
        'name': ['姓名', '名字', '学生姓名', 'name', 'studentname', 'student_name'],
        'class_name': ['班级', '班级名称', 'class', 'classname', 'class_name', '班别']
    }
    
    try:
        # 加载 Excel 文件
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active  # 使用第一个工作表
        
        # 获取所有行
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return False, "Excel 文件为空", []
        
        # 解析表头（第一行）
        header_row = rows[0]
        column_indices = {}
        
        for idx, cell_value in enumerate(header_row):
            if not cell_value:
                continue
            header_str = str(cell_value).strip().lower()
            
            # 匹配学号列
            for alias in column_mapping['student_id']:
                if alias in header_str:
                    column_indices['student_id'] = idx
                    break
            
            # 匹配姓名列
            for alias in column_mapping['name']:
                if alias in header_str:
                    column_indices['name'] = idx
                    break
            
            # 匹配班级列
            for alias in column_mapping['class_name']:
                if alias in header_str:
                    column_indices['class_name'] = idx
                    break
        
        # 检查必需的列
        if 'student_id' not in column_indices:
            return False, "未找到'学号'列，请确保表头包含'学号'或类似字样", []
        if 'name' not in column_indices:
            return False, "未找到'姓名'列，请确保表头包含'姓名'或类似字样", []
        
        # 处理数据行
        for row_idx, row in enumerate(rows[1:], 2):  # 从第2行开始，行号从2计
            if not row:
                continue
            
            # 获取学号和姓名
            student_id = str(row[column_indices['student_id']]).strip() if row[column_indices['student_id']] else ''
            name = str(row[column_indices['name']]).strip() if row[column_indices['name']] else ''
            
            # 跳过空行
            if not student_id or not name:
                continue
            
            # 获取班级（优先使用 Excel 中的，其次使用默认的）
            cls = default_class or '未分班'
            if 'class_name' in column_indices and row[column_indices['class_name']]:
                excel_class = str(row[column_indices['class_name']]).strip()
                if excel_class:
                    cls = excel_class
            
            # 添加学生（使用默认分数 70 分）
            success, msg = add_student(student_id, name, cls)
            if success:
                imported_count += 1
            else:
                errors.append(f"第 {row_idx} 行 学号 {student_id}: {msg}")
        
        wb.close()
        return True, f"成功导入 {imported_count} 名学生", errors
        
    except Exception as e:
        return False, f"导入失败: {str(e)}", errors


def update_student_score(student_id, score_change, reason=""):
    """更新学生分数（增减分数）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查学生是否存在
        cursor.execute('SELECT score FROM students WHERE student_id = ?', (student_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "学生不存在"
        
        # 计算新分数
        current_score = row['score'] if row['score'] is not None else 70
        new_score = current_score + score_change
        
        # 更新学生分数
        cursor.execute('''
            UPDATE students 
            SET score = ? 
            WHERE student_id = ?
        ''', (new_score, student_id))
        
        # 记录分数变更日志
        log_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        cursor.execute('''
            INSERT INTO score_logs (log_id, student_id, score_change, reason)
            VALUES (?, ?, ?, ?)
        ''', (log_id, student_id, score_change, reason))
        
        conn.commit()
        return True, f"分数更新成功，当前分数: {new_score}"
    except Exception as e:
        conn.rollback()
        return False, f"更新失败: {str(e)}"


def add_checkin_record(student_id, checkin_type="网页签到"):
    """添加签到记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查学生是否存在
        cursor.execute('SELECT name FROM students WHERE student_id = ?', (student_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "学生不存在", None
        
        student_name = row['name']
        
        # 检查今天是否已经签到过
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM checkin_records 
            WHERE student_id = ? AND DATE(checkin_time) = ?
        ''', (student_id, today))
        
        check_result = cursor.fetchone()
        if check_result and check_result['count'] > 0:
            # 已经签到过，仍然允许签到但提示
            pass  # 如果需要禁止重复签到，可以在这里返回
        
        # 添加签到记录
        record_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        cursor.execute('''
            INSERT INTO checkin_records (record_id, student_id, checkin_type)
            VALUES (?, ?, ?)
        ''', (record_id, student_id, checkin_type))
        
        conn.commit()
        return True, "签到成功", student_name
    except Exception as e:
        conn.rollback()
        return False, f"签到失败: {str(e)}", None


def get_checkin_records(student_id=None, date=None):
    """获取签到记录（包含学生姓名）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT cr.record_id, cr.student_id, cr.checkin_time, cr.checkin_type,
               s.name as student_name
        FROM checkin_records cr
        LEFT JOIN students s ON cr.student_id = s.student_id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND cr.student_id = ?'
        params.append(student_id)
    
    if date:
        query += ' AND DATE(cr.checkin_time) = ?'
        params.append(date)
    
    query += ' ORDER BY cr.checkin_time DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    return [
        {
            'record_id': row['record_id'],
            'student_id': row['student_id'],
            'student_name': row['student_name'] or row['student_id'],
            'checkin_time': row['checkin_time'],
            'checkin_type': row['checkin_type']
        }
        for row in rows
    ]


def get_score_logs(student_id=None, class_name=None, student_name=None):
    """获取分数变更日志
    
    Args:
        student_id: 学号筛选（可选）
        class_name: 班级筛选（可选）
        student_name: 学生姓名筛选（可选）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 使用 JOIN 关联 students 表以支持按班级和姓名筛选
    query = '''
        SELECT 
            sl.log_id, 
            sl.student_id, 
            sl.score_change, 
            sl.reason, 
            sl.operation_time,
            s.name as student_name,
            s.class_name
        FROM score_logs sl
        LEFT JOIN students s ON sl.student_id = s.student_id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND sl.student_id = ?'
        params.append(student_id)
    
    if class_name:
        query += ' AND s.class_name = ?'
        params.append(class_name)
    
    if student_name:
        query += ' AND s.name LIKE ?'
        params.append(f'%{student_name}%')
    
    query += ' ORDER BY sl.operation_time DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    return [
        {
            'log_id': row['log_id'],
            'student_id': row['student_id'],
            'student_name': row['student_name'],
            'class_name': row['class_name'],
            'score_change': row['score_change'],
            'reason': row['reason'],
            'operation_time': row['operation_time']
        }
        for row in rows
    ]


def delete_student(student_id):
    """删除学生，同时清空该学生的签到记录和分数变更日志"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 先检查学生是否存在
        cursor.execute('SELECT name FROM students WHERE student_id = ?', (student_id,))
        row = cursor.fetchone()
        if not row:
            return False, "学生不存在"
        
        student_name = row['name']
        
        # 删除该学生的签到记录
        cursor.execute('DELETE FROM checkin_records WHERE student_id = ?', (student_id,))
        checkin_deleted = cursor.rowcount
        
        # 删除该学生的分数变更日志
        cursor.execute('DELETE FROM score_logs WHERE student_id = ?', (student_id,))
        score_logs_deleted = cursor.rowcount
        
        # 删除学生
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            message = f"成功删除学生 '{student_name}'"
            if checkin_deleted > 0:
                message += f"，清空 {checkin_deleted} 条签到记录"
            if score_logs_deleted > 0:
                message += f"，清空 {score_logs_deleted} 条分数变更日志"
            return True, message
        return False, "学生不存在"
    except Exception as e:
        conn.rollback()
        return False, f"删除失败: {str(e)}"


def delete_class(class_name):
    """删除整个班级，同时清空该班级所有学生的签到记录和分数变更日志"""
    print(f"[delete_class] 接收到的班级名: {repr(class_name)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 先查看数据库中有哪些班级
        cursor.execute('SELECT DISTINCT class_name FROM students')
        all_classes = [row['class_name'] for row in cursor.fetchall()]
        print(f"[delete_class] 数据库中所有班级: {all_classes}")
        
        # 先统计要删除的学生数量
        cursor.execute('SELECT COUNT(*) as count FROM students WHERE class_name = ?', (class_name,))
        result = cursor.fetchone()
        count = result['count'] if result else 0
        print(f"[delete_class] 班级 '{class_name}' 的学生数量: {count}")
        
        if count == 0:
            return False, "该班级不存在或没有学生"
        
        # 获取该班级所有学生的学号
        cursor.execute('SELECT student_id FROM students WHERE class_name = ?', (class_name,))
        student_ids = [row['student_id'] for row in cursor.fetchall()]
        print(f"[delete_class] 要删除的学生: {student_ids}")
        
        # 批量删除该班级所有学生的签到记录和分数日志（使用 IN 子句更高效）
        placeholders = ','.join('?' * len(student_ids))
        
        # 删除签到记录
        cursor.execute(f'DELETE FROM checkin_records WHERE student_id IN ({placeholders})', student_ids)
        checkin_deleted = cursor.rowcount
        
        # 删除分数变更日志
        cursor.execute(f'DELETE FROM score_logs WHERE student_id IN ({placeholders})', student_ids)
        score_logs_deleted = cursor.rowcount
        
        print(f"[delete_class] 已删除 {checkin_deleted} 条签到记录, {score_logs_deleted} 条分数变更日志")
        
        # 删除该班级的所有学生
        cursor.execute('DELETE FROM students WHERE class_name = ?', (class_name,))
        conn.commit()
        
        print(f"[delete_class] 成功删除班级 '{class_name}' 的 {count} 名学生")
        message = f"成功删除班级 '{class_name}' 的 {count} 名学生"
        if checkin_deleted > 0:
            message += f"，清空 {checkin_deleted} 条签到记录"
        if score_logs_deleted > 0:
            message += f"，清空 {score_logs_deleted} 条分数变更日志"
        return True, message
    except Exception as e:
        conn.rollback()
        print(f"[delete_class] 删除失败: {str(e)}")
        return False, f"删除班级失败: {str(e)}"


# 上课状态管琁函数
def set_current_class(class_name):
    """设置当前上课班级"""
    global current_class_session
    
    # 如果 class_name 为空，表示结束上课，清除今天的签到记录
    if not class_name:
        success, message = clear_today_checkin_records()
        current_class_session = {
            'class_name': None,
            'start_time': None,
            'active': False
        }
        return True, f"已结束上课，{message}"
    
    current_class_session = {
        'class_name': class_name,
        'start_time': datetime.now().isoformat(),
        'active': True
    }
    return True, f"当前上课班级: {class_name}"


def get_current_class():
    """获取当前上课班级信息"""
    return current_class_session


def get_class_students_with_checkin_status(class_name):
    """获取班级学生及其签到状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取班级所有学生
    cursor.execute('''
        SELECT student_id, name, score 
        FROM students 
        WHERE class_name = ?
        ORDER BY student_id
    ''', (class_name,))
    
    students = cursor.fetchall()
    if not students:
        return []
    
    # 获取今天的签到记录
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT student_id, checkin_time
        FROM checkin_records
        WHERE DATE(checkin_time) = ?
    ''', (today,))
    
    checkin_records = {row['student_id']: row['checkin_time'] for row in cursor.fetchall()}
    
    # 组合数据
    result = []
    for student in students:
        result.append({
            'student_id': student['student_id'],
            'name': student['name'],
            'score': student['score'],
            'checked_in': student['student_id'] in checkin_records,
            'checkin_time': checkin_records.get(student['student_id'])
        })
    
    return result


def clear_today_checkin_records():
    """清除今天的所有签到记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            DELETE FROM checkin_records
            WHERE DATE(checkin_time) = ?
        ''', (today,))
        conn.commit()
        return True, f"已清除今天的 {cursor.rowcount} 条签到记录"
    except Exception as e:
        conn.rollback()
        return False, f"清除签到记录失败: {str(e)}"


def reset_all_scores(default_score=70):
    """重置所有学生的分数为指定值（默认70分）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE students SET score = ?', (default_score,))
        conn.commit()
        
        affected_count = cursor.rowcount
        return True, f"成功重置 {affected_count} 名学生的分数为 {default_score} 分"
    except Exception as e:
        conn.rollback()
        return False, f"重置失败: {str(e)}"


# 初始化
def init_data():
    """初始化数据"""
    init_db()
