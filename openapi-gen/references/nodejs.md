# Node.js 框架路由识别参考

本文件覆盖 Node.js 生态中三个主流 Web 框架的路由识别方式。

---

## Express

### 路由定义模式

**直接注册：**
```javascript
const express = require('express');
const app = express();

app.get('/users', listUsers);
app.post('/users', createUser);
app.get('/users/:id', getUser);
app.put('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);
```

**Router 模块化路由：**
```javascript
const router = express.Router();

router.get('/', listUsers);
router.post('/', createUser);
router.get('/:id', getUser);
router.put('/:id', updateUser);
router.delete('/:id', deleteUser);

// 挂载到主应用
app.use('/api/users', router);
```

**路由方法：**

| 方法 | HTTP 方法 |
|------|-----------|
| `app.get()` / `router.get()` | GET |
| `app.post()` / `router.post()` | POST |
| `app.put()` / `router.put()` | PUT |
| `app.delete()` / `router.delete()` | DELETE |
| `app.patch()` / `router.patch()` | PATCH |
| `app.all()` | 所有方法 |
| `app.use()` | 中间件挂载（含子路由） |

路径参数格式：`:name` → OpenAPI `{name}`。
可选参数：`:name?`。

### 参数提取

```javascript
// 路径参数
const id = req.params.id;

// 查询参数
const page = req.query.page || 1;
const keyword = req.query.keyword;

// 请求体（需 body-parser 中间件）
const { username, email } = req.body;

// 请求头
const token = req.headers['authorization'];
// 或
const token = req.get('Authorization');
```

### 数据模型识别

Express 本身不强制模型定义，需要从以下来源寻找：

**Joi 验证（常见）：**
```javascript
const Joi = require('joi');

const createUserSchema = Joi.object({
    username: Joi.string().min(3).max(32).required(),
    email: Joi.string().email().required(),
    age: Joi.number().integer().min(0).max(150),
    role: Joi.string().valid('admin', 'user', 'guest').default('user'),
});
```

| Joi 方法 | OpenAPI 约束 |
|----------|-------------|
| `.required()` | required: true |
| `.min(n)` | minLength (string) / minimum (number) |
| `.max(n)` | maxLength (string) / maximum (number) |
| `.email()` | format: email |
| `.uri()` | format: uri |
| `.uuid()` | format: uuid |
| `.valid('a', 'b')` | enum: [a, b] |
| `.default(v)` | default: v |
| `.integer()` | format: int32 |
| `.pattern(/regex/)` | pattern |

**express-validator：**
```javascript
const { body, query, param } = require('express-validator');

router.post('/users', [
    body('username').isString().isLength({ min: 3, max: 32 }),
    body('email').isEmail(),
    body('age').optional().isInt({ min: 0, max: 150 }),
], createUser);
```

**Mongoose Schema（如使用 MongoDB）：**
```javascript
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, minlength: 3, maxlength: 32 },
    email: { type: String, required: true, unique: true },
    age: { type: Number, min: 0, max: 150 },
    role: { type: String, enum: ['admin', 'user', 'guest'], default: 'user' },
    createdAt: { type: Date, default: Date.now },
});
```

**TypeScript 接口 / 类型（如使用 TS）：**
```typescript
interface CreateUserRequest {
    username: string;
    email: string;
    age?: number;
    role?: 'admin' | 'user' | 'guest';
}
```

**JS/TS 类型映射：**

| JS/TS 类型 | OpenAPI type + format |
|------------|----------------------|
| `string` | string |
| `number` (整数场景) | integer |
| `number` (小数场景) | number |
| `boolean` | boolean |
| `Date` | string, format: date-time |
| `Array<T>` / `T[]` | array, items: T |
| `object` / `Record<string, T>` | object |
| `Buffer` | string, format: binary |
| 联合类型 `'a' \| 'b'` | string, enum: [a, b] |
| `T \| null` | nullable |
| `T?` / `T \| undefined` | required: false |

### 响应结构

```javascript
// 常见模式
res.json({ code: 0, message: 'success', data: result });
res.status(201).json(user);
res.status(400).json({ error: 'Bad Request', message: '...' });
res.status(404).json({ error: 'Not Found' });
```

### 扫描位置

1. `app.js` / `app.ts` / `index.js` / `server.js` — 入口文件
2. `routes/` / `routers/` — 路由模块
3. `controllers/` — 控制器
4. `middlewares/` / `middleware/` — 中间件（可能含验证逻辑）
5. `models/` — Mongoose 模型
6. `validators/` / `schemas/` — 验证规则
7. `types/` / `interfaces/` — TypeScript 类型定义
8. `dto/` — 数据传输对象

---

## NestJS

### 路由定义模式

NestJS 使用装饰器（TypeScript）定义路由：

```typescript
import { Controller, Get, Post, Put, Delete, Patch, Body, Param, Query, Headers } from '@nestjs/common';

@Controller('users')
export class UserController {
    @Get()
    findAll(@Query('page') page: number, @Query('pageSize') pageSize: number) { ... }

    @Get(':id')
    findOne(@Param('id') id: string) { ... }

    @Post()
    create(@Body() createUserDto: CreateUserDto) { ... }

    @Put(':id')
    update(@Param('id') id: string, @Body() updateUserDto: UpdateUserDto) { ... }

    @Delete(':id')
    remove(@Param('id') id: string) { ... }

    @Patch(':id/status')
    updateStatus(@Param('id') id: string, @Body() dto: UpdateStatusDto) { ... }
}
```

**装饰器映射：**

| 装饰器 | HTTP 方法 |
|--------|-----------|
| `@Get()` | GET |
| `@Post()` | POST |
| `@Put()` | PUT |
| `@Delete()` | DELETE |
| `@Patch()` | PATCH |

**模块路由前缀：**
```typescript
@Module({
    imports: [RouterModule.register([
        { path: 'api/v1', module: V1Module },
    ])],
})
```

完整路径 = 全局前缀（`app.setGlobalPrefix('api')`） + 模块路径 + `@Controller` 路径 + 方法路径。

**参数装饰器：**

| 装饰器 | OpenAPI 参数 |
|--------|-------------|
| `@Param('name')` | in: path |
| `@Query('name')` | in: query |
| `@Headers('name')` | in: header |
| `@Body()` | requestBody |
| `@Body('field')` | requestBody 的特定字段 |

### 数据模型识别（DTO）

NestJS 使用 class-validator 和 class-transformer：

```typescript
import { IsString, IsEmail, IsOptional, IsInt, Min, Max, MinLength, MaxLength, IsEnum } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateUserDto {
    @ApiProperty({ description: '用户名', example: 'john_doe', minLength: 3, maxLength: 32 })
    @IsString()
    @MinLength(3)
    @MaxLength(32)
    username: string;

    @ApiProperty({ description: '邮箱', example: 'john@example.com' })
    @IsEmail()
    email: string;

    @ApiPropertyOptional({ description: '年龄', example: 25, minimum: 0, maximum: 150 })
    @IsOptional()
    @IsInt()
    @Min(0)
    @Max(150)
    age?: number;

    @ApiProperty({ description: '角色', enum: Role, example: Role.USER })
    @IsEnum(Role)
    role: Role;
}
```

**class-validator 装饰器映射：**

| 装饰器 | OpenAPI 约束 |
|--------|-------------|
| `@IsString()` | type: string |
| `@IsInt()` / `@IsNumber()` | type: integer / number |
| `@IsBoolean()` | type: boolean |
| `@IsEmail()` | format: email |
| `@IsUrl()` | format: uri |
| `@IsUUID()` | format: uuid |
| `@IsDateString()` | format: date-time |
| `@MinLength(n)` | minLength: n |
| `@MaxLength(n)` | maxLength: n |
| `@Min(n)` | minimum: n |
| `@Max(n)` | maximum: n |
| `@Matches(regex)` | pattern |
| `@IsEnum(E)` | enum: [...] |
| `@IsOptional()` | required: false |
| `@IsArray()` | type: array |
| `@ArrayMinSize(n)` | minItems: n |
| `@ArrayMaxSize(n)` | maxItems: n |

**@nestjs/swagger 装饰器（如果已使用）：**
- `@ApiProperty()` — 字段属性（直接使用其中的 description, example, enum 等）
- `@ApiOperation()` — 接口描述
- `@ApiResponse()` — 响应描述
- `@ApiTags()` — 分组标签

如果代码中已用 `@nestjs/swagger` 装饰器，优先使用其中的信息。

### 扫描位置

1. `src/**/*.controller.ts` — 控制器
2. `src/**/*.dto.ts` — DTO 数据模型
3. `src/**/*.entity.ts` — TypeORM 实体
4. `src/**/*.module.ts` — 模块（含路由配置）
5. `src/main.ts` — 全局前缀配置
6. `src/**/*.service.ts` — 服务层（辅助理解业务逻辑）

---

## Koa

### 路由定义模式

**koa-router：**
```javascript
const Router = require('@koa/router');
const router = new Router({ prefix: '/api' });

router.get('/users', listUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
router.put('/users/:id', updateUser);
router.delete('/users/:id', deleteUser);

// 嵌套路由
const usersRouter = new Router({ prefix: '/users' });
usersRouter.get('/', listUsers);
usersRouter.post('/', createUser);
router.use(usersRouter.routes());

app.use(router.routes());
app.use(router.allowedMethods());
```

路径参数格式与 Express 相同：`:name` → OpenAPI `{name}`。

### 参数提取

```javascript
// 路径参数
const id = ctx.params.id;

// 查询参数
const page = ctx.query.page || 1;
const keyword = ctx.query.keyword;

// 请求体（需 koa-bodyparser 中间件）
const { username, email } = ctx.request.body;

// 请求头
const token = ctx.headers['authorization'];
// 或
const token = ctx.get('Authorization');
```

### 数据模型识别

与 Express 类似，Koa 本身不强制模型定义。常见搭配：

- **Joi** — 同 Express
- **Yup** — 类似 Joi 的验证库
- **TypeScript 接口** — 同 Express
- **Mongoose Schema** — 同 Express

### 响应结构

```javascript
ctx.body = { code: 0, message: 'success', data: result };
ctx.status = 201;
ctx.body = user;
```

### 扫描位置

1. `app.js` / `index.js` / `server.js` — 入口文件
2. `routes/` / `routers/` — 路由模块
3. `controllers/` — 控制器
4. `models/` — 数据模型
5. `validators/` / `schemas/` — 验证规则
6. `middlewares/` — 中间件
