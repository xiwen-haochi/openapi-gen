#!/usr/bin/env python3
"""
OpenAPI YAML 验证脚本
验证生成的 openapi.yaml 是否为合法的 YAML 且符合基本 OpenAPI 3.1.0 结构。

用法：
    python validate.py <path-to-openapi.yaml>

退出码：
    0 — 验证通过
    1 — 验证失败
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML — pip install pyyaml")
    sys.exit(1)


def validate(file_path: str) -> list[str]:
    """验证 OpenAPI YAML 文件，返回错误列表（空列表 = 通过）。"""
    errors: list[str] = []
    path = Path(file_path)

    if not path.exists():
        return [f"文件不存在: {file_path}"]

    # 1. YAML 语法解析
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"YAML 语法错误: {e}"]

    if not isinstance(doc, dict):
        return ["YAML 顶层必须是对象（mapping）"]

    # 2. OpenAPI 版本
    openapi_ver = doc.get("openapi")
    if not openapi_ver:
        errors.append("缺少 openapi 版本字段")
    elif not str(openapi_ver).startswith("3.1"):
        errors.append(f"openapi 版本应为 3.1.x，当前为 {openapi_ver}")

    # 3. info 块
    info = doc.get("info")
    if not isinstance(info, dict):
        errors.append("缺少 info 块")
    else:
        if not info.get("title"):
            errors.append("info.title 不能为空")
        if not info.get("version"):
            errors.append("info.version 不能为空")

    # 4. paths 块
    paths = doc.get("paths")
    if not isinstance(paths, dict) or len(paths) == 0:
        errors.append("paths 为空，至少应包含一个接口路径")
    else:
        http_methods = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
        for route, methods in paths.items():
            if not route.startswith("/"):
                errors.append(f"路径 {route} 应以 '/' 开头")
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method in ("summary", "description", "parameters", "servers"):
                    continue  # 路径级别公共字段
                if method not in http_methods:
                    errors.append(f"路径 {route} 下存在未知方法: {method}")
                    continue
                if not isinstance(operation, dict):
                    continue
                if not operation.get("summary") and not operation.get("description"):
                    errors.append(f"{method.upper()} {route} 缺少 summary 或 description")
                if not operation.get("responses"):
                    errors.append(f"{method.upper()} {route} 缺少 responses")

    # 5. $ref 引用完整性
    schemas = {}
    components = doc.get("components")
    if isinstance(components, dict):
        schemas = components.get("schemas", {})
        responses = components.get("responses", {})
        parameters = components.get("parameters", {})
    else:
        responses = {}
        parameters = {}

    def collect_refs(node, path_prefix=""):
        """递归收集所有 $ref。"""
        refs = []
        if isinstance(node, dict):
            if "$ref" in node:
                refs.append((path_prefix, node["$ref"]))
            for k, v in node.items():
                refs.extend(collect_refs(v, f"{path_prefix}/{k}"))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                refs.extend(collect_refs(v, f"{path_prefix}[{i}]"))
        return refs

    all_refs = collect_refs(doc)
    for location, ref in all_refs:
        if not ref.startswith("#/components/"):
            continue
        parts = ref.replace("#/", "").split("/")
        # 检查引用目标是否存在
        target = doc
        for part in parts:
            if isinstance(target, dict):
                target = target.get(part)
            else:
                target = None
                break
        if target is None:
            errors.append(f"引用 {ref} 目标不存在（位于 {location}）")

    return errors


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <openapi.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]
    errors = validate(file_path)

    if errors:
        print(f"❌ 验证失败，共 {len(errors)} 个问题：\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        sys.exit(1)
    else:
        print("✅ 验证通过，OpenAPI 文件结构正确。")
        sys.exit(0)


if __name__ == "__main__":
    main()
