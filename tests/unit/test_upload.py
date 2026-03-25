"""
文件上传安全测试 - SEC-001: 文件上传缺乏安全控制

测试安全上传功能的各个方面:
- 文件类型验证
- 文件大小限制
- 文件名安全处理
- 路径遍历防护
"""
import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi import UploadFile, HTTPException

# Python 3.7 兼容：AsyncMock 在 3.8+ 才有
try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(Mock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)

from app.core.upload import (
    save_upload_file_securely,
    cleanup_file,
    cleanup_directory,
    _validate_filename,
    _validate_extension,
    _validate_content_type,
    _generate_safe_filename,
    _ensure_upload_directory,
    DANGEROUS_EXTENSIONS,
    DANGEROUS_CONTENT_TYPES,
)


class TestValidateFilename:
    """文件名验证测试"""
    
    def test_valid_filename(self):
        """正常文件名通过验证"""
        result = _validate_filename("students.xlsx")
        assert result == "students.xlsx"
    
    def test_filename_with_spaces(self):
        """带空格的文件名"""
        result = _validate_filename("student list.xlsx")
        assert result == "student list.xlsx"
    
    def test_empty_filename(self):
        """空文件名被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_filename("")
        assert exc_info.value.status_code == 400
        assert "不能为空" in exc_info.value.detail
    
    def test_whitespace_only_filename(self):
        """仅空白的文件名被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_filename("   ")
        assert exc_info.value.status_code == 400
    
    def test_path_traversal_double_dot(self):
        """路径遍历 ../ 被清理"""
        # 路径遍历会被清理而非抛出异常
        result = _validate_filename("../../../etc/passwd")
        # 清理后应该是安全的文件名
        assert ".." not in result
        assert "/" not in result
        assert result == "etcpasswd"
    
    def test_path_traversal_single_dot(self):
        """路径遍历 ./ 被清理"""
        result = _validate_filename("./config.py")
        assert ".." not in result
        assert result == "config.py"
    
    def test_path_traversal_mixed(self):
        """混合路径遍历被清理"""
        result = _validate_filename("..\\..\\windows\\system32\\cmd.exe")
        assert ".." not in result
        assert "\\" not in result
        assert result == "windowssystem32cmd.exe"


class TestValidateExtension:
    """文件扩展名验证测试"""
    
    def test_allowed_extension(self):
        """允许的扩展名通过验证"""
        # 不应抛出异常
        _validate_extension("students.xlsx", [".xlsx", ".xls"])
    
    def test_case_insensitive_extension(self):
        """扩展名不区分大小写"""
        _validate_extension("students.XLSX", [".xlsx", ".xls"])
        _validate_extension("students.Xls", [".xlsx", ".xls"])
    
    def test_no_extension(self):
        """无扩展名被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_extension("students", [".xlsx"])
        assert exc_info.value.status_code == 400
        assert "缺少扩展名" in exc_info.value.detail
    
    def test_not_allowed_extension(self):
        """不允许的扩展名被拒绝（.py在危险列表中）"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_extension("script.py", [".xlsx", ".xls"])
        assert exc_info.value.status_code == 400
        # .py 在 DANGEROUS_EXTENSIONS 中，所以报错是"不安全"
        assert "不安全" in exc_info.value.detail or "不支持" in exc_info.value.detail
    
    def test_dangerous_extension_exe(self):
        """可执行文件被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_extension("virus.exe", [".xlsx"])
        assert exc_info.value.status_code == 400
        assert "不安全" in exc_info.value.detail
    
    def test_dangerous_extension_php(self):
        """PHP文件被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_extension("shell.php", [".xlsx"])
        assert exc_info.value.status_code == 400
    
    @pytest.mark.parametrize("ext", list(DANGEROUS_EXTENSIONS))
    def test_all_dangerous_extensions(self, ext):
        """所有危险扩展名都被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_extension(f"file{ext}", [".xlsx", ".pdf"])
        assert exc_info.value.status_code == 400


class TestValidateContentType:
    """MIME类型验证测试"""
    
    def test_allowed_content_type(self):
        """允许的MIME类型通过"""
        # 不应抛出异常
        _validate_content_type(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
        )
    
    def test_none_content_type(self):
        """None MIME类型允许通过（依赖扩展名验证）"""
        _validate_content_type(None, ["application/json"])
    
    def test_empty_content_type(self):
        """空MIME类型允许通过"""
        _validate_content_type("", ["application/json"])
    
    def test_dangerous_content_type(self):
        """危险MIME类型被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_content_type("application/x-msdownload", [".xlsx"])
        assert exc_info.value.status_code == 400
        assert "不安全" in exc_info.value.detail
    
    @pytest.mark.parametrize("ct", list(DANGEROUS_CONTENT_TYPES))
    def test_all_dangerous_content_types(self, ct):
        """所有危险MIME类型都被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            _validate_content_type(ct, ["application/json"])
        assert exc_info.value.status_code == 400


class TestGenerateSafeFilename:
    """安全文件名生成测试"""
    
    def test_uuid_filename(self):
        """UUID重命名生成唯一文件名"""
        result = _generate_safe_filename("students.xlsx", use_uuid=True)
        assert result.endswith(".xlsx")
        # UUID hex 是 32 位（不含 dashes）+ .xlsx (5) = 37
        assert len(result) == 32 + 5  # UUID hex (32) + .xlsx (5)
        assert result != "students.xlsx"
    
    def test_uuid_unique(self):
        """每次生成不同的UUID文件名"""
        result1 = _generate_safe_filename("students.xlsx", use_uuid=True)
        result2 = _generate_safe_filename("students.xlsx", use_uuid=True)
        assert result1 != result2
    
    def test_preserve_original_name(self):
        """不强制UUID时保留原始名称"""
        result = _generate_safe_filename("students.xlsx", use_uuid=False)
        assert "students" in result
        assert result.endswith(".xlsx")
        # 应该添加了随机后缀
        assert len(result) > len("students.xlsx")
    
    def test_long_filename_truncated(self):
        """长文件名被截断"""
        long_name = "a" * 200 + ".xlsx"
        result = _generate_safe_filename(long_name, use_uuid=False)
        assert len(result) < 150  # 应该被截断


class TestEnsureUploadDirectory:
    """上传目录确保测试"""
    
    def test_create_directory(self, tmp_path):
        """创建上传目录"""
        test_dir = tmp_path / "uploads" / "test"
        result = _ensure_upload_directory(str(test_dir))
        assert test_dir.exists()
        assert result == test_dir
    
    def test_directory_already_exists(self, tmp_path):
        """目录已存在时不报错"""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        result = _ensure_upload_directory(str(test_dir))
        assert result == test_dir


class TestSaveUploadFileSecurely:
    """安全保存文件集成测试"""
    
    @pytest.fixture
    def mock_upload_file(self):
        """创建模拟上传文件"""
        file = Mock(spec=UploadFile)
        file.filename = "students.xlsx"
        file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        file.read = AsyncMock(return_value=b"")
        return file
    
    @pytest.fixture
    def upload_settings(self, tmp_path):
        """测试上传配置"""
        return {
            "allowed_extensions": [".xlsx", ".xls"],
            "allowed_content_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ],
            "max_size_mb": 10,
            "upload_directory": str(tmp_path / "uploads"),
        }
    
    @pytest.mark.asyncio
    async def test_save_valid_file(self, mock_upload_file, upload_settings, tmp_path):
        """成功保存有效文件"""
        file_content = b"Fake Excel content"
        mock_upload_file.read = AsyncMock(side_effect=[file_content, b""])
        
        with patch("app.core.upload.get_settings") as mock_settings:
            mock_settings.return_value.upload.allowed_extensions = upload_settings["allowed_extensions"]
            mock_settings.return_value.upload.allowed_content_types = upload_settings["allowed_content_types"]
            mock_settings.return_value.upload.max_file_size_mb = upload_settings["max_size_mb"]
            mock_settings.return_value.upload.directory = upload_settings["upload_directory"]
            mock_settings.return_value.upload.use_uuid_filename = True
            
            file_path, original_name = await save_upload_file_securely(mock_upload_file)
        
        assert original_name == "students.xlsx"
        assert Path(file_path).exists()
        assert Path(file_path).name.endswith(".xlsx")
        assert Path(file_path).name != "students.xlsx"  # UUID重命名
    
    @pytest.mark.asyncio
    async def test_reject_wrong_extension(self, mock_upload_file, upload_settings):
        """拒绝错误扩展名"""
        mock_upload_file.filename = "script.txt"
        
        with pytest.raises(HTTPException) as exc_info:
            with patch("app.core.upload.get_settings") as mock_settings:
                mock_settings.return_value.upload.allowed_extensions = upload_settings["allowed_extensions"]
                await save_upload_file_securely(mock_upload_file)
        
        assert exc_info.value.status_code == 400
        assert "不支持" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_reject_oversized_file(self, mock_upload_file, upload_settings, tmp_path):
        """拒绝超大文件"""
        # 创建1MB的测试内容
        large_content = b"x" * (1024 * 1024)
        mock_upload_file.read = AsyncMock(side_effect=[large_content, large_content, b""])
        mock_upload_file.filename = "large.xlsx"
        
        with pytest.raises(HTTPException) as exc_info:
            with patch("app.core.upload.get_settings") as mock_settings:
                mock_settings.return_value.upload.allowed_extensions = upload_settings["allowed_extensions"]
                mock_settings.return_value.upload.allowed_content_types = upload_settings["allowed_content_types"]
                mock_settings.return_value.upload.max_file_size_mb = 1  # 1MB限制
                mock_settings.return_value.upload.directory = str(tmp_path / "uploads")
                mock_settings.return_value.upload.use_uuid_filename = True
                
                await save_upload_file_securely(mock_upload_file)
        
        assert exc_info.value.status_code == 400
        assert "超过限制" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_reject_path_traversal_cleaned(self, mock_upload_file, upload_settings, tmp_path):
        """路径遍历被清理后正常保存"""
        mock_upload_file.filename = "../../../etc/passwd.xlsx"
        file_content = b"Fake Excel content"
        mock_upload_file.read = AsyncMock(side_effect=[file_content, b""])
        
        with patch("app.core.upload.get_settings") as mock_settings:
            mock_settings.return_value.upload.allowed_extensions = upload_settings["allowed_extensions"]
            mock_settings.return_value.upload.allowed_content_types = upload_settings["allowed_content_types"]
            mock_settings.return_value.upload.max_file_size_mb = upload_settings["max_size_mb"]
            mock_settings.return_value.upload.directory = str(tmp_path / "uploads")
            mock_settings.return_value.upload.use_uuid_filename = True
            
            file_path, original_name = await save_upload_file_securely(mock_upload_file)
        
        # 路径遍历被清理，文件正常保存
        assert Path(file_path).exists()
        assert ".." not in Path(file_path).name
        assert "/" not in Path(file_path).name
    
    @pytest.mark.asyncio
    async def test_reject_dangerous_extension(self, mock_upload_file, upload_settings):
        """拒绝危险扩展名"""
        mock_upload_file.filename = "virus.exe"
        
        with pytest.raises(HTTPException) as exc_info:
            with patch("app.core.upload.get_settings") as mock_settings:
                mock_settings.return_value.upload.allowed_extensions = [".exe"]  # 即使允许也被黑名单拦截
                await save_upload_file_securely(mock_upload_file)
        
        assert exc_info.value.status_code == 400
        assert "不安全" in exc_info.value.detail


class TestCleanupFile:
    """文件清理测试"""
    
    def test_cleanup_existing_file(self, tmp_path):
        """清理存在的文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = cleanup_file(str(test_file))
        assert result is True
        assert not test_file.exists()
    
    def test_cleanup_nonexistent_file(self, tmp_path):
        """清理不存在的文件返回False"""
        test_file = tmp_path / "nonexistent.txt"
        
        result = cleanup_file(str(test_file))
        assert result is False
    
    def test_cleanup_directory(self, tmp_path):
        """清理目录返回False（不删除目录）"""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        
        result = cleanup_file(str(test_dir))
        assert result is False
        assert test_dir.exists()


class TestCleanupDirectory:
    """目录清理测试"""
    
    def test_cleanup_old_files(self, tmp_path):
        """清理旧文件"""
        import time
        
        # 创建测试目录
        test_dir = tmp_path / "uploads"
        test_dir.mkdir()
        
        # 创建旧文件（模拟2天前）
        old_file = test_dir / "old.xlsx"
        old_file.write_text("old content")
        old_time = time.time() - (2 * 24 * 3600)  # 2天前
        os.utime(old_file, (old_time, old_time))
        
        # 创建新文件
        new_file = test_dir / "new.xlsx"
        new_file.write_text("new content")
        
        # 清理超过1天的文件
        count = cleanup_directory(str(test_dir), max_age_hours=24)
        
        assert count == 1
        assert not old_file.exists()
        assert new_file.exists()
    
    def test_cleanup_empty_directory(self, tmp_path):
        """清理空目录"""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()
        
        count = cleanup_directory(str(test_dir), max_age_hours=1)
        assert count == 0
    
    def test_cleanup_nonexistent_directory(self, tmp_path):
        """清理不存在的目录"""
        count = cleanup_directory(str(tmp_path / "nonexistent"), max_age_hours=1)
        assert count == 0
