# Java 框架路由识别参考

本文件覆盖 Java 生态中三个主流后端框架的路由识别方式。

---

## Spring Boot / Spring MVC

### 路由定义模式

**控制器识别：**
- 标注 `@RestController` 或 `@Controller` 的类
- 类级别 `@RequestMapping("/prefix")` 定义路径前缀

**路由注解（方法级别）：**

| 注解 | HTTP 方法 |
|------|-----------|
| `@GetMapping("/path")` | GET |
| `@PostMapping("/path")` | POST |
| `@PutMapping("/path")` | PUT |
| `@DeleteMapping("/path")` | DELETE |
| `@PatchMapping("/path")` | PATCH |
| `@RequestMapping(value="/path", method=RequestMethod.GET)` | 由 method 决定 |

完整路径 = 类级别 `@RequestMapping` 前缀 + 方法级别注解路径。

**路径参数：**
```java
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) { ... }

@GetMapping("/users/{userId}/orders/{orderId}")
public Order getOrder(@PathVariable("userId") Long uid, @PathVariable("orderId") Long oid) { ... }
```

**查询参数：**
```java
@GetMapping("/users")
public List<User> listUsers(
    @RequestParam(defaultValue = "1") Integer page,
    @RequestParam(defaultValue = "20") Integer pageSize,
    @RequestParam(required = false) String keyword
) { ... }
```

**请求头：**
```java
@GetMapping("/profile")
public User getProfile(@RequestHeader("Authorization") String token) { ... }
```

**请求体：**
```java
@PostMapping("/users")
public User createUser(@RequestBody @Valid CreateUserDTO dto) { ... }
```

### 数据模型识别

**DTO / VO / Request / Response 类：**
- 通常在 `dto`、`vo`、`request`、`response`、`model`、`entity`、`domain` 包下
- 关注字段上的校验注解：

| 注解 | OpenAPI 约束 |
|------|-------------|
| `@NotNull` / `@NotBlank` / `@NotEmpty` | required: true |
| `@Size(min=3, max=32)` | minLength / maxLength |
| `@Min(1)` / `@Max(100)` | minimum / maximum |
| `@Pattern(regexp="...")` | pattern |
| `@Email` | format: email |
| `@Past` / `@Future` | description 中说明 |
| `@Positive` / `@PositiveOrZero` | minimum: 1 / minimum: 0 |

**字段类型映射：**

| Java 类型 | OpenAPI type + format |
|-----------|----------------------|
| `String` | string |
| `Integer` / `int` | integer, format: int32 |
| `Long` / `long` | integer, format: int64 |
| `Float` / `float` | number, format: float |
| `Double` / `double` | number, format: double |
| `BigDecimal` | number |
| `Boolean` / `boolean` | boolean |
| `LocalDateTime` / `Date` | string, format: date-time |
| `LocalDate` | string, format: date |
| `List<T>` | array, items: T 的 schema |
| `Map<String, T>` | object, additionalProperties: T 的 schema |
| 枚举类 | string, enum: [枚举值列表] |

### 响应结构识别

**常见通用响应包装：**
```java
public class Result<T> {
    private Integer code;
    private String message;
    private T data;
}
```

如果存在此类统一包装，所有接口的响应 schema 应反映此结构。

**Swagger/OpenAPI 注解（如项目已使用）：**
- `@Operation(summary="...", description="...")`
- `@ApiResponse(responseCode="200", description="...")`
- `@Schema(description="...", example="...")`
- `@Tag(name="...", description="...")`

如果代码中已有这些注解，优先使用注解中的描述信息。

### 扫描位置

1. `src/main/java/**/controller/` — 控制器目录
2. `src/main/java/**/rest/` — REST 控制器
3. `src/main/java/**/api/` — API 控制器
4. `src/main/java/**/web/` — Web 控制器
5. `src/main/java/**/dto/` — 数据传输对象
6. `src/main/java/**/vo/` — 视图对象
7. `src/main/java/**/entity/` / `domain/` — 实体类
8. `src/main/java/**/config/` — 可能包含路由配置

---

## Spring Cloud

Spring Cloud 在 Spring Boot 基础上增加了微服务相关的路由方式。

### Feign Client（声明式服务调用）

```java
@FeignClient(name = "user-service", path = "/api/users")
public interface UserClient {
    @GetMapping("/{id}")
    User getUser(@PathVariable Long id);

    @PostMapping
    User createUser(@RequestBody CreateUserDTO dto);
}
```

Feign Client 接口定义了对外暴露的 API 契约，应作为接口来源。

### Gateway 路由

```yaml
# application.yml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
```

Gateway 路由配置体现了 API 的统一入口路径前缀，生成 OpenAPI 时需要将 Gateway 的路径前缀与各服务的实际路径合并。

### 扫描位置

1. 所有 Spring Boot 的扫描位置
2. 带 `@FeignClient` 注解的接口
3. `application.yml` / `application.properties` 中的 Gateway 路由配置
4. `bootstrap.yml` 中的服务配置

---

## Quarkus（JAX-RS）

### 路由定义模式

**资源类识别：**
- 标注 `@Path("/prefix")` 的类
- 类通常命名为 `*Resource`

**路由注解：**

| 注解 | HTTP 方法 |
|------|-----------|
| `@GET` | GET |
| `@POST` | POST |
| `@PUT` | PUT |
| `@DELETE` | DELETE |
| `@PATCH` | PATCH |

```java
@Path("/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {

    @GET
    public List<User> list(@QueryParam("page") @DefaultValue("1") int page) { ... }

    @GET
    @Path("/{id}")
    public User get(@PathParam("id") Long id) { ... }

    @POST
    public Response create(@Valid CreateUserDTO dto) { ... }

    @PUT
    @Path("/{id}")
    public User update(@PathParam("id") Long id, @Valid UpdateUserDTO dto) { ... }

    @DELETE
    @Path("/{id}")
    public void delete(@PathParam("id") Long id) { ... }
}
```

**参数注解：**

| 注解 | 对应 OpenAPI |
|------|-------------|
| `@PathParam("name")` | parameters, in: path |
| `@QueryParam("name")` | parameters, in: query |
| `@HeaderParam("name")` | parameters, in: header |
| `@DefaultValue("value")` | schema.default |
| `@FormParam("name")` | requestBody, multipart/form-data |

**请求体：** 无注解的 POJO 参数即为请求体（JAX-RS 约定）。

### 数据模型识别

与 Spring Boot 相同的校验注解（`javax.validation` / `jakarta.validation`）。

Quarkus 还支持 Panache 实体：
```java
@Entity
public class User extends PanacheEntity {
    public String username;
    public String email;
}
```

### 扫描位置

1. `src/main/java/**/resource/` — 资源类
2. `src/main/java/**/endpoint/` — 端点类
3. `src/main/java/**/rest/` — REST 资源
4. `src/main/java/**/dto/` / `model/` / `entity/` — 数据模型
