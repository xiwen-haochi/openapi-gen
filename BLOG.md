# 让 AI 替你写 API 文档——openapi-gen 技能实战

> 一条消息，零配置，从代码直接生成可交互的 API 文档。

---

## 痛点

写 API 文档是后端开发中最无聊却最重要的工作之一。

你有没有过这种经历：代码里加了三个接口，文档却停留在上个月的版本。前端同事来问"这个字段到底是 `int` 还是 `string`"——你只能让他去看代码。

手写 Swagger YAML？光是把一个带分页的列表接口的请求参数、响应体、Schema 引用全部写对，就够你折腾半小时。更别提整个项目几十甚至上百个接口了。

**openapi-gen** 的目标很简单：你写代码，AI 写文档。

---

## 它做了什么

openapi-gen 是一个技能。：

```
帮我生成这个项目的 OpenAPI 文档
```

它会：

1. **自动识别技术栈**——不管你用的是 Spring Boot、Gin、FastAPI、NestJS、Laravel 还是 ASP.NET Core，它都能认出来
2. **递归扫描所有路由**——路由注册、控制器注解、装饰器、宏标注……一个不漏
3. **提取完整的接口细节**——路径参数、查询参数、请求体 Schema、响应体 Schema、状态码、示例值、校验规则
4. **生成 OpenAPI 3.1.0 YAML**——不是草稿，不是占位，而是每个字段都有中文注释、每个类型都精确到 format 的生产级规范
5. **同步输出 Redoc 可视化页面**——`npx serve .openapi_gen`，浏览器打开就能用

整个过程不需要你写一行 YAML，不需要配置任何注解库，不需要启动任何服务。

---

## 大型项目？没问题

接口一多，AI 的上下文窗口就不够用了。这是所有"AI 生成文档"方案的死穴。

openapi-gen 用了一个工程化的方式解决这个问题——**分批模式**：

- 当检测到接口超过 50 个或模型文件超过 80 个时，自动切换
- 先快速扫描所有路由，产出轻量级的 JSONL 中间文件
- 然后按 20-30 个接口为一批，逐批深入提取参数和响应体
- 最后用 `merge.py` 脚本将所有 JSONL 合并为一份完整的 OpenAPI YAML

核心思路：**把 token 密集的生成任务拆成多轮低 token 任务，用文件系统做记忆**。

中间文件全部存在 `.openapi_gen/_work/` 目录下，合并验证通过后自动清理，不污染项目目录。

---

## 质量，不是凑数

很多代码生成工具的输出看着像那么回事，仔细一看全是 `TODO` 和空的 `properties: {}`。

openapi-gen 在提示词中植入了严格的质量约束：

- **每个字段必须有 `description`**——Redoc 里不会出现一片空白
- **每个字段必须有 `example`**——而且是从代码中的测试数据、默认值、种子数据提取的真实值
- **类型精确到 format**——不只是 `string`，而是 `string` + `format: date-time`
- **约束完整**——`minLength`、`maximum`、`pattern`、`enum`，代码里写了的全部提取
- **$ref 引用必须可达**——内置验证脚本自动检查所有引用路径
- **禁止占位内容**——`TODO`、`待补充`、`...` 出现即报错

生成完毕后还有一份 7 项检查清单（分批模式 11 项），确保没有遗漏。

---

## 7 种语言，开箱即用

| 语言 | 支持的框架 |
|------|-----------|
| Java | Spring Boot, Spring Cloud, Quarkus |
| Go | Gin, Echo, Fiber |
| Python | Django/DRF, FastAPI, Flask |
| Node.js | Express, NestJS, Koa |
| PHP | Laravel, ThinkPHP, Symfony |
| C# | ASP.NET Core, ABP, NancyFX |
| Rust | Axum, Actix Web, Rocket |

每种语言都有独立的参考文件，告诉 AI 在哪里找路由、怎么解析注解、如何处理中间件。不是靠猜，而是靠精确的规则。

---

## 30 秒上手

**安装：**

```bash
npx skills add xiwen-haochi/openapi-gen
```

**使用：**

在 IDE 里说 "生成 OpenAPI 文档"。

**查看：**
进入 openapi_gen 目录
node
```bash
npx serve .
```
python
```bash
python -m http.server 3000
```

浏览器打开 `http://localhost:3000`，你会看到一份完整的、可搜索、可交互的 API 文档。

---

## 底层设计

如果你对实现感兴趣，这是技能的核心架构：

```
SKILL.md          → 主提示词，7 步工作流
references/*.md   → 各语言的路由发现规则
scripts/
  validate.py     → YAML 结构校验 + JSONL 预检
  merge.py        → JSONL 中间文件合并
  cleanup.py      → 工作目录清理
assets/
  redoc.html      → 可视化模板（CDN 加载 Redoc）
```

技能本身不运行任何服务、不调用任何外部 API。所有的工作都在对话上下文中完成，脚本只负责验证和合并——纯 Python 3.6+，唯一依赖是 PyYAML。

---

## 写在最后

API 文档不应该是开发者的负担。代码已经包含了所有信息——路由、参数、类型、校验规则、默认值——只是没有人愿意花时间把它们抄写成 YAML。

现在有 AI 愿意做这件事了。

项目地址：[github.com/xiwen-haochi/openapi-gen](https://github.com/xiwen-haochi/openapi-gen)


