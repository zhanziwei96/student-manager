"""
文件上传安全处理模块 - SEC-001: 文件上传缺乏安全控制

提供安全的文件上传处理功能:
- 文件类型白名单验证
- 文件大小限制
- 文件名安全处理（UUID重命名）
- 路径遍历攻击防护
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException

from app.core.config import get_settings, HttpStatus
from app.core.logging import logger


# 危险文件扩展名黑名单（始终禁止）
DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.aspx',
    '.py', '.pyw', '.rb', '.pl', '.cgi', '.jar', '.war', '.ear', '.ps1',
    '.vbs', '.js', '.wsf', '.hta', '.scr', '.com', '.pif', '.msi'
}

# 危险的MIME类型黑名单
DANGEROUS_CONTENT_TYPES = {
    'application/x-msdownload',
    'application/x-exe',
    'application/x-dosexec',
    'application/x-sh',
    'application/x-php',
    'application/x-python-code',
    'text/x-python',
    'application/javascript',
    'text/javascript',
    'application/x-msdos-program',
}


def _validate_filename(filename: str) -> str:
    """
    验证文件名安全性
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
        
    Raises:
        HTTPException: 文件名不安全时抛出
    """
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    # 清理文件名：移除路径分隔符和危险字符
    # 路径遍历攻击防护：移除 ../ 和 ./
    dangerous_patterns = ['../', '..\\', './', '.\\', '..', '/', '\\']
    cleaned = filename
    for pattern in dangerous_patterns:
        cleaned = cleaned.replace(pattern, '')
    
    # 再次检查是否还有危险字符
    if '..' in cleaned or '/' in cleaned or '\\' in cleaned:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="文件名包含非法字符"
        )
    
    cleaned = cleaned.strip()
    if not cleaned:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="文件名无效"
        )
    
    return cleaned


def _get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）
    
    Args:
        filename: 文件名
        
    Returns:
        str: 小写扩展名（包含点，如 .xlsx）
    """
    return Path(filename).suffix.lower()


def _validate_extension(
    filename: str,
    allowed_extensions: List[str]
) -> None:
    """
    验证文件扩展名是否在白名单中
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表
        
    Raises:
        HTTPException: 扩展名不合法时抛出
    """
    ext = _get_file_extension(filename)
    
    # 检查是否有扩展名
    if not ext:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="文件缺少扩展名"
        )
    
    # 检查是否在危险扩展名列表中
    if ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"不安全的文件类型: {ext}"
        )
    
    # 检查是否在允许列表中
    allowed_lower = [e.lower() for e in allowed_extensions]
    if ext not in allowed_lower:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}，仅支持: {', '.join(allowed_extensions)}"
        )


def _validate_content_type(
    content_type: Optional[str],
    allowed_content_types: List[str]
) -> None:
    """
    验证MIME类型
    
    Args:
        content_type: 文件的MIME类型
        allowed_content_types: 允许的MIME类型列表
        
    Raises:
        HTTPException: MIME类型不合法时抛出
    """
    if not content_type:
        return  # 允许未知MIME类型，依赖扩展名验证
    
    content_type_lower = content_type.lower()
    
    # 检查是否在危险MIME类型列表中
    if content_type_lower in DANGEROUS_CONTENT_TYPES:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"不安全的文件类型: {content_type}"
        )
    
    # 检查是否在允许列表中（如果指定了允许列表）
    if allowed_content_types:
        allowed_lower = [ct.lower() for ct in allowed_content_types]
        if content_type_lower not in allowed_lower:
            # MIME类型不匹配但扩展名正确时，仅记录警告
            # 因为浏览器可能发送不准确的MIME类型
            logger.warning(f"MIME类型不匹配: {content_type}，依赖扩展名验证")


def _generate_safe_filename(original_filename: str, use_uuid: bool = True) -> str:
    """
    生成安全的文件名
    
    Args:
        original_filename: 原始文件名
        use_uuid: 是否使用UUID作为文件名
        
    Returns:
        str: 安全的文件名
    """
    ext = _get_file_extension(original_filename)
    
    if use_uuid:
        # 使用UUID作为文件名，保留原始扩展名
        return f"{uuid.uuid4().hex}{ext}"
    else:
        # 清理原始文件名但保留名称
        name = Path(original_filename).stem
        # 移除危险字符，限制长度
        safe_name = "".join(c for c in name if c.isalnum() or c in '._-').strip()
        safe_name = safe_name[:100]  # 限制文件名长度
        if not safe_name:
            safe_name = "upload"
        return f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"


def _ensure_upload_directory(directory: str) -> Path:
    """
    确保上传目录存在
    
    Args:
        directory: 上传目录路径
        
    Returns:
        Path: 上传目录的Path对象
    """
    upload_dir = Path(directory)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _validate_file_size(size: int, max_size_mb: int) -> None:
    """
    验证文件大小
    
    Args:
        size: 文件大小（字节）
        max_size_mb: 最大允许大小（MB）
        
    Raises:
        HTTPException: 文件大小超出限制时抛出
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if size > max_size_bytes:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"文件大小超过限制 ({max_size_mb}MB)"
        )


async def save_upload_file_securely(
    upload_file: UploadFile,
    allowed_extensions: List[str] = None,
    allowed_content_types: List[str] = None,
    max_size_mb: int = None,
    use_uuid: bool = True,
    upload_directory: str = None,
    validate_content: bool = True
) -> Tuple[str, str]:
    """
    安全保存上传文件
    
    执行完整的安全验证并保存文件:
    1. 验证文件名安全性（防止路径遍历）
    2. 验证文件扩展名白名单
    3. 验证MIME类型
    4. 验证文件大小
    5. 使用UUID重命名文件
    6. 保存到隔离目录
    
    Args:
        upload_file: FastAPI上传文件对象
        allowed_extensions: 允许的扩展名列表（默认从配置读取）
        allowed_content_types: 允许的MIME类型列表（默认从配置读取）
        max_size_mb: 最大文件大小MB（默认从配置读取）
        use_uuid: 是否使用UUID重命名（默认True）
        upload_directory: 上传目录（默认从配置读取）
        validate_content: 是否验证文件内容（默认True）
        
    Returns:
        Tuple[str, str]: (保存的文件绝对路径, 原始文件名)
        
    Raises:
        HTTPException: 验证失败时抛出400错误
    """
    settings = get_settings()
    
    # 使用配置默认值
    if allowed_extensions is None:
        allowed_extensions = settings.upload.allowed_extensions
    if allowed_content_types is None:
        allowed_content_types = settings.upload.allowed_content_types
    if max_size_mb is None:
        max_size_mb = settings.upload.max_file_size_mb
    if upload_directory is None:
        upload_directory = settings.upload.directory
    
    # 获取原始文件名
    original_filename = upload_file.filename or "unnamed"
    
    # 1. 验证文件名安全性
    cleaned_filename = _validate_filename(original_filename)
    
    # 2. 验证扩展名
    _validate_extension(cleaned_filename, allowed_extensions)
    
    # 3. 验证MIME类型
    _validate_content_type(upload_file.content_type, allowed_content_types)
    
    # 4. 预检查Content-Length（如果可用）
    # FastAPI的UploadFile不直接提供大小，需要在读取时检查
    
    # 5. 生成安全文件名
    safe_filename = _generate_safe_filename(cleaned_filename, use_uuid)
    
    # 6. 确保上传目录存在
    upload_dir = _ensure_upload_directory(upload_directory)
    file_path = upload_dir / safe_filename
    
    # 确保生成的路径仍在上传目录内（防止路径遍历）
    try:
        file_path.resolve().relative_to(upload_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="无效的文件路径"
        )
    
    # 7. 保存文件并检查大小
    try:
        total_size = 0
        max_bytes = max_size_mb * 1024 * 1024
        
        with open(file_path, "wb") as buffer:
            # 分块读取并检查大小
            chunk_size = 8192  # 8KB chunks
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > max_bytes:
                    # 删除已写入的部分文件
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=HttpStatus.BAD_REQUEST,
                        detail=f"文件大小超过限制 ({max_size_mb}MB)"
                    )
                buffer.write(chunk)
        
        logger.info(f"文件上传成功: {original_filename} -> {safe_filename} ({total_size} bytes)")
        return str(file_path.resolve()), original_filename
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理可能的残留文件
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        logger.error(f"文件保存失败: {e}")
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_ERROR,
            detail="文件保存失败"
        )


def cleanup_file(file_path: str) -> bool:
    """
    清理上传的临时文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否成功删除
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"已清理临时文件: {file_path}")
            return True
        return False
    except Exception as e:
        logger.warning(f"清理文件失败 {file_path}: {e}")
        return False


def cleanup_directory(directory: str, max_age_hours: int = 24) -> int:
    """
    清理上传目录中的旧文件
    
    Args:
        directory: 目录路径
        max_age_hours: 文件最大保留时间（小时）
        
    Returns:
        int: 删除的文件数量
    """
    from datetime import datetime, timedelta
    
    try:
        upload_dir = Path(directory)
        if not upload_dir.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"已清理旧文件: {file_path}")
                except Exception as e:
                    logger.warning(f"无法清理文件 {file_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"清理完成: 删除了 {deleted_count} 个旧文件")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"清理目录失败 {directory}: {e}")
        return 0
