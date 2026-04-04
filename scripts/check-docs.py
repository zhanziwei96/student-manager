#!/usr/bin/env python3
"""
文档检查和验证脚本

功能：
1. 检查文档中的内部链接是否有效
2. 验证测试统计数据一致性
3. 检查文档版本标记
4. 生成文档健康报告

使用方法：
    python scripts/check-docs.py

退出码：
    0 - 所有检查通过
    1 - 发现错误或警告
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs"
AGENTS_DIR = ROOT_DIR / ".agents"

# 期望的测试统计数据
EXPECTED_STATS = {
    "backend_tests": 467,
    "backend_files": 43,
    "frontend_tests": 130,
    "frontend_files": 16,
}


def get_all_markdown_files() -> List[Path]:
    """获取所有 markdown 文件"""
    files = []
    for pattern in ["*.md", "**/*.md"]:
        files.extend(ROOT_DIR.glob(pattern))
    return [f for f in files if ".git" not in str(f)]


def check_internal_links(content: str, file_path: Path) -> List[str]:
    """检查内部链接是否有效"""
    errors = []

    # 匹配 markdown 链接: [text](path)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_pattern, content)

    for text, link_path in links:
        # 跳过外部链接
        if link_path.startswith(("http://", "https://", "#", "mailto:")):
            continue

        # 处理相对路径
        if link_path.startswith("./") or link_path.startswith("../"):
            target = (file_path.parent / link_path).resolve()
        else:
            target = ROOT_DIR / link_path

        # 检查文件是否存在
        if not target.exists():
            errors.append(f"   broken link: [{text}]({link_path}) -> {target}")

    return errors


def check_test_stats(content: str, file_path: Path) -> List[str]:
    """检查测试统计数据一致性"""
    errors = []
    file_name = file_path.name

    # 只在特定文件中检查测试统计
    test_related_files = ['README.md', 'TEST_GUIDE.md', 'OPTIMIZATION_PLAN.md']
    if not any(name in file_name for name in test_related_files):
        return errors

    # 只匹配精确的测试用例数描述（排除"测试文件数"）
    # 匹配格式: "467 个测试用例" 或 "全部测试（467个）" 或 "467 个测试全部通过"

    # 后端：查找包含测试数量关键字的行
    for line in content.split('\n'):
        # 排除测试文件数的行
        if '测试文件' in line or '文件数' in line:
            continue

        # 匹配后端测试数 (467)
        backend_match = re.search(r'(?:后端|Backend|pytest|全部测试).*?(\d+)\s*个测试(?:用例|全部通过)?', line, re.IGNORECASE)
        if backend_match:
            count = int(backend_match.group(1))
            # 只检查明确的测试数量（不是文件数）
            if count < 100:  # 文件数通常小于100
                continue
            if count != EXPECTED_STATS["backend_tests"]:
                errors.append(
                    f"  不一致的后端测试数: {count} (期望: {EXPECTED_STATS['backend_tests']}) [行: {line.strip()[:50]}]"
                )

        # 匹配前端测试数 (130)
        frontend_match = re.search(r'(?:前端|Frontend|Vitest).*?(\d+)\s*个测试(?:用例|全部通过)?', line, re.IGNORECASE)
        if frontend_match:
            count = int(frontend_match.group(1))
            # 只检查明确的测试数量（不是文件数）
            if count < 50:  # 文件数通常小于50
                continue
            if count != EXPECTED_STATS["frontend_tests"]:
                errors.append(
                    f"  不一致的前端测试数: {count} (期望: {EXPECTED_STATS['frontend_tests']}) [行: {line.strip()[:50]}]"
                )

    return errors


def check_version_header(content: str, file_path: Path) -> List[str]:
    """检查文档是否有版本标记头"""
    errors = []

    # 跳过根目录的 README.md 和 CLAUDE.md
    if file_path.name in ["README.md", "CLAUDE.md"]:
        return errors

    # 检查是否有版本标记
    required_fields = ["文档版本", "最后更新", "适用版本"]
    missing = []

    for field in required_fields:
        if field not in content:
            missing.append(field)

    if missing:
        errors.append(f"  缺少版本标记: {', '.join(missing)}")

    return errors


def check_cross_references() -> List[str]:
    """检查交叉引用的一致性"""
    errors = []

    # 检查 CLAUDE.md 中的文档索引是否都存在
    claude_md = ROOT_DIR / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")

        # 提取文档索引中的链接
        doc_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, link_path in doc_links:
            if link_path.startswith(("http://", "https://")):
                continue

            # 只检查 .md 文件
            if not link_path.endswith(".md"):
                continue

            target = ROOT_DIR / link_path
            if not target.exists():
                errors.append(f"CLAUDE.md 中的链接失效: [{text}]({link_path})")

    return errors


def generate_report(results: Dict[str, List[str]]) -> str:
    """生成检查报告"""
    lines = ["=" * 60, "文档检查报告", "=" * 60, ""]

    total_errors = 0
    total_warnings = 0

    for file_path, errors in results.items():
        if not errors:
            continue

        lines.append(f"\n📄 {file_path}")
        lines.append("-" * 40)

        for error in errors:
            lines.append(error)
            if "broken link" in error or "不一致" in error:
                total_errors += 1
            elif "缺少" in error:
                total_warnings += 1

    lines.extend([
        "",
        "=" * 60,
        f"总结: {total_errors} 个错误, {total_warnings} 个警告",
        "=" * 60,
    ])

    if total_errors == 0 and total_warnings == 0:
        lines.append("\n✅ 所有检查通过！")
    elif total_errors == 0:
        lines.append("\n⚠️  存在警告，建议修复")
    else:
        lines.append("\n❌ 存在错误，需要修复")

    return "\n".join(lines)


def main():
    """主函数"""
    print("🔍 开始检查文档...\n")

    md_files = get_all_markdown_files()
    results = {}

    for file_path in md_files:
        # 跳过 node_modules 等目录
        if any(skip in str(file_path) for skip in ["node_modules", ".git", "__pycache__"]):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            results[str(file_path)] = [f"  无法读取文件: {e}"]
            continue

        errors = []

        # 检查内部链接
        errors.extend(check_internal_links(content, file_path))

        # 检查测试统计数据
        errors.extend(check_test_stats(content, file_path))

        # 检查版本标记
        errors.extend(check_version_header(content, file_path))

        if errors:
            results[str(file_path.relative_to(ROOT_DIR))] = errors

    # 检查交叉引用
    cross_ref_errors = check_cross_references()
    if cross_ref_errors:
        results["交叉引用检查"] = cross_ref_errors

    # 生成并打印报告
    report = generate_report(results)
    print(report)

    # 返回退出码
    has_errors = any(
        "broken link" in str(e) or "不一致" in str(e)
        for errors in results.values()
        for e in errors
    )

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
