"""
数据库管理 API 控制器
提供数据库索引、迁移和优化管理功能（管理员）
"""
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from infrastructure.persistence.database import Database
from infrastructure.persistence.index_manager import IndexManager, RECOMMENDED_INDEXES
from infrastructure.persistence.migration_manager import MigrationManager
from infrastructure.security.session import require_admin
from infrastructure.logging import logger
from infrastructure.config import get_db_settings

router = APIRouter(prefix="/api/admin/database", tags=["database-admin"])


class IndexInfo(BaseModel):
    """索引信息"""
    name: str
    table: str
    columns: List[str]


class MigrationStatus(BaseModel):
    """迁移状态"""
    current_version: int
    latest_version: int
    applied_count: int
    pending_count: int


@router.get("/indexes", response_model=dict)
async def get_indexes(request: Request):
    """获取数据库索引列表"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        existing = manager.get_existing_indexes()
        
        return {
            'success': True,
            'data': {
                'count': len(existing),
                'indexes': existing
            }
        }
        
    except Exception as e:
        logger.error(f"获取索引列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexes/create", response_model=dict)
async def create_indexes(request: Request):
    """创建所有推荐索引"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        results = manager.create_recommended_indexes()
        
        return {
            'success': True,
            'message': f"索引创建完成",
            'data': {
                'created': results['created'],
                'skipped': results['skipped'],
                'failed': results['failed'],
                'created_count': len(results['created']),
                'skipped_count': len(results['skipped']),
                'failed_count': len(results['failed'])
            }
        }
        
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/indexes/{index_name}", response_model=dict)
async def drop_index(request: Request, index_name: str):
    """删除指定索引"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        if manager.drop_index(index_name):
            return {
                'success': True,
                'message': f'索引 {index_name} 已删除'
            }
        else:
            raise HTTPException(status_code=500, detail='删除索引失败')
        
    except Exception as e:
        logger.error(f"删除索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables", response_model=dict)
async def get_table_stats(request: Request):
    """获取所有表的统计信息"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        stats = manager.get_table_stats()
        
        return {
            'success': True,
            'data': stats
        }
        
    except Exception as e:
        logger.error(f"获取表统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize", response_model=dict)
async def optimize_database(request: Request):
    """优化数据库（VACUUM + ANALYZE）"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        results = manager.optimize_database()
        
        return {
            'success': True,
            'message': '数据库优化完成',
            'data': results
        }
        
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migrations", response_model=dict)
async def get_migration_status(request: Request):
    """获取迁移状态"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = MigrationManager(settings.path)
        
        status = manager.get_migration_status()
        
        return {
            'success': True,
            'data': status
        }
        
    except Exception as e:
        logger.error(f"获取迁移状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrations/run", response_model=dict)
async def run_migrations(request: Request):
    """运行待处理的迁移"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = MigrationManager(settings.path)
        
        results = manager.migrate()
        
        return {
            'success': True,
            'message': '迁移执行完成',
            'data': {
                'applied': results['applied'],
                'skipped': results['skipped'],
                'failed': results['failed']
            }
        }
        
    except Exception as e:
        logger.error(f"运行迁移失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/validate", response_model=dict)
async def validate_schema(request: Request):
    """验证数据库结构完整性"""
    require_admin(request)
    
    try:
        settings = get_db_settings()
        manager = MigrationManager(settings.path)
        
        issues = manager.validate_schema()
        
        is_valid = (
            len(issues['missing_tables']) == 0 and
            len(issues['missing_columns']) == 0
        )
        
        return {
            'success': True,
            'data': {
                'is_valid': is_valid,
                'issues': issues
            }
        }
        
    except Exception as e:
        logger.error(f"验证数据库结构失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/analyze", response_model=dict)
async def analyze_query(
    request: Request,
    query: str = Query(..., description="要分析的 SQL 查询")
):
    """分析查询执行计划"""
    require_admin(request)
    
    # 安全检查：只允许 SELECT 查询
    query_lower = query.strip().lower()
    if not query_lower.startswith('select'):
        raise HTTPException(status_code=400, detail='只允许分析 SELECT 查询')
    
    try:
        settings = get_db_settings()
        manager = IndexManager(settings.path)
        
        plan = manager.analyze_query(query)
        
        return {
            'success': True,
            'data': plan
        }
        
    except Exception as e:
        logger.error(f"分析查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
