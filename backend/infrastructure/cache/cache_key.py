"""
缓存键构建器
生成规范化的缓存键，避免键冲突
"""
import hashlib
import json
from typing import Any, Optional, Dict


class CacheKeyBuilder:
    """
    缓存键构建器
    
    规范缓存键格式：app:{module}:{resource}:{identifier}:{action}
    示例：
        - app:student:list:all
        - app:student:detail:2024001
        - app:stats:class:class_a
    """
    
    # 应用前缀
    PREFIX = "app"
    
    # 模块名
    MODULE_STUDENT = "student"
    MODULE_USER = "user"
    MODULE_CHECKIN = "checkin"
    MODULE_AUDIT = "audit"
    MODULE_STATS = "stats"
    MODULE_CLASS = "class"
    
    # 资源类型
    RESOURCE_LIST = "list"
    RESOURCE_DETAIL = "detail"
    RESOURCE_STATS = "stats"
    RESOURCE_COUNT = "count"
    RESOURCE_SEARCH = "search"
    
    @classmethod
    def build(
        cls,
        module: str,
        resource: str,
        identifier: Optional[str] = None,
        action: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建缓存键
        
        Args:
            module: 模块名（student, user, checkin, audit, stats）
            resource: 资源类型（list, detail, stats, count, search）
            identifier: 标识符（如学生ID、班级名等）
            action: 动作/视图名
            params: 查询参数，用于生成哈希
            
        Returns:
            缓存键字符串
        """
        parts = [cls.PREFIX, module, resource]
        
        if identifier:
            # 清理标识符中的特殊字符
            clean_id = str(identifier).replace(':', '_').replace(' ', '_')
            parts.append(clean_id)
        
        if action:
            parts.append(action)
        
        key = ':'.join(parts)
        
        # 如果有参数，追加参数哈希
        if params:
            param_hash = cls._hash_params(params)
            key = f"{key}:{param_hash}"
        
        return key
    
    @classmethod
    def _hash_params(cls, params: Dict[str, Any]) -> str:
        """对参数进行哈希，生成短字符串"""
        # 排序确保一致性
        sorted_params = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:8]
    
    # ========== 便捷方法 ==========
    
    @classmethod
    def student_list(cls, class_name: Optional[str] = None) -> str:
        """学生列表缓存键"""
        if class_name:
            return cls.build(cls.MODULE_STUDENT, cls.RESOURCE_LIST, 
                           identifier=f"class_{class_name}")
        return cls.build(cls.MODULE_STUDENT, cls.RESOURCE_LIST, identifier="all")
    
    @classmethod
    def student_detail(cls, student_id: str) -> str:
        """学生详情缓存键"""
        return cls.build(cls.MODULE_STUDENT, cls.RESOURCE_DETAIL, 
                        identifier=student_id)
    
    @classmethod
    def student_stats(cls) -> str:
        """学生统计缓存键"""
        return cls.build(cls.MODULE_STUDENT, cls.RESOURCE_STATS)
    
    @classmethod
    def user_list(cls) -> str:
        """用户列表缓存键"""
        return cls.build(cls.MODULE_USER, cls.RESOURCE_LIST)
    
    @classmethod
    def user_detail(cls, user_id: int) -> str:
        """用户详情缓存键"""
        return cls.build(cls.MODULE_USER, cls.RESOURCE_DETAIL, 
                        identifier=str(user_id))
    
    @classmethod
    def checkin_list(cls, **filters) -> str:
        """签到列表缓存键"""
        return cls.build(cls.MODULE_CHECKIN, cls.RESOURCE_LIST, 
                        params=filters if filters else None)
    
    @classmethod
    def checkin_stats(cls, class_name: Optional[str] = None) -> str:
        """签到统计缓存键"""
        if class_name:
            return cls.build(cls.MODULE_CHECKIN, cls.RESOURCE_STATS,
                           identifier=f"class_{class_name}")
        return cls.build(cls.MODULE_CHECKIN, cls.RESOURCE_STATS)
    
    @classmethod
    def audit_logs(cls, **filters) -> str:
        """审计日志缓存键"""
        return cls.build(cls.MODULE_AUDIT, cls.RESOURCE_LIST,
                        params=filters if filters else None)
    
    @classmethod
    def audit_stats(cls, days: int = 7) -> str:
        """审计统计缓存键"""
        return cls.build(cls.MODULE_AUDIT, cls.RESOURCE_STATS,
                        identifier=f"days_{days}")
    
    @classmethod
    def class_list(cls) -> str:
        """班级列表缓存键"""
        return cls.build(cls.MODULE_CLASS, cls.RESOURCE_LIST)
    
    @classmethod
    def class_stats(cls, class_name: str) -> str:
        """班级统计缓存键"""
        return cls.build(cls.MODULE_CLASS, cls.RESOURCE_STATS,
                        identifier=class_name)
    
    # ========== 模式匹配 ==========
    
    @classmethod
    def pattern_student_all(cls) -> str:
        """匹配所有学生相关缓存"""
        return f"{cls.PREFIX}:{cls.MODULE_STUDENT}:*"
    
    @classmethod
    def pattern_checkin_all(cls) -> str:
        """匹配所有签到相关缓存"""
        return f"{cls.PREFIX}:{cls.MODULE_CHECKIN}:*"
    
    @classmethod
    def pattern_audit_all(cls) -> str:
        """匹配所有审计日志相关缓存"""
        return f"{cls.PREFIX}:{cls.MODULE_AUDIT}:*"
    
    @classmethod
    def pattern_stats_all(cls) -> str:
        """匹配所有统计相关缓存"""
        return f"{cls.PREFIX}:{cls.MODULE_STATS}:*"
