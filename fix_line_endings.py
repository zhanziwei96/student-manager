#!/usr/bin/env python3
"""
修复脚本换行符问题
在 Linux 上运行: python3 fix_line_endings.py
"""
import os
import stat

files = ['start_dev.sh', 'start_dev_simple.sh', 'start_dev_tmux.sh', 'stop_dev.sh']

for filename in files:
    if not os.path.exists(filename):
        print(f'跳过: {filename} (文件不存在)')
        continue
    
    # 读取文件
    with open(filename, 'rb') as f:
        content = f.read()
    
    # 检查是否有 Windows 换行符
    if b'\r\n' not in content:
        print(f'跳过: {filename} (已经是 Unix 格式)')
        # 确保有执行权限
        os.chmod(filename, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        continue
    
    # 替换 CRLF 为 LF
    content = content.replace(b'\r\n', b'\n')
    
    # 写回文件
    with open(filename, 'wb') as f:
        f.write(content)
    
    # 添加执行权限
    os.chmod(filename, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    
    print(f'已修复: {filename}')

print('')
print('所有脚本已转换为 Unix 格式，现在可以运行:')
print('  ./start_dev_tmux.sh')
