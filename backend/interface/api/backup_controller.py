"""
备份管理 API 控制器
提供备份查看、创建、删除、恢复功能（管理员）
"""
import os
import subprocess
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from infrastructure.security.session import require_admin
from infrastructure.logging import logger

router = APIRouter(prefix="/api/admin/backup", tags=["backup-admin"])

# 备份配置
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "backup", "data")
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "class_system.db")


class BackupInfo(BaseModel):
    """备份信息"""
    filename: str
    size: str
    size_bytes: int
    created_at: str
    age_days: int


class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: List[BackupInfo]
    total_count: int
    total_size: str


@router.get("/list", response_model=dict)
async def list_backups(
    request: Request,
    limit: int = Query(50, ge=1, le=100)
):
    """获取备份列表"""
    require_admin(request)
    
    try:
        if not os.path.exists(BACKUP_DIR):
            return {
                'success': True,
                'data': {
                    'backups': [],
                    'total_count': 0,
                    'total_size': '0B'
                }
            }
        
        backups = []
        total_size = 0
        
        # 获取所有备份文件
        files = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('class_system_') and (filename.endswith('.db') or filename.endswith('.db.gz')):
                filepath = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size_bytes': stat.st_size,
                        'mtime': stat.st_mtime
                    })
        
        # 按时间倒序排序
        files.sort(key=lambda x: x['mtime'], reverse=True)
        
        for file_info in files[:limit]:
            size_bytes = file_info['size_bytes']
            total_size += size_bytes
            
            # 格式化文件大小
            if size_bytes > 1073741824:
                size_str = f"{size_bytes / 1073741824:.2f} GB"
            elif size_bytes > 1048576:
                size_str = f"{size_bytes / 1048576:.2f} MB"
            elif size_bytes > 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes} B"
            
            # 计算文件年龄
            age_days = (datetime.now().timestamp() - file_info['mtime']) / 86400
            
            backups.append({
                'filename': file_info['filename'],
                'size': size_str,
                'size_bytes': size_bytes,
                'created_at': datetime.fromtimestamp(file_info['mtime']).isoformat(),
                'age_days': int(age_days)
            })
        
        # 格式化总大小
        if total_size > 1073741824:
            total_size_str = f"{total_size / 1073741824:.2f} GB"
        elif total_size > 1048576:
            total_size_str = f"{total_size / 1048576:.2f} MB"
        elif total_size > 1024:
            total_size_str = f"{total_size / 1024:.2f} KB"
        else:
            total_size_str = f"{total_size} B"
        
        return {
            'success': True,
            'data': {
                'backups': backups,
                'total_count': len(backups),
                'total_size': total_size_str
            }
        }
        
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=dict)
async def create_backup(request: Request):
    """立即创建备份"""
    require_admin(request)
    
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "backup", "backup-data.sh")
        
        if not os.path.exists(script_path):
            raise HTTPException(status_code=500, detail="备份脚本不存在")
        
        # 执行备份脚本
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"备份失败: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"备份失败: {result.stderr}")
        
        return {
            'success': True,
            'message': '备份创建成功',
            'data': {
                'output': result.stdout
            }
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="备份超时")
    except Exception as e:
        logger.error(f"创建备份失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup", response_model=dict)
async def cleanup_old_backups(
    request: Request,
    keep_days: int = Query(30, ge=1, le=365)
):
    """清理旧备份"""
    require_admin(request)
    
    try:
        if not os.path.exists(BACKUP_DIR):
            return {
                'success': True,
                'message': '备份目录不存在',
                'data': {'deleted_count': 0}
            }
        
        deleted_count = 0
        deleted_size = 0
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('class_system_') and (filename.endswith('.db') or filename.endswith('.db.gz')):
                filepath = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(filepath):
                    # 计算文件年龄
                    age_days = (datetime.now().timestamp() - os.stat(filepath).st_mtime) / 86400
                    
                    if age_days > keep_days:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                        logger.info(f"删除旧备份: {filename}")
        
        return {
            'success': True,
            'message': f'清理完成，删除 {deleted_count} 个备份',
            'data': {
                'deleted_count': deleted_count,
                'deleted_size_bytes': deleted_size,
                'keep_days': keep_days
            }
        }
        
    except Exception as e:
        logger.error(f"清理备份失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}", response_model=dict)
async def delete_backup(request: Request, filename: str):
    """删除指定备份"""
    require_admin(request)
    
    try:
        # 安全检查：只允许删除 class_system_ 开头的文件
        if not filename.startswith('class_system_'):
            raise HTTPException(status_code=400, detail='无效的文件名')
        
        if '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail='非法的文件名')
        
        filepath = os.path.join(BACKUP_DIR, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail='备份文件不存在')
        
        os.remove(filepath)
        logger.info(f"删除备份: {filename}")
        
        return {
            'success': True,
            'message': f'备份 {filename} 已删除'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_backup_stats(request: Request):
    """获取备份统计信息"""
    require_admin(request)
    
    try:
        if not os.path.exists(BACKUP_DIR):
            return {
                'success': True,
                'data': {
                    'total_count': 0,
                    'total_size': 0,
                    'oldest_backup': None,
                    'newest_backup': None
                }
            }
        
        files = []
        total_size = 0
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('class_system_') and (filename.endswith('.db') or filename.endswith('.db.gz')):
                filepath = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    })
                    total_size += stat.st_size
        
        if not files:
            return {
                'success': True,
                'data': {
                    'total_count': 0,
                    'total_size': 0,
                    'oldest_backup': None,
                    'newest_backup': None
                }
            }
        
        # 排序获取最老和最新的备份
        files.sort(key=lambda x: x['mtime'])
        
        return {
            'success': True,
            'data': {
                'total_count': len(files),
                'total_size': total_size,
                'total_size_human': format_size(total_size),
                'oldest_backup': {
                    'filename': files[0]['filename'],
                    'created_at': datetime.fromtimestamp(files[0]['mtime']).isoformat()
                },
                'newest_backup': {
                    'filename': files[-1]['filename'],
                    'created_at': datetime.fromtimestamp(files[-1]['mtime']).isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取备份统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes > 1073741824:
        return f"{size_bytes / 1073741824:.2f} GB"
    elif size_bytes > 1048576:
        return f"{size_bytes / 1048576:.2f} MB"
    elif size_bytes > 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"
