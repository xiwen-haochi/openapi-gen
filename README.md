# openapi-gen

> 从源代码自动生成 OpenAPI 3.1.0 规范文件 + Redoc 可视化文档的 VS Code Copilot 技能

---

## 功能

- **全自动**：阅读项目源代码，反推所有 API 接口，零手动配置
- **全注释**：每个路径、参数、字段均附带中文描述
- **全覆盖**：递归扫描路由注册、控制器注解、中间件路由，不遗漏任何接口
- **可视化**：同时生成 Redoc HTML 页面，一键预览接口文档
- **自动校验**：内置验证脚本，确保生成的 YAML 结构合法、引用完整

## 支持框架

| 语言 | 框架 |
|------|------|
| Java | Spring Boot, Spring Cloud, Quarkus |
| Go | Gin, Echo, Fiber |
| Python | Django / DRF, FastAPI, Flask |
| Node.js | Express, NestJS, Koa |
| PHP | Laravel, ThinkPHP, Symfony |
| C# | ASP.NET Core, ABP, NancyFX |
| Rust | Axum, Actix Web, Rocket |

## 安装

```bash
# 通过 skills.sh 安装（推荐）
skills install gh:你的用户名/openapi-gen

# 或手动复制到项目
cp -r openapi-gen/ 你的项目/.agents/skills/openapi-gen
```

## 使用

在 VS Code Copilot Chat 中输入：

```
帮我生成这个项目的 OpenAPI 文档
```

技能会自动识别项目技术栈，扫描所有接口，在项目根目录生成：

```
openapi_gen/
├── openapi.yaml   # OpenAPI 3.1.0 规范
└── index.html     # Redoc 可视化页面
```

### 查看文档

```bash
npx serve openapi_gen
# 或
python -m http.server -d openapi_gen
```

浏览器打开 `http://localhost:3000`（或 `8000`）即可查看。

## 项目结构

```
openapi-gen/
├── SKILL.md              # 技能指令
├── assets/
│   └── redoc.html         # 可视化模板
├── references/            # 各语言框架参考
│   ├── java.md
│   ├── go.md
│   ├── python.md
│   ├── nodejs.md
│   ├── php.md
│   ├── csharp.md
│   └── rust.md
└── scripts/
    └── validate.py        # YAML 验证脚本
```

## 许可证

[MIT](LICENSE)


