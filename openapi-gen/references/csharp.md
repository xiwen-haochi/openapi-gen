# C# 框架路由识别参考

本文件覆盖 C# / .NET 生态中三个后端框架的路由识别方式。

---

## ASP.NET Core

### 路由定义模式

**属性路由（推荐）：**
```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet]
    public ActionResult<IEnumerable<UserDto>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? keyword = null) { ... }

    [HttpGet("{id}")]
    public ActionResult<UserDto> GetById(int id) { ... }

    [HttpPost]
    public ActionResult<UserDto> Create([FromBody] CreateUserDto dto) { ... }

    [HttpPut("{id}")]
    public ActionResult<UserDto> Update(int id, [FromBody] UpdateUserDto dto) { ... }

    [HttpDelete("{id}")]
    public ActionResult Delete(int id) { ... }

    [HttpPatch("{id}/status")]
    public ActionResult UpdateStatus(int id, [FromBody] UpdateStatusDto dto) { ... }
}
```

**路由属性：**

| 属性 | HTTP 方法 |
|------|-----------|
| `[HttpGet]` / `[HttpGet("path")]` | GET |
| `[HttpPost]` / `[HttpPost("path")]` | POST |
| `[HttpPut]` / `[HttpPut("path")]` | PUT |
| `[HttpDelete]` / `[HttpDelete("path")]` | DELETE |
| `[HttpPatch]` / `[HttpPatch("path")]` | PATCH |

完整路径 = `[Route]` 前缀 + 方法属性路径。`[controller]` 会替换为控制器名称（去掉 Controller 后缀，首字母小写）。

**Minimal API（.NET 6+）：**
```csharp
var app = builder.Build();

app.MapGet("/users", GetUsers);
app.MapPost("/users", CreateUser);
app.MapGet("/users/{id}", GetUser);
app.MapPut("/users/{id}", UpdateUser);
app.MapDelete("/users/{id}", DeleteUser);

// 路由分组
var api = app.MapGroup("/api/v1");
var users = api.MapGroup("/users");
users.MapGet("/", GetUsers);
users.MapPost("/", CreateUser);
```

路径参数格式：`{name}` — 已经是 OpenAPI 格式。
类型约束：`{id:int}`, `{name:alpha}`, `{id:guid}`。

### 参数绑定

| 属性 | OpenAPI 参数 |
|------|-------------|
| `[FromRoute]` / 路径参数 | in: path |
| `[FromQuery]` | in: query |
| `[FromHeader]` | in: header |
| `[FromBody]` | requestBody |
| `[FromForm]` | requestBody (multipart/form-data) |

### 数据模型识别

**DTO + DataAnnotations：**
```csharp
using System.ComponentModel.DataAnnotations;

public class CreateUserDto
{
    [Required(ErrorMessage = "用户名不能为空")]
    [StringLength(32, MinimumLength = 3)]
    [RegularExpression(@"^[a-zA-Z0-9_]+$")]
    public string Username { get; set; } = string.Empty;

    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Range(0, 150)]
    public int? Age { get; set; }

    [Required]
    [EnumDataType(typeof(UserRole))]
    public UserRole Role { get; set; }

    [MaxLength(500)]
    public string? Bio { get; set; }

    [Url]
    public string? Website { get; set; }

    [Phone]
    public string? Phone { get; set; }
}

public enum UserRole
{
    Admin,
    User,
    Guest
}
```

**DataAnnotations 映射：**

| 属性 | OpenAPI 约束 |
|------|-------------|
| `[Required]` | required: true |
| `[StringLength(max, MinimumLength=min)]` | minLength / maxLength |
| `[MaxLength(n)]` | maxLength |
| `[MinLength(n)]` | minLength |
| `[Range(min, max)]` | minimum / maximum |
| `[EmailAddress]` | format: email |
| `[Url]` | format: uri |
| `[Phone]` | pattern (电话格式) |
| `[RegularExpression(pattern)]` | pattern |
| `[EnumDataType(typeof(E))]` | enum: [...] |
| `[CreditCard]` | description 注明 |
| `[FileExtensions]` | description 注明 |

**FluentValidation（如使用）：**
```csharp
public class CreateUserValidator : AbstractValidator<CreateUserDto>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Username).NotEmpty().Length(3, 32).Matches(@"^[a-zA-Z0-9_]+$");
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Age).InclusiveBetween(0, 150).When(x => x.Age.HasValue);
        RuleFor(x => x.Role).IsInEnum();
    }
}
```

**C# 类型映射：**

| C# 类型 | OpenAPI type + format |
|---------|----------------------|
| `string` | string |
| `int` | integer, format: int32 |
| `long` | integer, format: int64 |
| `float` | number, format: float |
| `double` | number, format: double |
| `decimal` | number |
| `bool` | boolean |
| `DateTime` / `DateTimeOffset` | string, format: date-time |
| `DateOnly` | string, format: date |
| `TimeOnly` | string, format: time |
| `Guid` | string, format: uuid |
| `byte[]` | string, format: byte |
| `IFormFile` | string, format: binary |
| `List<T>` / `IEnumerable<T>` | array, items: T |
| `Dictionary<string, T>` | object, additionalProperties: T |
| `T?` (nullable) | nullable: true |
| `enum` | string/integer, enum: [...] |

### 响应结构

```csharp
// ActionResult<T> — T 定义了成功响应的模型
[ProducesResponseType(typeof(UserDto), StatusCodes.Status200OK)]
[ProducesResponseType(StatusCodes.Status404NotFound)]
[ProducesResponseType(StatusCodes.Status400BadRequest)]
public ActionResult<UserDto> GetById(int id) { ... }
```

`[ProducesResponseType]` 属性直接映射为 OpenAPI responses。

**Swagger/Swashbuckle 注解（如果已使用）：**
```csharp
[SwaggerOperation(Summary = "获取用户详情", Description = "根据ID获取用户信息")]
[SwaggerResponse(200, "成功", typeof(UserDto))]
[SwaggerResponse(404, "用户不存在")]
```

### 扫描位置

1. `Controllers/` — 控制器
2. `Dtos/` / `Models/` / `ViewModels/` — 数据模型
3. `Entities/` — EF Core 实体
4. `Validators/` — FluentValidation 验证器
5. `Program.cs` / `Startup.cs` — 路由配置和中间件
6. `Endpoints/` — Minimal API 端点（.NET 6+）
7. `*.csproj` — 依赖和版本信息

---

## ABP Framework

ABP 基于 ASP.NET Core，有自己的约定。

### 路由定义模式

ABP 通过 Application Service 自动生成 API 端点：

```csharp
// 接口定义（契约层）
public interface IUserAppService : ICrudAppService<
    UserDto,          // 输出 DTO
    Guid,             // 主键类型
    PagedAndSortedResultRequestDto,  // 分页查询输入
    CreateUserDto,    // 创建输入
    UpdateUserDto>    // 更新输入
{
    Task<UserDto> GetByUsernameAsync(string username);
}

// 实现
public class UserAppService : CrudAppService<
    User, UserDto, Guid,
    PagedAndSortedResultRequestDto,
    CreateUserDto, UpdateUserDto>,
    IUserAppService
{
    public async Task<UserDto> GetByUsernameAsync(string username) { ... }
}
```

**ICrudAppService 自动生成的路由：**

| 方法 | HTTP | URI |
|------|------|-----|
| `GetListAsync` | GET | /api/app/user |
| `GetAsync` | GET | /api/app/user/{id} |
| `CreateAsync` | POST | /api/app/user |
| `UpdateAsync` | PUT | /api/app/user/{id} |
| `DeleteAsync` | DELETE | /api/app/user/{id} |
| `GetByUsernameAsync` | GET | /api/app/user/by-username?username= |

**ABP 路由约定：**
- 前缀：`/api/app/`（默认，可配置）
- 服务名去掉 `AppService` 后缀，转为 kebab-case
- 方法名转为 HTTP 方法 + 路由：
  - `Get*` → GET
  - `Create*` → POST
  - `Update*` → PUT
  - `Delete*` → DELETE
  - 其他方法名 → kebab-case 的 action 路由

### 数据模型识别

```csharp
public class CreateUserDto
{
    [Required]
    [StringLength(UserConsts.MaxUsernameLength, MinimumLength = UserConsts.MinUsernameLength)]
    public string Username { get; set; }

    [Required]
    [EmailAddress]
    public string Email { get; set; }

    public int? Age { get; set; }
}

// ABP 内置分页响应
// PagedResultDto<T> 包含 Items (List<T>) 和 TotalCount (long)
```

验证规则与 ASP.NET Core DataAnnotations 相同。

### 扫描位置

1. `*.Application.Contracts/` — 接口定义和 DTO
2. `*.Application/` — 服务实现
3. `*.Domain/` — 领域实体
4. `*.HttpApi/` — 自定义 Controller（如有）
5. `*.HttpApi.Host/` — 启动配置

---

## NancyFX

NancyFX 目前已不再维护，但仍有旧项目使用。

### 路由定义模式

```csharp
public class UserModule : NancyModule
{
    public UserModule() : base("/api/users")
    {
        Get("/", args => ListUsers());
        Get("/{id}", args => GetUser(args.id));
        Post("/", args => CreateUser());
        Put("/{id}", args => UpdateUser(args.id));
        Delete("/{id}", args => DeleteUser(args.id));
    }

    private object ListUsers()
    {
        var page = Request.Query["page"] ?? 1;
        var keyword = Request.Query["keyword"];
        ...
    }

    private object CreateUser()
    {
        var dto = this.Bind<CreateUserDto>();
        ...
    }
}
```

**路由方法：**

| 方法 | HTTP 方法 |
|------|-----------|
| `Get["/path"]` 或 `Get("/path", ...)` | GET |
| `Post["/path"]` 或 `Post("/path", ...)` | POST |
| `Put["/path"]` 或 `Put("/path", ...)` | PUT |
| `Delete["/path"]` 或 `Delete("/path", ...)` | DELETE |
| `Patch["/path"]` 或 `Patch("/path", ...)` | PATCH |

完整路径 = `base("/prefix")` + 方法路径。

### 参数提取

```csharp
// 路径参数
var id = args.id;  // 动态参数

// 查询参数
var page = Request.Query["page"];

// 请求体
var dto = this.Bind<CreateUserDto>();   // 需要 Nancy.ModelBinding
var dto = this.BindAndValidate<CreateUserDto>();  // 带验证

// 请求头
var token = Request.Headers["Authorization"].FirstOrDefault();
```

### 数据模型识别

NancyFX 使用 FluentValidation：

```csharp
public class CreateUserDtoValidator : AbstractValidator<CreateUserDto>
{
    public CreateUserDtoValidator()
    {
        RuleFor(x => x.Username).NotEmpty().Length(3, 32);
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
    }
}
```

映射规则与 ASP.NET Core 的 FluentValidation 相同。

### 扫描位置

1. `Modules/` / `*Module.cs` — Nancy 模块
2. `Models/` / `Dtos/` — 数据模型
3. `Validators/` — FluentValidation 验证器
4. `Bootstrapper.cs` — 启动配置
