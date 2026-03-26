---
name: openapi-gen
description: >-
  自动阅读项目源代码，反推所有 API 接口，生成完整的 OpenAPI 3.1.0 YAML 规范文件（含全量中文注释）和 Redoc 可视化页面。
  支持 Java (Spring Boot/Cloud, Quarkus)、Go (Gin, Echo, Fiber)、Python (Django, FastAPI, Flask)、
  Node.js (Express, NestJS, Koa)、PHP (Laravel, ThinkPHP, Symfony)、C# (ASP.NET Core, ABP, NancyFX)、
  Rust (Axum, Actix Web, Rocket) 等主流后端框架。
  当用户提到生成 OpenAPI、生成接口文档、生成 API 文档、生成 swagger、导出接口规范、自动生成 YAML、
  接口梳理、API 梳理、接口全量导出、openapi spec、api specification 等需求时，请使用此技能。
  即使用户没有明确说"OpenAPI"，只要意图是从代码中提取或整理接口信息并生成规范文档，也应触发此技能。
---

# OpenAPI 自动生成专家

从项目源代码中反推所有 API 接口，零错误生成带完整中文注释的 OpenAPI 3.1.0 规范文件，并附带 Redoc 可视化页面。

## 工作流程

按以下 7 个步骤顺序执行，不可跳过。

### Step 1: 识别项目技术栈 & 规模评估

扫描项目根目录，确定编程语言和框架：

| 信号 | 语言 | 常见框架 |
|------|------|----------|
| `pom.xml` / `build.gradle` / `.java` | Java | Spring Boot, Spring Cloud, Quarkus |
| `go.mod` / `.go` | Go | Gin, Echo, Fiber |
| `requirements.txt` / `pyproject.toml` / `.py` | Python | Django, FastAPI, Flask |
| `package.json` / `.ts` / `.js` | Node.js | Express, NestJS, Koa |
| `composer.json` / `.php` | PHP | Laravel, ThinkPHP, Symfony |
| `*.csproj` / `*.sln` / `.cs` | C# | ASP.NET Core, ABP, NancyFX |
| `Cargo.toml` / `.rs` | Rust | Axum, Actix Web, Rocket |

确定具体框架后，记录下来。

**规模评估（决定生成模式）：**

统计项目中的控制器/路由文件数量和模型/DTO 文件数量，估算接口总数：

| 文件类型 | 统计目标 | 估算系数 |
|----------|----------|----------|
| `*Controller.java` / `*Resource.java` | 控制器数 | × 4 ≈ 接口数 |
| `*_handler.go` / `*_router.go` | 处理器数 | × 3 ≈ 接口数 |
| `views.py` / `*_view.py` | 视图数 | × 3 ≈ 接口数 |
| `*.controller.ts` / `*.router.ts` | 控制器数 | × 4 ≈ 接口数 |
| `*Controller.php` | 控制器数 | × 4 ≈ 接口数 |
| `*Controller.cs` | 控制器数 | × 4 ≈ 接口数 |
| `*_handler.rs` | 处理器数 | × 3 ≈ 接口数 |

**模式选择：**

- **估算接口数 ≤ 50 且模型文件 ≤ 80** → 使用**标准模式**（Step 3 ~ Step 7 按原流程执行）
- **估算接口数 > 50 或模型文件 > 80** → 使用**分批模式**（Step 3 ~ Step 7 按下方分批流程执行）

向用户报告评估结果，例如："检测到约 120 个接口、45 个模型，将采用分批生成模式以确保完整性。"

### Step 2: 加载框架参考文件

根据识别到的语言，读取本技能 `references/` 目录下对应的参考文件：

- Java → 读取 `references/java.md`
- Go → 读取 `references/go.md`
- Python → 读取 `references/python.md`
- Node.js → 读取 `references/nodejs.md`
- PHP → 读取 `references/php.md`
- C# → 读取 `references/csharp.md`
- Rust → 读取 `references/rust.md`

参考文件包含该语言下各框架的路由定义模式、参数提取方式、数据模型定义方式。严格按照参考文件中的指引来识别接口。

如果项目使用多种语言（如前端 + 后端分离），只处理后端 API 部分。

### Step 3: 全面扫描路由，提取所有接口

这是最关键的一步——必须做到不遗漏任何接口。

**扫描策略：**

1. **找到路由注册入口**：每个框架都有集中注册路由的方式（路由文件、控制器注解、路由表等），先定位入口
2. **递归追踪**：从入口出发，追踪所有路由分组、子路由、模块化路由
3. **扫描所有控制器/处理函数**：不仅看路由注册文件，还要扫描所有控制器类/处理函数文件，确保注解式路由也被覆盖
4. **检查中间件路由**：部分接口可能通过中间件注册（如认证、健康检查）
5. **非 REST 端点**：留意 WebSocket（`/ws`）、Server-Sent Events（`/sse`）、GraphQL（`/graphql`）、文件上传/下载等特殊端点。WebSocket 和 GraphQL 不属于标准 OpenAPI 路径，但应在 YAML 的 info.description 中列出供参考；文件上传/下载接口使用 `multipart/form-data` 或 `application/octet-stream` 正确描述

**提取信息清单（每个接口）：**

- HTTP 方法（GET / POST / PUT / DELETE / PATCH）
- 完整路径（含路径参数占位符，如 `/users/{id}`）
- 路径参数（名称、类型、是否必填）
- 查询参数（名称、类型、默认值、是否必填）
- 请求头参数（如有自定义请求头）
- 请求体结构（字段名、类型、约束、是否必填）
- 成功响应结构（状态码、字段名、类型）
- 错误响应结构（常见错误码及其含义）
- 接口所属分组 / 模块（用于 tags）
- 接口中文描述（从注释、函数名、类名推断）
- 认证方式（Bearer Token / API Key / Cookie 等，用于 securitySchemes）

#### 分批模式下的 Step 3

当 Step 1 评估为分批模式时，Step 3 拆分为两个子步骤以避免 token 溢出：

**Step 3A — 路由索引（轻量扫描）：**

快速扫描所有路由注册和控制器，只提取每个接口的最小信息，逐行写入 `.openapi_gen/_work/endpoints.jsonl`：

```jsonl
{"method": "GET", "path": "/users/{id}", "tags": ["用户管理"], "summary": "查询用户详情", "source_file": "src/controller/UserController.java", "line": 45}
{"method": "POST", "path": "/users", "tags": ["用户管理"], "summary": "创建用户", "source_file": "src/controller/UserController.java", "line": 62}
```

此步只做路径发现、不深入提取参数和请求/响应体细节，token 消耗极低。完成后在 `.openapi_gen/_work/metadata.json` 中记录接口总数和进度。

**Step 3B — 分批参数提取：**

按 tags 或控制器文件对接口分组，每批处理 20~30 个接口：

1. 读取当前批次涉及的控制器源文件
2. 提取每个接口的完整参数（路径参数、查询参数、请求头、请求体、响应体）
3. 将提取结果更新到 `endpoints.jsonl` 中对应行（覆盖原有简要记录）
4. 在 `metadata.json` 中更新已完成批次
5. **释放当前批次的源码上下文**，不带入下一批

重复直到所有批次完成。每批完成后可运行预检确认中间数据结构正确：
```bash
python <skill-path>/scripts/validate.py --jsonl .openapi_gen/_work
```

### Step 4: 提取数据模型

从代码中提取所有与 API 相关的数据模型：

1. **请求模型**：DTO / Request / Form / Input 类
2. **响应模型**：VO / Response / Output / Resource 类
3. **实体模型**：Entity / Model 类（当直接暴露给 API 时）
4. **枚举类型**：状态码、类型标识等枚举

**对每个模型字段提取：**

- 字段名称
- 字段类型（string / integer / number / boolean / array / object）
- 格式（format：date-time / email / uri / int32 / int64 / float / double 等）
- 约束（minLength / maxLength / minimum / maximum / pattern / enum）
- 是否必填（required）
- 默认值（default）
- 中文注释（从代码注释推断）
- 示例值（从代码中的测试数据、默认值或合理推断）

#### 分批模式下的 Step 4

**Step 4A — 模型发现：**

扫描所有 DTO / VO / Model / Entity 目录，每个模型逐行写入 `.openapi_gen/_work/schemas.jsonl`：

```jsonl
{"name": "UserDTO", "type": "object", "description": "用户信息传输对象", "fields": [{"name": "id", "type": "integer", "format": "int64", "description": "用户唯一标识", "required": true, "example": 1001}]}
{"name": "CreateUserRequest", "type": "object", "description": "创建用户请求", "fields": [...]}
```

**Step 4B — 分批字段提取：**

如果模型文件过多（> 80 个），按目录分批读取，每批提取字段细节后写入 `schemas.jsonl`，与 Step 3B 同理释放上下文。

### Step 5: 组织接口分类（Tags）

根据代码中的模块划分（包名、目录结构、控制器分组）来组织 tags：

- 每个 tag 必须有 `name` 和 `description`
- description 使用中文
- 按业务功能分组，而非技术分层

### Step 6: 组装 OpenAPI YAML

**标准模式**：将上述信息在上下文中直接组装为完整的 OpenAPI 3.1.0 YAML 文件，严格遵循下方的输出规范。

**分批模式**：调用本技能 `scripts/merge.py` 从 JSONL 中间文件组装 YAML，无需再在上下文中拼装全量内容：

```bash
python <skill-path>/scripts/merge.py .openapi_gen/_work --output .openapi_gen/openapi.yaml
```

合并脚本会自动：
- 从 `endpoints.jsonl` 构建 `paths`
- 从 `schemas.jsonl` 构建 `components/schemas`
- 从 `metadata.json` 读取 `info`、`servers`、`tags`、`securitySchemes`
- 添加通用 ErrorResponse（如不存在）
- 输出完整的 OpenAPI 3.1.0 YAML

合并完成后，检查脚本输出的接口数和模型数是否与预期一致。如有遗漏，回到 Step 3B 补充后重新合并。

### Step 7: 输出文件与验证

1. 在用户项目根目录下创建 `.openapi_gen/` 目录
2. 将生成的 OpenAPI YAML 写入 `.openapi_gen/openapi.yaml`
3. 将本技能 `assets/redoc.html` 模板复制到 `.openapi_gen/index.html`
4. **运行验证脚本**：执行本技能 `scripts/validate.py` 对生成的 YAML 进行结构校验：
   ```bash
   python <skill-path>/scripts/validate.py .openapi_gen/openapi.yaml
   ```
   如果验证报错，根据错误信息修正 YAML 后重新验证，直至通过
5. （分批模式）清理工作目录——执行本技能 `scripts/cleanup.py` 删除中间文件：
   ```bash
   python <skill-path>/scripts/cleanup.py .openapi_gen
   ```
6. 告知用户：用浏览器直接打开 `.openapi_gen/index.html` 即可查看可视化文档（需要通过本地 HTTP 服务，如 `npx serve .openapi_gen` 或 `python -m http.server -d .openapi_gen`）

---

## OpenAPI 3.1.0 输出规范

生成的 YAML 必须严格遵循以下结构。每一处注释和描述都使用中文。

### 顶层结构

```yaml
openapi: 3.1.0

info:
  title: 项目名称（从代码中提取）
  version: 版本号（从代码配置中提取，默认 1.0.0）
  description: |
    项目简要描述（从 README 或代码注释中提取）
  contact:
    name: 维护团队或个人（从代码中提取，如无则写项目名）
    email: 联系邮箱（如有）

servers:
  - url: http://localhost:8080
    description: 本地开发环境
  - url: https://api.example.com
    description: 生产环境
  # 从代码配置文件中提取实际的端口和地址

tags:
  - name: 分组名称
    description: 分组的中文描述

paths:
  /具体路径:
    get|post|put|delete|patch:
      tags:
        - 所属分组
      summary: 接口简要描述（中文，一句话）
      description: |
        接口详细描述（中文，说明功能、使用场景、注意事项）
      operationId: 操作标识符（使用代码中的函数名）
      parameters: []    # 路径参数 + 查询参数 + 请求头参数
      requestBody: {}   # POST/PUT/PATCH 的请求体
      responses: {}     # 成功 + 失败响应

components:
  schemas: {}       # 所有数据模型
  securitySchemes: {} # 认证方式（Bearer / ApiKey / OAuth2 等）
  responses: {}     # 通用响应定义
  parameters: {}    # 通用参数定义

security: []        # 全局安全要求（从代码中的认证中间件推断）
```

### parameters 格式

```yaml
parameters:
  - name: id
    in: path          # path / query / header / cookie
    required: true    # path 参数必须为 true
    description: 资源唯一标识
    schema:
      type: integer
      format: int64
      minimum: 1
      example: 42
```

### requestBody 格式

```yaml
requestBody:
  required: true
  description: 请求体描述（中文）
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/模型名称'
      example:
        field1: 真实示例值
        field2: 真实示例值
```

### responses 格式

```yaml
responses:
  '200':
    description: 操作成功
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/响应模型名称'
        example:
          code: 0
          message: success
          data: {}
  '400':
    description: 请求参数错误
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/ErrorResponse'
  '404':
    description: 资源不存在
  '500':
    description: 服务器内部错误
```

### components/schemas 格式

```yaml
components:
  schemas:
    UserDTO:
      type: object
      description: 用户信息传输对象
      required:
        - username
        - email
      properties:
        id:
          type: integer
          format: int64
          description: 用户唯一标识
          readOnly: true
          example: 1001
        username:
          type: string
          description: 用户名
          minLength: 3
          maxLength: 32
          pattern: '^[a-zA-Z0-9_]+$'
          example: john_doe
        email:
          type: string
          format: email
          description: 电子邮箱
          example: john@example.com
        status:
          type: string
          description: 用户状态
          enum:
            - active
            - inactive
            - banned
          example: active
        createdAt:
          type: string
          format: date-time
          description: 创建时间
          readOnly: true
          example: '2025-01-15T08:30:00Z'
```

### 通用响应和参数

```yaml
components:
  responses:
    BadRequest:
      description: 请求参数错误
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: 资源不存在
    InternalError:
      description: 服务器内部错误

  parameters:
    PageParam:
      name: page
      in: query
      required: false
      description: 页码，从 1 开始
      schema:
        type: integer
        minimum: 1
        default: 1
        example: 1
    PageSizeParam:
      name: pageSize
      in: query
      required: false
      description: 每页数量
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
        example: 20

  schemas:
    ErrorResponse:
      type: object
      description: 通用错误响应
      properties:
        code:
          type: integer
          description: 错误码
          example: 400
        message:
          type: string
          description: 错误信息
          example: 参数校验失败
        details:
          type: array
          description: 详细错误列表
          items:
            type: string
          example:
            - username 不能为空
            - email 格式不正确
```

---

## 质量约束

这些约束的核心目标是生成可直接用于生产环境的规范文件，而非占位式的草稿。

### 字段注释

每个 `schema` 的每个 `property` 必须包含 `description` 字段，使用中文描述该字段的业务含义。因为没有注释的字段在 Redoc 中显示为空白，会让使用者困惑。

### 类型准确

- 整数用 `integer`（加 `format: int32` 或 `int64`）
- 浮点数用 `number`（加 `format: float` 或 `double`）
- 日期时间用 `string` + `format: date-time`
- 邮箱用 `string` + `format: email`
- URL 用 `string` + `format: uri`
- UUID 用 `string` + `format: uuid`

### 约束完整

从代码中的校验注解 / 验证规则中提取：

- `minLength` / `maxLength`（字符串长度限制）
- `minimum` / `maximum`（数值范围限制）
- `pattern`（正则约束）
- `enum`（枚举值列表）
- `default`（默认值）
- `nullable`（是否可为空）

### 示例值

每个字段的 `example` 必须是真实有效的值，从代码中的测试数据、种子数据、默认值中提取。如果代码中没有，根据字段语义合理推断（如手机号用 `13800138000`、邮箱用 `user@example.com`）。

### YAML 格式

- 使用 2 空格缩进
- 字符串值无需引号（除非包含特殊字符）
- 日期时间值加引号：`'2025-01-15T08:30:00Z'`
- 多行描述使用 `|` 块标量
- 保持缩进一致，不混用制表符

### 禁止事项

- 不使用 `TODO`、`待补充`、`...` 等占位内容
- 不生成空的 `properties: {}`
- 不遗漏任何已发现的接口
- 不编造代码中不存在的接口
- 不在 YAML 之外输出额外的说明文字（直接输出文件内容）

---

## 完整性检查清单

生成完毕后，逐项核对：

1. **接口完整性**：对照代码中的路由注册和控制器，确认所有接口都已包含
2. **模型完整性**：所有被接口引用的 `$ref` 都在 `components/schemas` 中有定义
3. **字段完整性**：每个模型的每个字段都有 `type`、`description`、`example`
4. **分组完整性**：每个接口都归属到至少一个 tag，每个 tag 都有 description
5. **响应完整性**：每个接口至少包含一个成功响应（200/201/204）和常见错误响应
6. **引用正确性**：所有 `$ref` 路径格式正确且指向存在的定义
7. **YAML 有效性**：缩进正确，无语法错误，可被标准 YAML 解析器正确解析

### 分批模式额外检查

8. **批次完整性**：`metadata.json` 中所有批次均已标记完成，无遗漏批次
9. **接口计数**：`merge.py` 输出的接口数与 Step 3A 中发现的总数一致
10. **模型计数**：`merge.py` 输出的模型数与 Step 4A 中发现的总数一致
11. **JSONL 预检**：`validate.py --jsonl` 通过，无引用缺失
