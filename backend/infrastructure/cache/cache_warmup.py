"""
缓存预热服务
在应用启动时预热常用数据
"""
from typing import List, Optional
from infrastructure.cache.cache_client import get_cache_client, CacheClient
from infrastructure.cache.cache_key import CacheKeyBuilder
from infrastructure.config import CacheConfig
from infrastructure.logging import logger


class CacheWarmupService:
    """
    缓存预热服务
    
    在应用启动时预加载热点数据到缓存，减少冷启动延迟。
    """
    
    def __init__(self, cache: Optional[CacheClient] = None):
        self.cache = cache or get_cache_client()
    
    async def warmup_all(self):
        """预热所有常用数据"""
        if not self.cache.is_connected:
            logger.info("Cache not connected, skipping warmup")
            return
        
        logger.info("Starting cache warmup...")
        
        # 预热班级列表
        await self.warmup_class_list()
        
        # 预热学生统计
        await self.warmup_student_stats()
        
        # 预热用户列表
        await self.warmup_user_list()
        
        logger.info("Cache warmup completed")
    
    async def warmup_class_list(self):
        """预热班级列表"""
        try:
            from infrastructure.persistence.database import Database
            from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
            
            db = Database()
            repo = SQLiteStudentRepository(db)
            
            # 获取所有学生，提取班级列表
            students = repo.find_all()
            classes = set()
            for student in students:
                if student.class_name:
                    classes.add(student.class_name)
            
            class_list = sorted(list(classes))
            
            # 缓存班级列表
            key = CacheKeyBuilder.class_list()
            await self.cache.set_json(key, class_list, ttl=CacheConfig.CLASS_LIST_TTL_SECONDS)
            
            logger.info(f"Warmed up class list: {len(class_list)} classes")
            
        except Exception as e:
            logger.warning(f"Failed to warmup class list: {e}")
    
    async def warmup_student_stats(self):
        """预热学生统计"""
        try:
            from infrastructure.persistence.database import Database
            
            db = Database()
            
            with db.connection() as conn:
                # 总学生数
                cursor = conn.execute("SELECT COUNT(*) as count FROM students")
                total = cursor.fetchone()['count']
                
                # 班级统计
                cursor = conn.execute(
                    "SELECT class_name, COUNT(*) as count FROM students GROUP BY class_name"
                )
                class_stats = [
                    {'class_name': row['class_name'], 'count': row['count']}
                    for row in cursor.fetchall()
                ]
                
                # 平均分
                cursor = conn.execute("SELECT AVG(score) as avg FROM students")
                avg_score = cursor.fetchone()['avg'] or 0
            
            stats = {
                'total_students': total,
                'class_count': len(class_stats),
                'class_stats': class_stats,
                'average_score': round(avg_score, 2)  # 保留两位小数
            }
            
            # 缓存统计
            key = CacheKeyBuilder.student_stats()
            await self.cache.set_json(key, stats, ttl=CacheConfig.STATS_TTL_SECONDS)
            
            logger.info(f"Warmed up student stats: {total} students")
            
        except Exception as e:
            logger.warning(f"Failed to warmup student stats: {e}")
    
    async def warmup_user_list(self):
        """预热用户列表"""
        try:
            from infrastructure.persistence.database import Database
            from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
            
            db = Database()
            repo = SQLiteUserRepository(db)
            
            users = repo.find_all()
            user_list = [
                {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role.value,
                    'status': user.status.value
                }
                for user in users
            ]
            
            # 缓存用户列表
            key = CacheKeyBuilder.user_list()
            await self.cache.set_json(key, user_list, ttl=CacheConfig.USER_LIST_TTL_SECONDS)
            
            logger.info(f"Warmed up user list: {len(user_list)} users")
            
        except Exception as e:
            logger.warning(f"Failed to warmup user list: {e}")
    
    async def warmup_student_list(self, class_name: Optional[str] = None):
        """
        预热学生列表
        
        Args:
            class_name: 特定班级，None 表示所有学生
        """
        try:
            from infrastructure.persistence.database import Database
            from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
            
            db = Database()
            repo = SQLiteStudentRepository(db)
            
            if class_name:
                students = repo.find_by_class(class_name)
            else:
                students = repo.find_all()
            
            student_list = [
                {
                    'student_id': str(s.student_id),
                    'name': s.name,
                    'class_name': s.class_name,
                    'score': float(s.score)
                }
                for s in students
            ]
            
            # 缓存
            key = CacheKeyBuilder.student_list(class_name)
            await self.cache.set_json(key, student_list, ttl=CacheConfig.STUDENT_LIST_TTL_SECONDS)
            
            logger.info(f"Warmed up student list: {len(student_list)} students")
            
        except Exception as e:
            logger.warning(f"Failed to warmup student list: {e}")
    
    async def clear_all_cache(self):
        """清除所有应用缓存"""
        if not self.cache.is_connected:
            return
        
        try:
            # 删除所有以 app: 开头的键
            count = await self.cache.delete_pattern("app:*")
            logger.info(f"Cleared {count} cache entries")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


# 便捷函数
async def warmup_cache():
    """便捷函数：预热缓存"""
    service = CacheWarmupService()
    await service.warmup_all()


async def clear_cache():
    """便捷函数：清除缓存"""
    service = CacheWarmupService()
    await service.clear_all_cache()
