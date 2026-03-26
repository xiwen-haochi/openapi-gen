# Go 框架路由识别参考

本文件覆盖 Go 生态中三个主流 Web 框架的路由识别方式。

---

## Gin

### 路由定义模式

**路由注册：**
```go
r := gin.Default()

// 直接注册
r.GET("/users", listUsers)
r.POST("/users", createUser)
r.GET("/users/:id", getUser)
r.PUT("/users/:id", updateUser)
r.DELETE("/users/:id", deleteUser)

// 路由分组
api := r.Group("/api/v1")
{
    users := api.Group("/users")
    {
        users.GET("", listUsers)
        users.POST("", createUser)
        users.GET("/:id", getUser)
    }
}
```

**路由方法映射：**

| 方法 | HTTP 方法 |
|------|-----------|
| `r.GET()` | GET |
| `r.POST()` | POST |
| `r.PUT()` | PUT |
| `r.DELETE()` | DELETE |
| `r.PATCH()` | PATCH |
| `r.Any()` | 所有方法 |
| `r.Handle("METHOD", ...)` | 由第一个参数决定 |

路径参数使用 `:name` 格式（如 `/users/:id`），转为 OpenAPI 的 `{id}`。
通配符使用 `*name` 格式。

### 参数提取

**路径参数：**
```go
func getUser(c *gin.Context) {
    id := c.Param("id")           // 路径参数
}
```

**查询参数：**
```go
func listUsers(c *gin.Context) {
    page := c.Query("page")               // 可选查询参数
    pageSize := c.DefaultQuery("pageSize", "20")  // 带默认值
    keyword := c.Query("keyword")
}
```

**请求体（JSON）：**
```go
func createUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil { ... }
}
```

**表单参数：**
```go
func upload(c *gin.Context) {
    name := c.PostForm("name")
    file, _ := c.FormFile("file")
}
```

**请求头：**
```go
func handler(c *gin.Context) {
    token := c.GetHeader("Authorization")
}
```

### 数据模型识别

Go 使用 struct tag 来定义字段约束：

```go
type CreateUserRequest struct {
    Username string `json:"username" binding:"required,min=3,max=32"`
    Email    string `json:"email" binding:"required,email"`
    Age      int    `json:"age" binding:"gte=0,lte=150"`
    Role     string `json:"role" binding:"oneof=admin user guest"`
    Phone    string `json:"phone,omitempty"`
}
```

**struct tag 映射：**

| Tag | OpenAPI 约束 |
|-----|-------------|
| `json:"name"` | 字段名 |
| `json:",omitempty"` | required: false |
| `binding:"required"` | required: true |
| `binding:"min=3"` | minLength (string) / minimum (number) |
| `binding:"max=32"` | maxLength (string) / maximum (number) |
| `binding:"gte=0"` | minimum: 0 |
| `binding:"lte=100"` | maximum: 100 |
| `binding:"email"` | format: email |
| `binding:"url"` | format: uri |
| `binding:"uuid"` | format: uuid |
| `binding:"oneof=a b c"` | enum: [a, b, c] |
| `binding:"len=11"` | minLength + maxLength = 11 |

**Go 类型映射：**

| Go 类型 | OpenAPI type + format |
|---------|----------------------|
| `string` | string |
| `int` / `int32` | integer, format: int32 |
| `int64` | integer, format: int64 |
| `float32` | number, format: float |
| `float64` | number, format: double |
| `bool` | boolean |
| `time.Time` | string, format: date-time |
| `[]T` | array, items: T |
| `map[string]T` | object, additionalProperties: T |
| 自定义 type（别名） | 看底层类型 |

### 响应结构

```go
type Response struct {
    Code    int         `json:"code"`
    Message string      `json:"message"`
    Data    interface{} `json:"data"`
}
```

关注 handler 函数中 `c.JSON(statusCode, data)` 的调用来确定响应结构和状态码。

### 扫描位置

1. `main.go` — 路由注册入口
2. `router/` / `routes/` / `routers/` — 路由定义
3. `handler/` / `handlers/` / `controller/` / `controllers/` — 处理函数
4. `model/` / `models/` / `dto/` / `types/` — 数据模型
5. `internal/` — 内部模块（可能包含路由和处理函数）
6. `api/` — API 定义
7. `pkg/` — 公共包

---

## Echo

### 路由定义模式

```go
e := echo.New()

e.GET("/users", listUsers)
e.POST("/users", createUser)
e.GET("/users/:id", getUser)
e.PUT("/users/:id", updateUser)
e.DELETE("/users/:id", deleteUser)

// 路由分组
g := e.Group("/api/v1")
g.GET("/users", listUsers)

// 带中间件的分组
admin := g.Group("/admin", adminMiddleware)
admin.GET("/stats", getStats)
```

路径参数格式与 Gin 相同：`:name` → `{name}`。

### 参数提取

```go
// 路径参数
id := c.Param("id")

// 查询参数
page := c.QueryParam("page")
keyword := c.QueryParam("keyword")

// 请求头
token := c.Request().Header.Get("Authorization")

// 请求体
var req CreateUserRequest
if err := c.Bind(&req); err != nil { ... }
```

### 数据模型识别

与 Gin 相同的 struct tag 体系。Echo 使用 `validate` tag 代替 `binding`：

```go
type CreateUserRequest struct {
    Username string `json:"username" validate:"required,min=3,max=32"`
    Email    string `json:"email" validate:"required,email"`
    Age      int    `json:"age" validate:"gte=0,lte=150"`
}
```

`validate` tag 的映射规则与 Gin 的 `binding` tag 完全相同。

### 响应结构

关注 `c.JSON(statusCode, data)` 和 `c.String(statusCode, text)` 调用。

---

## Fiber

### 路由定义模式

```go
app := fiber.New()

app.Get("/users", listUsers)
app.Post("/users", createUser)
app.Get("/users/:id", getUser)
app.Put("/users/:id", updateUser)
app.Delete("/users/:id", deleteUser)

// 路由分组
api := app.Group("/api/v1")
api.Get("/users", listUsers)

// 路由前缀
app.Route("/users", func(router fiber.Router) {
    router.Get("/", listUsers)
    router.Post("/", createUser)
    router.Get("/:id", getUser)
})
```

**注意 Fiber 方法名首字母大写：** `Get` 而非 `GET`。

路径参数格式与 Gin/Echo 相同：`:name` → `{name}`。也支持可选参数 `:name?` 和通配符 `*`。

### 参数提取

```go
// 路径参数
id := c.Params("id")
id, err := c.ParamsInt("id")  // 直接解析为 int

// 查询参数
page := c.Query("page")
page := c.Query("page", "1")  // 带默认值

// 请求头
token := c.Get("Authorization")

// 请求体
var req CreateUserRequest
if err := c.BodyParser(&req); err != nil { ... }
```

### 数据模型识别

与 Gin/Echo 相同的 struct tag 体系。Fiber 默认也使用 `validate` tag（配合 go-playground/validator）。

### 响应结构

关注 `c.JSON(data)` 和 `c.Status(code).JSON(data)` 调用。Fiber 的状态码通过 `c.Status()` 链式调用设置。
