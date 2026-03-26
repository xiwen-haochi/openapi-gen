#!/usr/bin/env python3
"""
OpenAPI YAML 验证脚本
验证生成的 openapi.yaml 是否为合法的 YAML 且符合基本 OpenAPI 3.1.0 结构。
也支持验证 JSONL 中间文件（分批模式下的 endpoints.jsonl / schemas.jsonl）。

用法：
    python validate.py <path-to-openapi.yaml>
    python validate.py --jsonl <work-dir>

退出码：
    0 — 验证通过
    1 — 验证失败
"""

import json
import sys
import os

try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML — pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# JSONL 中间文件验证（分批模式预检）
# ---------------------------------------------------------------------------
def validate_jsonl(work_dir):
    """验证分批模式工作目录下的 JSONL 中间文件，返回错误列表。"""
    errors = []
    work = work_dir

    if not os.path.isdir(work):
        return ["工作目录不存在: %s" % work_dir]

    endpoints_path = os.path.join(work, "endpoints.jsonl")
    schemas_path = os.path.join(work, "schemas.jsonl")

    # 检查 endpoints.jsonl
    if not os.path.exists(endpoints_path):
        errors.append("缺少 endpoints.jsonl 文件")
    else:
        schema_refs_used = set()
        endpoints = []
        with open(endpoints_path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    ep = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append("endpoints.jsonl 第 %d 行 JSON 格式错误: %s" % (lineno, e))
                    continue
                endpoints.append(ep)
                # 必填字段
                if not ep.get("method"):
                    errors.append("endpoints.jsonl 第 %d 行缺少 method" % lineno)
                if not ep.get("path"):
                    errors.append("endpoints.jsonl 第 %d 行缺少 path" % lineno)
                elif not ep["path"].startswith("/"):
                    errors.append("endpoints.jsonl 第 %d 行 path 应以 / 开头: %s" % (lineno, ep['path']))
                if not ep.get("summary") and not ep.get("description"):
                    errors.append("endpoints.jsonl 第 %d 行缺少 summary 或 description" % lineno)
                # 收集引用的 schema
                for resp in ep.get("responses", {}).values():
                    if isinstance(resp, dict) and resp.get("schema_ref"):
                        schema_refs_used.add(resp["schema_ref"])
                rb = ep.get("requestBody")
                if isinstance(rb, dict) and rb.get("schema_ref"):
                    schema_refs_used.add(rb["schema_ref"])

        if not endpoints:
            errors.append("endpoints.jsonl 为空")

        # 检查 schemas.jsonl 中的引用完整性
        schema_names = set()
        if os.path.exists(schemas_path):
            with open(schemas_path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        sc = json.loads(line)
                    except (json.JSONDecodeError, ValueError) as e:
                        errors.append("schemas.jsonl 第 %d 行 JSON 格式错误: %s" % (lineno, e))
                        continue
                    name = sc.get("name")
                    if not name:
                        errors.append("schemas.jsonl 第 %d 行缺少 name" % lineno)
                    else:
                        schema_names.add(name)
                    if not sc.get("fields") and not sc.get("enum"):
                        errors.append("schemas.jsonl 第 %d 行 (%s) 缺少 fields 或 enum" % (lineno, name))

        # 自动忽略 ErrorResponse（merge.py 会自动补充）
        schema_refs_used.discard("ErrorResponse")
        missing = schema_refs_used - schema_names
        if missing:
            errors.append("以下 schema 被接口引用但未在 schemas.jsonl 中定义: %s" % ', '.join(sorted(missing)))

    return errors


def validate(file_path):
    """验证 OpenAPI YAML 文件，返回错误列表（空列表 = 通过）。"""
    errors = []

    if not os.path.exists(file_path):
        return ["文件不存在: %s" % file_path]

    # 1. YAML 语法解析
    try:
        with open(file_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return ["YAML 语法错误: %s" % e]

    if not isinstance(doc, dict):
        return ["YAML 顶层必须是对象（mapping）"]

    # 2. OpenAPI 版本
    openapi_ver = doc.get("openapi")
    if not openapi_ver:
        errors.append("缺少 openapi 版本字段")
    elif not str(openapi_ver).startswith("3.1"):
        errors.append("openapi 版本应为 3.1.x，当前为 %s" % openapi_ver)

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
                errors.append("路径 %s 应以 '/' 开头" % route)
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method in ("summary", "description", "parameters", "servers"):
                    continue  # 路径级别公共字段
                if method not in http_methods:
                    errors.append("路径 %s 下存在未知方法: %s" % (route, method))
                    continue
                if not isinstance(operation, dict):
                    continue
                if not operation.get("summary") and not operation.get("description"):
                    errors.append("%s %s 缺少 summary 或 description" % (method.upper(), route))
                if not operation.get("responses"):
                    errors.append("%s %s 缺少 responses" % (method.upper(), route))

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
                refs.extend(collect_refs(v, "%s/%s" % (path_prefix, k)))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                refs.extend(collect_refs(v, "%s[%d]" % (path_prefix, i)))
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
            errors.append("引用 %s 目标不存在（位于 %s）" % (ref, location))

    return errors


def main():
    if len(sys.argv) < 2:
        print("用法: %s <openapi.yaml>" % sys.argv[0])
        print("      %s --jsonl <work-dir>" % sys.argv[0])
        sys.exit(1)

    # JSONL 预检模式
    if sys.argv[1] == "--jsonl":
        if len(sys.argv) < 3:
            print("用法: %s --jsonl <work-dir>" % sys.argv[0])
            sys.exit(1)
        errors = validate_jsonl(sys.argv[2])
        if errors:
            print("❌ JSONL 预检失败，共 %d 个问题：\n" % len(errors))
            for i, err in enumerate(errors, 1):
                print("  %d. %s" % (i, err))
            sys.exit(1)
        else:
            print("✅ JSONL 预检通过，中间文件结构正确。")
            sys.exit(0)

    # OpenAPI YAML 验证模式
    file_path = sys.argv[1]
    errors = validate(file_path)

    if errors:
        print("❌ 验证失败，共 %d 个问题：\n" % len(errors))
        for i, err in enumerate(errors, 1):
            print("  %d. %s" % (i, err))
        sys.exit(1)
    else:
        print("✅ 验证通过，OpenAPI 文件结构正确。")
        sys.exit(0)


if __name__ == "__main__":
    main()
