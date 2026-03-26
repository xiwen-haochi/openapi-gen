#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理分批模式工作目录。

用法：
    python cleanup.py <openapi-gen-dir>

示例：
    python cleanup.py .openapi_gen

将删除 <openapi-gen-dir>/_work/ 目录及其所有内容。
"""

import shutil
import sys
import os


def main():
    if len(sys.argv) < 2:
        print("用法: %s <openapi-gen-dir>" % sys.argv[0])
        print("示例: %s .openapi_gen" % sys.argv[0])
        sys.exit(1)

    base_dir = sys.argv[1]
    work_dir = os.path.join(base_dir, "_work")

    if not os.path.isdir(work_dir):
        print("工作目录不存在，无需清理: %s" % work_dir)
        sys.exit(0)

    # 统计文件数
    file_count = 0
    for _root, _dirs, files in os.walk(work_dir):
        file_count += len(files)

    shutil.rmtree(work_dir)
    print("已清理工作目录: %s（共 %d 个文件）" % (work_dir, file_count))


if __name__ == "__main__":
    main()
