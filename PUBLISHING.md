# 发布指南 / Publishing Guide

## 目录结构检查

发布前确认仓库包含以下文件，且路径正确：

```
openapi-gen/
├── openapi-gen/
│   ├── SKILL.md              # 技能主文件（必须）
│   ├── assets/
│   │   └── redoc.html         # Redoc 可视化模板
│   ├── references/
│   │   ├── java.md            # Java 框架参考
│   │   ├── go.md              # Go 框架参考
│   │   ├── python.md          # Python 框架参考
│   │   ├── nodejs.md          # Node.js 框架参考
│   │   ├── php.md             # PHP 框架参考
│   │   ├── csharp.md          # C# 框架参考
│   │   └── rust.md            # Rust 框架参考
│   └── scripts/
│       ├── validate.py        # YAML 验证脚本（支持 --jsonl 预检）
│       ├── merge.py           # JSONL → OpenAPI YAML 合并脚本（分批模式）
│       └── cleanup.py         # 清理 _work 工作目录
├── README.md
├── PUBLISHING.md              # 本文件
└── LICENSE
```

---

## 格式验证

### 1. SKILL.md YAML Frontmatter

确保 SKILL.md 顶部的 YAML frontmatter 格式正确：

```yaml
---
name: openapi-gen
description: >-
  技能描述内容（不换行、不含特殊 YAML 字符）
---
```

**检查项：**
- `---` 标记成对出现
- `name` 字段为小写字母加连字符
- `description` 使用 `>-` 多行折叠，不包含裸冒号或其他可能破坏 YAML 的字符
- 编码为 UTF-8（无 BOM）

### 2. Markdown 格式

```bash
# 如果已安装 markdownlint
npx markdownlint-cli2 '**/*.md'
```

### 3. 验证脚本自检

```bash
python openapi-gen/scripts/validate.py --help
python openapi-gen/scripts/merge.py --help
python openapi-gen/scripts/cleanup.py --help
```

确认三个脚本均可正常执行、无导入错误。

---

## 安装方式

### 通过 skills 安装（推荐）

```bash
npx skills add xiwen-haochi/openapi-gen
```

安装完成后，技能将出现在 VS Code Copilot 的可用技能列表中。

### 手动安装

```bash
# 克隆到本地
git clone https://github.com/你的用户名/openapi-gen.git

# 复制技能目录到你的项目或全局技能位置
cp -r openapi-gen/openapi-gen ~/.vscode/skills/openapi-gen
```

或将 `openapi-gen/openapi-gen/` 目录复制到项目的 `.agents/skills/` 下：

```bash
cp -r openapi-gen/openapi-gen 你的项目/.agents/skills/openapi-gen
```

---

## 使用方法

安装后，在 VS Code Copilot Chat 中直接对话即可触发。示例提示词：

| 提示词 | 说明 |
|--------|------|
| "帮我生成这个项目的 OpenAPI 文档" | 最常见用法 |
| "梳理一下所有 API 接口，生成 swagger" | 也能触发 |
| "从代码中提取所有接口，生成 YAML 规范" | 明确指定格式 |
| "Generate OpenAPI spec for this project" | 英文提示也可以 |

### 输出

技能会在项目根目录生成 `.openapi_gen/` 目录：

```
.openapi_gen/
├── openapi.yaml   # OpenAPI 3.1.0 规范文件
└── index.html     # Redoc 可视化页面
```

### 查看文档

```bash
# 方式一：Node.js
npx serve .openapi_gen

# 方式二：Python
python -m http.server -d .openapi_gen

# 然后在浏览器打开 http://localhost:3000（或 8000）
```

> 注意：由于浏览器安全策略，`index.html` 需要通过 HTTP 服务访问，不能直接双击打开。

---

## 发布到 GitHub

### 1. 创建仓库

```bash
gh repo create openapi-gen --public --description "自动生成 OpenAPI 3.1.0 规范文件的 VS Code Copilot 技能"
```

### 2. 推送代码

```bash
git add -A
git commit -m "feat: initial release of openapi-gen skill"
git push origin main
```

### 3. 创建 Release（可选）

```bash
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "首次发布"
```

### 4. 验证安装

在另一个环境中测试安装：

```bash
skills install gh:你的用户名/openapi-gen
```

打开一个包含 API 的项目，在 Copilot Chat 中输入 "生成 OpenAPI 文档"，确认技能正常触发并输出文件。

---

## 常见问题

**Q: 技能没有被触发？**
A: 确保 SKILL.md 的 `description` 字段包含足够的触发关键词。检查技能是否正确安装到技能目录。

**Q: 生成的 YAML 有语法错误？**
A: 运行验证脚本检查：
```bash
python openapi-gen/scripts/validate.py .openapi_gen/openapi.yaml
```

**Q: Redoc 页面空白？**
A: 确保通过 HTTP 服务访问（不要直接打开 HTML 文件），并确认 `openapi.yaml` 与 `index.html` 在同一目录下。
