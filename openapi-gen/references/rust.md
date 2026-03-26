# Rust 框架路由识别参考

本文件覆盖 Rust 生态中三个主流 Web 框架的路由识别方式。

---

## Axum

### 路由定义模式

```rust
use axum::{
    routing::{get, post, put, delete, patch},
    Router,
};

let app = Router::new()
    .route("/users", get(list_users).post(create_user))
    .route("/users/:id", get(get_user).put(update_user).delete(delete_user))
    .route("/users/:id/status", patch(update_status));

// 嵌套路由
let users = Router::new()
    .route("/", get(list_users).post(create_user))
    .route("/:id", get(get_user).put(update_user).delete(delete_user));

let app = Router::new()
    .nest("/api/v1/users", users);

// 带状态
let app = Router::new()
    .route("/users", get(list_users))
    .with_state(app_state);
```

路径参数格式：`:name` → OpenAPI `{name}`。

**路由函数映射：**

| 函数 | HTTP 方法 |
|------|-----------|
| `get(handler)` | GET |
| `post(handler)` | POST |
| `put(handler)` | PUT |
| `delete(handler)` | DELETE |
| `patch(handler)` | PATCH |
| `any(handler)` | 所有方法 |
| `MethodRouter::on(MethodFilter::GET, handler)` | 由 filter 决定 |

### 参数提取（Extractors）

```rust
use axum::extract::{Path, Query, Json, State};
use axum::http::HeaderMap;

// 路径参数
async fn get_user(Path(id): Path<u64>) -> impl IntoResponse { ... }

// 多个路径参数
async fn get_order(Path((user_id, order_id)): Path<(u64, u64)>) -> impl IntoResponse { ... }

// 查询参数
#[derive(Deserialize)]
struct ListParams {
    page: Option<u32>,
    page_size: Option<u32>,
    keyword: Option<String>,
}
async fn list_users(Query(params): Query<ListParams>) -> impl IntoResponse { ... }

// 请求体（JSON）
async fn create_user(Json(payload): Json<CreateUserRequest>) -> impl IntoResponse { ... }

// 请求头
async fn profile(headers: HeaderMap) -> impl IntoResponse {
    let token = headers.get("Authorization");
    ...
}

// 或使用 TypedHeader
use axum_extra::headers::Authorization;
use axum_extra::TypedHeader;
async fn profile(TypedHeader(auth): TypedHeader<Authorization<Bearer>>) -> impl IntoResponse { ... }
```

**提取器 → OpenAPI 参数映射：**

| 提取器 | OpenAPI |
|--------|---------|
| `Path<T>` | in: path |
| `Query<T>` | in: query（T 的每个字段为一个 query 参数） |
| `Json<T>` | requestBody (application/json) |
| `Form<T>` | requestBody (application/x-www-form-urlencoded) |
| `Multipart` | requestBody (multipart/form-data) |
| `HeaderMap` / `TypedHeader` | in: header |

### 数据模型识别

Rust 使用 `serde` 和 `validator` crate：

```rust
use serde::{Deserialize, Serialize};
use validator::Validate;

#[derive(Deserialize, Validate)]
pub struct CreateUserRequest {
    /// 用户名
    #[validate(length(min = 3, max = 32))]
    #[validate(regex(path = "RE_USERNAME"))]
    pub username: String,

    /// 邮箱地址
    #[validate(email)]
    pub email: String,

    /// 年龄
    #[validate(range(min = 0, max = 150))]
    pub age: Option<u32>,

    /// 角色
    pub role: UserRole,

    /// 标签列表
    #[serde(default)]
    pub tags: Vec<String>,
}

#[derive(Serialize)]
pub struct UserResponse {
    /// 用户 ID
    pub id: u64,
    /// 用户名
    pub username: String,
    /// 邮箱地址
    pub email: String,
    /// 创建时间
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UserRole {
    Admin,
    User,
    Guest,
}
```

**validator 宏映射：**

| 验证宏 | OpenAPI 约束 |
|--------|-------------|
| `#[validate(length(min=N, max=M))]` | minLength / maxLength |
| `#[validate(range(min=N, max=M))]` | minimum / maximum |
| `#[validate(email)]` | format: email |
| `#[validate(url)]` | format: uri |
| `#[validate(regex(...))]` | pattern |
| `#[validate(contains(...))]` | description 中说明 |
| `#[validate(must_match(...))]` | description 中说明 |

**serde 属性映射：**

| 属性 | 影响 |
|------|------|
| `#[serde(rename = "name")]` | 字段名 |
| `#[serde(rename_all = "camelCase")]` | 所有字段名转换 |
| `#[serde(default)]` | required: false, 有默认值 |
| `#[serde(skip_serializing)]` | writeOnly（仅输入） |
| `#[serde(skip_deserializing)]` | readOnly（仅输出） |
| `#[serde(flatten)]` | 展开嵌套结构 |

**Rust 类型映射：**

| Rust 类型 | OpenAPI type + format |
|-----------|----------------------|
| `String` / `&str` | string |
| `i32` | integer, format: int32 |
| `i64` | integer, format: int64 |
| `u32` | integer, format: int32, minimum: 0 |
| `u64` | integer, format: int64, minimum: 0 |
| `f32` | number, format: float |
| `f64` | number, format: double |
| `bool` | boolean |
| `chrono::DateTime<Utc>` | string, format: date-time |
| `chrono::NaiveDate` | string, format: date |
| `uuid::Uuid` | string, format: uuid |
| `Vec<T>` | array, items: T |
| `HashMap<String, T>` | object, additionalProperties: T |
| `Option<T>` | required: false, nullable |
| `serde_json::Value` | object（任意 JSON） |
| enum（带 serde） | string, enum: [...] |
| `Bytes` / `Vec<u8>` | string, format: binary |

### 响应结构

```rust
// 常见做法：返回 Json<T>
async fn get_user(Path(id): Path<u64>) -> Json<UserResponse> { ... }

// 带状态码
async fn create_user(Json(req): Json<CreateUserRequest>) -> (StatusCode, Json<UserResponse>) { ... }

// Result 类型
async fn get_user(Path(id): Path<u64>) -> Result<Json<UserResponse>, AppError> { ... }
```

关注返回类型中的泛型参数来确定响应 schema。

### 扫描位置

1. `src/main.rs` — 入口和路由注册
2. `src/routes/` / `src/router.rs` — 路由模块
3. `src/handlers/` / `src/api/` — 处理函数
4. `src/models/` / `src/dto/` / `src/types.rs` — 数据模型
5. `src/errors.rs` — 错误类型
6. `Cargo.toml` — 判断使用的框架和依赖

---

## Actix Web

### 路由定义模式

**宏路由（推荐）：**
```rust
use actix_web::{get, post, put, delete, patch, web, HttpResponse};

#[get("/users")]
async fn list_users(query: web::Query<ListParams>) -> HttpResponse { ... }

#[get("/users/{id}")]
async fn get_user(path: web::Path<u64>) -> HttpResponse { ... }

#[post("/users")]
async fn create_user(body: web::Json<CreateUserRequest>) -> HttpResponse { ... }

#[put("/users/{id}")]
async fn update_user(
    path: web::Path<u64>,
    body: web::Json<UpdateUserRequest>,
) -> HttpResponse { ... }

#[delete("/users/{id}")]
async fn delete_user(path: web::Path<u64>) -> HttpResponse { ... }
```

**手动路由注册：**
```rust
App::new()
    .service(
        web::scope("/api/v1")
            .service(
                web::resource("/users")
                    .route(web::get().to(list_users))
                    .route(web::post().to(create_user))
            )
            .service(
                web::resource("/users/{id}")
                    .route(web::get().to(get_user))
                    .route(web::put().to(update_user))
                    .route(web::delete().to(delete_user))
            )
    );

// 或使用 configure
fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/users")
            .route("", web::get().to(list_users))
            .route("", web::post().to(create_user))
            .route("/{id}", web::get().to(get_user))
    );
}
```

路径参数格式：`{name}` — 已经是 OpenAPI 格式。

**路由宏映射：**

| 宏 | HTTP 方法 |
|----|-----------|
| `#[get("/path")]` | GET |
| `#[post("/path")]` | POST |
| `#[put("/path")]` | PUT |
| `#[delete("/path")]` | DELETE |
| `#[patch("/path")]` | PATCH |

### 参数提取

| 提取器 | OpenAPI |
|--------|---------|
| `web::Path<T>` | in: path |
| `web::Query<T>` | in: query |
| `web::Json<T>` | requestBody (application/json) |
| `web::Form<T>` | requestBody (form) |
| `web::Header<T>` | in: header |
| `actix_multipart::Multipart` | requestBody (multipart) |

### 数据模型识别

与 Axum 完全相同的 `serde` + `validator` 体系。

### 响应结构

```rust
// HttpResponse
async fn get_user(...) -> HttpResponse {
    HttpResponse::Ok().json(user)
}

// impl Responder
async fn get_user(...) -> impl Responder {
    web::Json(user)
}

// 带错误
async fn get_user(...) -> Result<HttpResponse, AppError> { ... }
```

### 扫描位置

与 Axum 相同，另外注意：
- `src/lib.rs` — 可能包含路由配置
- `src/services/` — 服务层

---

## Rocket

### 路由定义模式

**宏路由：**
```rust
use rocket::serde::json::Json;
use rocket::{get, post, put, delete, patch};

#[get("/users?<page>&<page_size>&<keyword>")]
async fn list_users(page: Option<u32>, page_size: Option<u32>, keyword: Option<String>) -> Json<Vec<UserResponse>> { ... }

#[get("/users/<id>")]
async fn get_user(id: u64) -> Option<Json<UserResponse>> { ... }

#[post("/users", data = "<req>")]
async fn create_user(req: Json<CreateUserRequest>) -> (rocket::http::Status, Json<UserResponse>) { ... }

#[put("/users/<id>", data = "<req>")]
async fn update_user(id: u64, req: Json<UpdateUserRequest>) -> Json<UserResponse> { ... }

#[delete("/users/<id>")]
async fn delete_user(id: u64) -> rocket::http::Status { ... }
```

**路由注册：**
```rust
#[launch]
fn rocket() -> _ {
    rocket::build()
        .mount("/api/v1", routes![list_users, get_user, create_user, update_user, delete_user])
        .mount("/api/v1/admin", routes![admin_stats, admin_users])
}
```

完整路径 = `mount` 前缀 + 宏路由路径。

路径参数格式：`<name>` → OpenAPI `{name}`。
带类型：`<id>` 的类型由函数参数类型决定。

**路由宏：**

| 宏 | HTTP 方法 |
|----|-----------|
| `#[get("/path")]` | GET |
| `#[post("/path")]` | POST |
| `#[put("/path")]` | PUT |
| `#[delete("/path")]` | DELETE |
| `#[patch("/path")]` | PATCH |

### 参数提取

Rocket 的参数提取通过函数签名自动推断：

- **路径参数**：`<name>` 对应函数参数 `name: Type`
- **查询参数**：`?<param>` 对应函数参数 `param: Option<Type>` 或 `param: Type`
- **请求体**：`data = "<name>"` 对应 `name: Json<T>` 或 `name: Form<T>`
- **请求头**：使用 Request Guard

```rust
// 自定义请求头
use rocket::request::{FromRequest, Outcome};

struct AuthToken(String);

#[rocket::async_trait]
impl<'r> FromRequest<'r> for AuthToken {
    type Error = ();
    async fn from_request(req: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        match req.headers().get_one("Authorization") {
            Some(token) => Outcome::Success(AuthToken(token.to_string())),
            None => Outcome::Error((Status::Unauthorized, ())),
        }
    }
}

#[get("/profile")]
async fn profile(token: AuthToken) -> Json<UserResponse> { ... }
```

### 数据模型识别

与 Axum/Actix Web 相同的 `serde` + `validator` 体系。

Rocket 特有的表单结构：
```rust
#[derive(FromForm)]
struct LoginForm {
    username: String,
    password: String,
    remember: bool,
}
```

`#[derive(FromForm)]` 表示表单数据模型。

### 响应结构

```rust
// Json<T> — 直接返回 200
async fn get_user(id: u64) -> Json<UserResponse> { ... }

// Option<Json<T>> — 返回 200 或 404
async fn get_user(id: u64) -> Option<Json<UserResponse>> { ... }

// Result<Json<T>, Status> — 可能返回错误
async fn get_user(id: u64) -> Result<Json<UserResponse>, Status> { ... }

// (Status, Json<T>) — 自定义状态码
async fn create_user(req: Json<CreateUserRequest>) -> (Status, Json<UserResponse>) { ... }
```

Rocket 的返回类型直接反映响应结构：
- `Json<T>` → 200, body: T
- `Option<Json<T>>` → 200 或 404
- `Result<T, E>` → 成功或错误
- `Status` → 仅状态码，无 body
- `(Status, Json<T>)` → 自定义状态码 + body

### 扫描位置

1. `src/main.rs` — `#[launch]` 入口和 `mount` 路由注册
2. `src/routes/` / `src/api/` — 路由处理函数
3. `src/models/` / `src/dto/` — 数据模型
4. `src/guards/` / `src/fairings/` — Request Guard（可能影响参数）
5. `src/errors.rs` — 错误类型
6. `Rocket.toml` — 服务器配置（端口、环境等）
7. `Cargo.toml` — 依赖信息
