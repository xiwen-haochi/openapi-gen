# PHP 框架路由识别参考

本文件覆盖 PHP 生态中三个主流后端框架的路由识别方式。

---

## Laravel

### 路由定义模式

**路由文件（`routes/api.php`）：**
```php
use App\Http\Controllers\UserController;

Route::get('/users', [UserController::class, 'index']);
Route::post('/users', [UserController::class, 'store']);
Route::get('/users/{user}', [UserController::class, 'show']);
Route::put('/users/{user}', [UserController::class, 'update']);
Route::delete('/users/{user}', [UserController::class, 'destroy']);

// 资源路由（自动生成 CRUD）
Route::apiResource('users', UserController::class);

// 路由分组
Route::prefix('api/v1')->group(function () {
    Route::middleware('auth:sanctum')->group(function () {
        Route::apiResource('users', UserController::class);
    });
});

// 嵌套资源
Route::apiResource('users.orders', OrderController::class);
// 生成: /users/{user}/orders, /users/{user}/orders/{order}
```

**`Route::apiResource` 自动生成的路由：**

| 方法 | URI | 控制器方法 |
|------|-----|-----------|
| GET | /users | index |
| POST | /users | store |
| GET | /users/{user} | show |
| PUT/PATCH | /users/{user} | update |
| DELETE | /users/{user} | destroy |

路径参数格式：`{name}` — 已经是 OpenAPI 格式。
可选参数：`{name?}`。
正则约束：`Route::get('/users/{id}', ...)->where('id', '[0-9]+');`

### 参数提取

**控制器方法：**
```php
class UserController extends Controller
{
    // 查询参数
    public function index(Request $request)
    {
        $page = $request->query('page', 1);
        $keyword = $request->input('keyword');
        $perPage = $request->integer('per_page', 20);
    }

    // 路径参数（路由模型绑定）
    public function show(User $user)  // 自动注入
    {
        return $user;
    }

    // 或手动获取
    public function show($id)
    {
        $user = User::findOrFail($id);
    }

    // 请求体
    public function store(CreateUserRequest $request)
    {
        $validated = $request->validated();
    }

    // 请求头
    public function profile(Request $request)
    {
        $token = $request->header('Authorization');
    }
}
```

### 数据模型识别

**FormRequest 验证类：**
```php
class CreateUserRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'username' => ['required', 'string', 'min:3', 'max:32', 'regex:/^[a-zA-Z0-9_]+$/'],
            'email' => ['required', 'email', 'unique:users'],
            'age' => ['nullable', 'integer', 'min:0', 'max:150'],
            'role' => ['required', 'in:admin,user,guest'],
            'tags' => ['array'],
            'tags.*' => ['string', 'max:50'],
            'avatar' => ['nullable', 'image', 'max:2048'],
        ];
    }

    public function messages(): array
    {
        return [
            'username.required' => '用户名不能为空',
            'email.email' => '请填写正确的邮箱地址',
        ];
    }
}
```

**Laravel 验证规则映射：**

| 规则 | OpenAPI 约束 |
|------|-------------|
| `required` | required: true |
| `nullable` | nullable: true |
| `string` | type: string |
| `integer` | type: integer |
| `numeric` | type: number |
| `boolean` | type: boolean |
| `array` | type: array |
| `email` | format: email |
| `url` | format: uri |
| `uuid` | format: uuid |
| `date` | format: date |
| `date_format:Y-m-d H:i:s` | format: date-time |
| `min:N` | minLength (string) / minimum (number) / minItems (array) |
| `max:N` | maxLength (string) / maximum (number) / maxItems (array) |
| `between:min,max` | 同时设置 min 和 max |
| `in:a,b,c` | enum: [a, b, c] |
| `regex:/pattern/` | pattern |
| `image` | format: binary |
| `file` | format: binary |
| `size:N` | 固定长度/大小 |

**Eloquent 模型：**
```php
class User extends Model
{
    protected $fillable = ['username', 'email', 'age', 'role'];

    protected $casts = [
        'age' => 'integer',
        'email_verified_at' => 'datetime',
        'is_active' => 'boolean',
        'settings' => 'array',
    ];

    protected $hidden = ['password', 'remember_token'];
}
```

`$casts` 提供类型信息，`$fillable` 和 `$hidden` 帮助确定哪些字段应出现在 API 中。

**API Resource（响应转换）：**
```php
class UserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'username' => $this->username,
            'email' => $this->email,
            'created_at' => $this->created_at->toISOString(),
        ];
    }
}
```

Resource 定义了响应结构。

### 扫描位置

1. `routes/api.php` — API 路由（最重要）
2. `routes/web.php` — Web 路由（可能含 API）
3. `app/Http/Controllers/` — 控制器
4. `app/Http/Requests/` — FormRequest 验证类
5. `app/Http/Resources/` — API Resource 响应转换
6. `app/Models/` — Eloquent 模型
7. `app/Http/Middleware/` — 中间件
8. `config/` — 配置文件（端口、环境等）

---

## ThinkPHP

### 路由定义模式

**路由文件（`route/app.php` 或 `route/route.php`）：**
```php
use think\facade\Route;

Route::get('users', 'UserController/index');
Route::post('users', 'UserController/store');
Route::get('users/:id', 'UserController/show');
Route::put('users/:id', 'UserController/update');
Route::delete('users/:id', 'UserController/destroy');

// 资源路由
Route::resource('users', 'UserController');

// 路由分组
Route::group('api/v1', function () {
    Route::resource('users', 'UserController');
})->middleware('auth');

// 注解路由（ThinkPHP 6+）
// 在控制器方法上使用 @route 注解
```

路径参数格式：`:name` → OpenAPI `{name}`。
带类型约束：`:id\d+` → integer 类型。

**`Route::resource` 自动生成的路由：**

| 方法 | URI | 控制器方法 |
|------|-----|-----------|
| GET | /users | index |
| GET | /users/create | create |
| POST | /users | save |
| GET | /users/:id | read |
| GET | /users/:id/edit | edit |
| PUT | /users/:id | update |
| DELETE | /users/:id | delete |

### 参数提取

```php
use think\Request;

class UserController extends BaseController
{
    // 查询参数
    public function index(Request $request)
    {
        $page = $request->param('page', 1, 'intval');
        $keyword = $request->param('keyword', '', 'trim');
    }

    // 路径参数
    public function show($id)
    {
        $user = UserModel::find($id);
    }

    // 请求体
    public function store(Request $request)
    {
        $data = $request->post();
        // 或
        $data = $request->only(['username', 'email', 'age']);
    }

    // 请求头
    public function profile(Request $request)
    {
        $token = $request->header('Authorization');
    }
}
```

### 数据模型识别

**验证器类：**
```php
class UserValidate extends Validate
{
    protected $rule = [
        'username' => 'require|length:3,32|alphaNum',
        'email' => 'require|email',
        'age' => 'number|between:0,150',
        'role' => 'require|in:admin,user,guest',
    ];

    protected $message = [
        'username.require' => '用户名不能为空',
        'email.email' => '请填写正确的邮箱',
    ];
}
```

**ThinkPHP 验证规则映射：**

| 规则 | OpenAPI 约束 |
|------|-------------|
| `require` | required: true |
| `number` | type: number |
| `integer` | type: integer |
| `email` | format: email |
| `url` | format: uri |
| `length:min,max` | minLength / maxLength |
| `between:min,max` | minimum / maximum |
| `in:a,b,c` | enum: [a, b, c] |
| `regex:pattern` | pattern |
| `boolean` | type: boolean |
| `array` | type: array |
| `float` | type: number, format: float |

### 扫描位置

1. `route/app.php` / `route/route.php` — 路由定义
2. `app/controller/` — 控制器
3. `app/validate/` — 验证器
4. `app/model/` — 模型
5. `config/` — 配置文件

---

## Symfony

### 路由定义模式

**PHP 属性路由（Symfony 6+，推荐）：**
```php
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\HttpFoundation\JsonResponse;

#[Route('/api/users', name: 'api_users_')]
class UserController extends AbstractController
{
    #[Route('', name: 'list', methods: ['GET'])]
    public function list(Request $request): JsonResponse { ... }

    #[Route('', name: 'create', methods: ['POST'])]
    public function create(Request $request): JsonResponse { ... }

    #[Route('/{id}', name: 'show', methods: ['GET'])]
    public function show(int $id): JsonResponse { ... }

    #[Route('/{id}', name: 'update', methods: ['PUT'])]
    public function update(int $id, Request $request): JsonResponse { ... }

    #[Route('/{id}', name: 'delete', methods: ['DELETE'])]
    public function delete(int $id): JsonResponse { ... }
}
```

**YAML 路由（`config/routes.yaml`）：**
```yaml
api_users_list:
    path: /api/users
    controller: App\Controller\UserController::list
    methods: GET

api_users_create:
    path: /api/users
    controller: App\Controller\UserController::create
    methods: POST
```

**参数类型约束：**
```php
#[Route('/{id}', requirements: ['id' => '\d+'])]
public function show(int $id): JsonResponse { ... }
```

路径参数格式：`{name}` — 已经是 OpenAPI 格式。

### 参数提取

```php
use Symfony\Component\HttpFoundation\Request;

// 查询参数
$page = $request->query->getInt('page', 1);
$keyword = $request->query->get('keyword');

// 请求体（JSON）
$data = json_decode($request->getContent(), true);

// 或使用 Serializer
$dto = $serializer->deserialize($request->getContent(), CreateUserDto::class, 'json');

// 请求头
$token = $request->headers->get('Authorization');

// 路径参数（通过方法参数自动注入）
public function show(int $id): JsonResponse { ... }
```

### 数据模型识别

**DTO + Symfony Validator：**
```php
use Symfony\Component\Validator\Constraints as Assert;

class CreateUserDto
{
    #[Assert\NotBlank(message: '用户名不能为空')]
    #[Assert\Length(min: 3, max: 32)]
    #[Assert\Regex(pattern: '/^[a-zA-Z0-9_]+$/')]
    public string $username;

    #[Assert\NotBlank]
    #[Assert\Email]
    public string $email;

    #[Assert\Range(min: 0, max: 150)]
    public ?int $age = null;

    #[Assert\Choice(choices: ['admin', 'user', 'guest'])]
    public string $role = 'user';

    #[Assert\All([
        new Assert\Type('string'),
        new Assert\Length(max: 50),
    ])]
    public array $tags = [];
}
```

**Symfony Validator 约束映射：**

| 约束 | OpenAPI |
|------|---------|
| `#[Assert\NotBlank]` | required: true |
| `#[Assert\Length(min, max)]` | minLength / maxLength |
| `#[Assert\Range(min, max)]` | minimum / maximum |
| `#[Assert\Email]` | format: email |
| `#[Assert\Url]` | format: uri |
| `#[Assert\Uuid]` | format: uuid |
| `#[Assert\Regex(pattern)]` | pattern |
| `#[Assert\Choice(choices)]` | enum |
| `#[Assert\Type('integer')]` | type: integer |
| `#[Assert\Type('boolean')]` | type: boolean |
| `#[Assert\Count(min, max)]` | minItems / maxItems |
| `#[Assert\Positive]` | minimum: 1 |
| `#[Assert\PositiveOrZero]` | minimum: 0 |

**API Platform（如果使用）：**
```php
use ApiPlatform\Metadata\ApiResource;
use ApiPlatform\Metadata\Get;
use ApiPlatform\Metadata\GetCollection;
use ApiPlatform\Metadata\Post;

#[ApiResource(
    operations: [
        new GetCollection(description: '获取用户列表'),
        new Get(description: '获取用户详情'),
        new Post(description: '创建用户'),
    ]
)]
class User { ... }
```

API Platform 自动生成 OpenAPI 规范。如果项目已使用 API Platform，优先从其配置中提取信息。

**NelmioApiDocBundle（如果使用）：**
```php
use OpenApi\Attributes as OA;

#[OA\Tag(name: '用户管理')]
class UserController
{
    #[OA\Get(summary: '获取用户列表')]
    #[OA\Response(response: 200, description: '成功')]
    public function list(): JsonResponse { ... }
}
```

### PHP 类型映射

| PHP 类型 | OpenAPI type + format |
|----------|----------------------|
| `string` | string |
| `int` | integer, format: int32 |
| `float` | number, format: float |
| `bool` | boolean |
| `array` | array 或 object（看上下文） |
| `\DateTimeInterface` | string, format: date-time |
| `?type` (nullable) | nullable: true |
| enum (PHP 8.1+) | enum: [...] |

### 扫描位置

1. `src/Controller/` — 控制器
2. `src/Dto/` / `src/Request/` — DTO 类
3. `src/Entity/` — Doctrine 实体
4. `config/routes.yaml` / `config/routes/` — YAML 路由配置
5. `src/EventSubscriber/` — 事件订阅（可能影响响应）
6. `config/packages/` — 包配置
