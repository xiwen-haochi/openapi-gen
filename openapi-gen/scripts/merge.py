#!/usr/bin/env python3
"""
OpenAPI YAML 合并脚本
从 JSONL 中间文件（endpoints.jsonl + schemas.jsonl）组装完整的 OpenAPI 3.1.0 YAML。

用法：
    python merge.py <work-dir> [--output <output-path>]

参数：
    work-dir     工作目录，包含 metadata.json、endpoints.jsonl、schemas.jsonl
    --output     输出文件路径，默认为 <work-dir>/../openapi.yaml

退出码：
    0 — 合并成功
    1 — 合并失败
"""

import json
import os
import sys
from collections import OrderedDict

try:
    import yaml
except ImportError:
    print("错误: 需要安装 PyYAML — pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# YAML OrderedDict 支持 — 保持键顺序
# ---------------------------------------------------------------------------
def _dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


yaml.add_representer(OrderedDict, _dict_representer)


def od(*pairs):
    """快捷创建 OrderedDict。"""
    return OrderedDict(pairs)


# ---------------------------------------------------------------------------
# 读取 JSONL
# ---------------------------------------------------------------------------
def read_jsonl(path):
    """逐行读取 JSONL 文件，跳过空行。"""
    records = []
    if not os.path.exists(path):
        return records
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print("警告: %s 第 %d 行 JSON 解析失败: %s" % (os.path.basename(path), lineno, e))
    return records


# ---------------------------------------------------------------------------
# 构建 components/schemas
# ---------------------------------------------------------------------------
def build_schemas(schema_records):
    schemas = OrderedDict()
    for rec in schema_records:
        name = rec.get("name")
        if not name:
            continue
        schema = OrderedDict()
        schema["type"] = rec.get("type", "object")
        if rec.get("description"):
            schema["description"] = rec["description"]

        # required 字段列表
        required = [
            f["name"] for f in rec.get("fields", []) if f.get("required")
        ]
        if required:
            schema["required"] = required

        # properties
        props = OrderedDict()
        for field in rec.get("fields", []):
            fname = field.get("name")
            if not fname:
                continue
            prop = OrderedDict()
            prop["type"] = field.get("type", "string")
            if field.get("format"):
                prop["format"] = field["format"]
            if field.get("description"):
                prop["description"] = field["description"]
            # 约束
            for constraint in (
                "minLength", "maxLength", "minimum", "maximum",
                "pattern", "default", "readOnly", "writeOnly",
            ):
                if constraint in field:
                    prop[constraint] = field[constraint]
            if "enum" in field:
                prop["enum"] = field["enum"]
            if "example" in field:
                prop["example"] = field["example"]
            # 嵌套引用
            if field.get("ref"):
                prop["$ref"] = "#/components/schemas/%s" % field["ref"]
            if field.get("items_ref"):
                prop["type"] = "array"
                prop["items"] = {"$ref": "#/components/schemas/%s" % field["items_ref"]}
            if field.get("items_type"):
                prop["type"] = "array"
                prop["items"] = {"type": field["items_type"]}
            props[fname] = prop

        if props:
            schema["properties"] = props
        schemas[name] = schema
    return schemas


# ---------------------------------------------------------------------------
# 构建 paths
# ---------------------------------------------------------------------------
def build_paths(endpoint_records):
    paths = OrderedDict()
    for rec in endpoint_records:
        path_str = rec.get("path")
        method = rec.get("method", "get").lower()
        if not path_str:
            continue

        if path_str not in paths:
            paths[path_str] = OrderedDict()

        operation = OrderedDict()
        if rec.get("tags"):
            operation["tags"] = rec["tags"]
        if rec.get("summary"):
            operation["summary"] = rec["summary"]
        if rec.get("description"):
            operation["description"] = rec["description"]
        if rec.get("operationId"):
            operation["operationId"] = rec["operationId"]

        # parameters
        params = []
        for p in rec.get("parameters", []):
            param = OrderedDict()
            param["name"] = p["name"]
            param["in"] = p.get("in", "query")
            if p.get("in") == "path":
                param["required"] = True
            elif "required" in p:
                param["required"] = p["required"]
            if p.get("description"):
                param["description"] = p["description"]
            schema = OrderedDict()
            schema["type"] = p.get("type", "string")
            if p.get("format"):
                schema["format"] = p["format"]
            if "default" in p:
                schema["default"] = p["default"]
            if "example" in p:
                schema["example"] = p["example"]
            if "enum" in p:
                schema["enum"] = p["enum"]
            if "minimum" in p:
                schema["minimum"] = p["minimum"]
            if "maximum" in p:
                schema["maximum"] = p["maximum"]
            param["schema"] = schema
            params.append(param)
        if params:
            operation["parameters"] = params

        # requestBody
        rb = rec.get("requestBody")
        if rb:
            request_body = OrderedDict()
            request_body["required"] = rb.get("required", True)
            if rb.get("description"):
                request_body["description"] = rb["description"]
            content_type = rb.get("contentType", "application/json")
            content = OrderedDict()
            if rb.get("schema_ref"):
                content["schema"] = {"$ref": "#/components/schemas/%s" % rb["schema_ref"]}
            elif rb.get("schema"):
                content["schema"] = rb["schema"]
            if rb.get("example"):
                content["example"] = rb["example"]
            request_body["content"] = {content_type: content}
            operation["requestBody"] = request_body

        # responses
        responses = OrderedDict()
        for code, resp in rec.get("responses", {}).items():
            code_str = str(code)
            resp_obj = OrderedDict()
            resp_obj["description"] = resp.get("description", "成功")
            if resp.get("schema_ref"):
                resp_obj["content"] = {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/%s" % resp["schema_ref"]}
                    }
                }
            if resp.get("example"):
                if "content" not in resp_obj:
                    resp_obj["content"] = {"application/json": {}}
                resp_obj["content"]["application/json"]["example"] = resp["example"]
            responses[code_str] = resp_obj
        if responses:
            operation["responses"] = responses

        # security（接口级别）
        if rec.get("security"):
            operation["security"] = rec["security"]

        paths[path_str][method] = operation
    return paths


# ---------------------------------------------------------------------------
# 收集 tags
# ---------------------------------------------------------------------------
def collect_tags(endpoint_records, metadata):
    """从接口记录和 metadata 中收集所有 tag。"""
    tag_map = OrderedDict()
    # 优先使用 metadata 中预定义的 tags
    for t in metadata.get("tags", []):
        tag_map[t["name"]] = t.get("description", "")
    # 从接口中补充
    for rec in endpoint_records:
        for tag_name in rec.get("tags", []):
            if tag_name not in tag_map:
                tag_map[tag_name] = ""
    return [
        od(("name", name), ("description", desc)) if desc else od(("name", name))
        for name, desc in tag_map.items()
    ]


# ---------------------------------------------------------------------------
# 主合并逻辑
# ---------------------------------------------------------------------------
def merge(work_dir, output_path=None):
    """合并 JSONL 中间文件为 OpenAPI YAML，返回错误列表。"""
    errors = []

    if not os.path.isdir(work_dir):
        return ["工作目录不存在: %s" % work_dir]

    # 读取 metadata
    meta_path = os.path.join(work_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # 读取 JSONL
    endpoints = read_jsonl(os.path.join(work_dir, "endpoints.jsonl"))
    schemas_records = read_jsonl(os.path.join(work_dir, "schemas.jsonl"))

    if not endpoints:
        errors.append("endpoints.jsonl 为空，无可合并的接口")
        return errors

    # 构建文档
    doc = OrderedDict()
    doc["openapi"] = "3.1.0"

    # info
    info = OrderedDict()
    info["title"] = metadata.get("project_name", "API 文档")
    info["version"] = metadata.get("version", "1.0.0")
    if metadata.get("description"):
        info["description"] = metadata["description"]
    if metadata.get("contact"):
        info["contact"] = metadata["contact"]
    doc["info"] = info

    # servers
    servers = metadata.get("servers", [
        {"url": "http://localhost:8080", "description": "本地开发环境"}
    ])
    doc["servers"] = servers

    # tags
    tags = collect_tags(endpoints, metadata)
    if tags:
        doc["tags"] = tags

    # paths
    doc["paths"] = build_paths(endpoints)

    # components
    components = OrderedDict()
    built_schemas = build_schemas(schemas_records)

    # 添加通用 ErrorResponse（如果不存在）
    if "ErrorResponse" not in built_schemas:
        built_schemas["ErrorResponse"] = od(
            ("type", "object"),
            ("description", "通用错误响应"),
            ("properties", od(
                ("code", od(("type", "integer"), ("description", "错误码"), ("example", 400))),
                ("message", od(("type", "string"), ("description", "错误信息"), ("example", "参数校验失败"))),
            )),
        )

    components["schemas"] = built_schemas

    # securitySchemes
    if metadata.get("securitySchemes"):
        components["securitySchemes"] = metadata["securitySchemes"]
    doc["components"] = components

    # security
    if metadata.get("security"):
        doc["security"] = metadata["security"]

    # 输出
    if output_path is None:
        output_path = os.path.join(os.path.dirname(work_dir), "openapi.yaml")

    yaml_str = yaml.dump(
        doc,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )

    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_str)

    print("✅ 合并完成: %s" % output_path)
    print("   接口数: %d，模型数: %d" % (len(endpoints), len(schemas_records)))
    return errors


def main():
    if len(sys.argv) < 2:
        print("用法: %s <work-dir> [--output <output-path>]" % sys.argv[0])
        sys.exit(1)

    work_dir = sys.argv[1]
    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    errors = merge(work_dir, output_path)
    if errors:
        print("\n❌ 合并时发现 %d 个问题：" % len(errors))
        for i, err in enumerate(errors, 1):
            print("  %d. %s" % (i, err))
        sys.exit(1)


if __name__ == "__main__":
    main()
