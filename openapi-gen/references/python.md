# Python 框架路由识别参考

本文件覆盖 Python 生态中三个主流 Web 框架的路由识别方式。

---

## Django / Django REST Framework (DRF)

### 路由定义模式

**URL 配置（urls.py）：**
```python
# 原生 Django
from django.urls import path, include

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('api/', include('api.urls')),  # 嵌套路由
]
```

**DRF Router 自动注册：**
```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = router.urls
```

Router 会自动生成以下路由：
- `GET /users/` — list
- `POST /users/` — create
- `GET /users/{id}/` — retrieve
- `PUT /users/{id}/` — update
- `PATCH /users/{id}/` — partial_update
- `DELETE /users/{id}/` — destroy
- 额外通过 `@action` 注册的自定义动作

**路径参数格式：**
- Django: `<int:pk>`, `<str:slug>`, `<uuid:id>` → OpenAPI `{pk}`, `{slug}`, `{id}`
- 类型转换器映射：`int` → integer, `str` → string, `uuid` → string(uuid), `slug` → string

### 视图识别

**函数视图（DRF）：**
```python
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_list(request):
    if request.method == 'GET': ...
    elif request.method == 'POST': ...
```

**类视图（DRF）：**
```python
class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['created_at']
```

**ViewSet（DRF）：**
```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):  # GET /users/me/
        ...

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):  # POST /users/{pk}/activate/
        ...
```

**DRF 泛型视图 → HTTP 方法映射：**

| 视图类 | HTTP 方法 |
|--------|-----------|
| `ListAPIView` | GET（列表） |
| `CreateAPIView` | POST |
| `RetrieveAPIView` | GET（详情） |
| `UpdateAPIView` | PUT, PATCH |
| `DestroyAPIView` | DELETE |
| `ListCreateAPIView` | GET, POST |
| `RetrieveUpdateAPIView` | GET, PUT, PATCH |
| `RetrieveUpdateDestroyAPIView` | GET, PUT, PATCH, DELETE |
| `ModelViewSet` | GET, POST, PUT, PATCH, DELETE |

### 数据模型识别

**DRF Serializer：**
```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'username': {'min_length': 3, 'max_length': 32},
            'email': {'required': True},
        }

class CreateUserSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=32, help_text='用户名')
    email = serializers.EmailField(required=True, help_text='邮箱地址')
    age = serializers.IntegerField(min_value=0, max_value=150, required=False)
    role = serializers.ChoiceField(choices=['admin', 'user', 'guest'])
```

**Serializer 字段映射：**

| DRF 字段 | OpenAPI type + format |
|----------|----------------------|
| `CharField` | string |
| `IntegerField` | integer |
| `FloatField` | number, format: float |
| `DecimalField` | number |
| `BooleanField` | boolean |
| `DateTimeField` | string, format: date-time |
| `DateField` | string, format: date |
| `EmailField` | string, format: email |
| `URLField` | string, format: uri |
| `UUIDField` | string, format: uuid |
| `FileField` / `ImageField` | string, format: binary |
| `ListField` / `ListSerializer` | array |
| `DictField` | object |
| `ChoiceField` | string, enum: [...] |
| `SlugRelatedField` | string |
| `PrimaryKeyRelatedField` | integer |

**Django Model 字段映射（当直接暴露时）：**

| Django 字段 | OpenAPI type + format |
|-------------|----------------------|
| `CharField(max_length=N)` | string, maxLength: N |
| `TextField` | string |
| `IntegerField` | integer, format: int32 |
| `BigIntegerField` | integer, format: int64 |
| `FloatField` | number, format: float |
| `DecimalField(max_digits, decimal_places)` | number |
| `BooleanField` | boolean |
| `DateTimeField` | string, format: date-time |
| `DateField` | string, format: date |
| `EmailField` | string, format: email |
| `URLField` | string, format: uri |
| `UUIDField` | string, format: uuid |
| `FileField` / `ImageField` | string, format: binary |
| `JSONField` | object |
| `ForeignKey` | integer (ID) |
| `ManyToManyField` | array of integer |

### 扫描位置

1. `urls.py` / `**/urls.py` — URL 路由配置
2. `views.py` / `**/views.py` / `**/viewsets.py` — 视图和视图集
3. `serializers.py` / `**/serializers.py` — 序列化器（数据模型）
4. `models.py` / `**/models.py` — Django 模型
5. `routers.py` — DRF 路由注册
6. `permissions.py` — 权限信息（辅助文档描述）
7. `filters.py` — 过滤器（辅助查询参数识别）

---

## FastAPI

### 路由定义模式

```python
from fastapi import FastAPI, Path, Query, Body, Header

app = FastAPI()

@app.get("/users", summary="获取用户列表", tags=["用户管理"])
async def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    keyword: str | None = Query(default=None, description="搜索关键词"),
):
    ...

@app.get("/users/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int = Path(..., gt=0, description="用户ID"),
):
    ...

@app.post("/users", summary="创建用户", status_code=201)
async def create_user(user: CreateUserRequest):
    ...

# APIRouter 子路由
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["v1"])
router.include_router(users_router, prefix="/users", tags=["用户管理"])

app.include_router(router)
```

**FastAPI 路由函数参数 → OpenAPI 参数的自动映射：**
- 路径中出现的变量名 → path 参数
- 简单类型参数（str, int, float, bool） → query 参数
- Pydantic 模型参数 → requestBody
- `Header()` 声明 → header 参数

### 数据模型识别（Pydantic）

```python
from pydantic import BaseModel, Field, EmailStr

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="用户名", examples=["john_doe"])
    email: EmailStr = Field(..., description="邮箱地址")
    age: int | None = Field(default=None, ge=0, le=150, description="年龄")
    role: Literal['admin', 'user', 'guest'] = Field(default='user', description="角色")
    tags: list[str] = Field(default_factory=list, description="标签列表")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"username": "john_doe", "email": "john@example.com"}]
        }
    )

class UserResponse(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    created_at: datetime = Field(..., description="创建时间")
```

**Pydantic Field 映射：**

| Field 参数 | OpenAPI 约束 |
|------------|-------------|
| `...`（必填标记） | required: true |
| `default=value` | required: false, default: value |
| `min_length` / `max_length` | minLength / maxLength |
| `ge` / `gt` / `le` / `lt` | minimum / exclusiveMinimum / maximum / exclusiveMaximum |
| `pattern` | pattern |
| `description` | description |
| `examples` | examples |
| `title` | title |
| `deprecated` | deprecated: true |

**Python 类型 → OpenAPI：**

| Python 类型 | OpenAPI type + format |
|-------------|----------------------|
| `str` | string |
| `int` | integer |
| `float` | number |
| `bool` | boolean |
| `datetime` | string, format: date-time |
| `date` | string, format: date |
| `EmailStr` | string, format: email |
| `HttpUrl` / `AnyUrl` | string, format: uri |
| `UUID` | string, format: uuid |
| `list[T]` | array, items: T |
| `dict[str, T]` | object, additionalProperties: T |
| `T | None` / `Optional[T]` | nullable 或 required: false |
| `Literal['a', 'b']` | string, enum: [a, b] |
| `Enum` 子类 | string/integer, enum: [...] |
| `bytes` | string, format: binary |
| `UploadFile` | string, format: binary |

### 响应声明

```python
@app.get("/users", response_model=list[UserResponse])
@app.post("/users", response_model=UserResponse, status_code=201)
@app.get("/users/{id}", responses={
    200: {"model": UserResponse, "description": "成功"},
    404: {"model": ErrorResponse, "description": "用户不存在"},
})
```

如果代码中声明了 `response_model` 或 `responses`，使用这些信息来生成响应 schema。

### 扫描位置

1. `main.py` — 应用入口和路由注册
2. `app/` — 应用目录
3. `routers/` / `routes/` / `api/` / `endpoints/` — 路由模块
4. `schemas/` / `models/` / `dto/` — Pydantic 模型
5. `dependencies.py` — 依赖注入（可能含公共参数）

---

## Flask

### 路由定义模式

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def list_users():
    ...

@app.route('/users', methods=['POST'])
def create_user():
    ...

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    ...

# Blueprint 子路由
from flask import Blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/', methods=['GET'])
def list_users():
    ...

app.register_blueprint(users_bp)
```

**Flask-RESTful：**
```python
from flask_restful import Resource, Api

class UserResource(Resource):
    def get(self, user_id):    # GET /users/<user_id>
        ...
    def put(self, user_id):    # PUT /users/<user_id>
        ...
    def delete(self, user_id): # DELETE /users/<user_id>
        ...

class UserListResource(Resource):
    def get(self):   # GET /users
        ...
    def post(self):  # POST /users
        ...

api = Api(app)
api.add_resource(UserListResource, '/users')
api.add_resource(UserResource, '/users/<int:user_id>')
```

**路径参数格式：**
- `<user_id>` → string
- `<int:user_id>` → integer
- `<float:price>` → number
- `<uuid:item_id>` → string(uuid)
- `<path:subpath>` → string

### 参数提取

```python
# 查询参数
page = request.args.get('page', 1, type=int)
keyword = request.args.get('keyword', '')

# 请求体（JSON）
data = request.get_json()

# 表单
name = request.form.get('name')
file = request.files.get('avatar')

# 请求头
token = request.headers.get('Authorization')
```

### 数据模型识别

**Marshmallow Schema（常配合 Flask 使用）：**
```python
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    email = fields.Email(required=True)
    age = fields.Int(validate=validate.Range(min=0, max=150))
    role = fields.Str(validate=validate.OneOf(['admin', 'user', 'guest']))
    created_at = fields.DateTime(dump_only=True)
```

**Marshmallow 字段映射：**

| Marshmallow 字段 | OpenAPI type + format |
|------------------|----------------------|
| `fields.Str` | string |
| `fields.Int` | integer |
| `fields.Float` | number, format: float |
| `fields.Bool` | boolean |
| `fields.DateTime` | string, format: date-time |
| `fields.Date` | string, format: date |
| `fields.Email` | string, format: email |
| `fields.URL` | string, format: uri |
| `fields.UUID` | string, format: uuid |
| `fields.List(fields.Str)` | array, items: string |
| `fields.Dict` | object |
| `fields.Nested(OtherSchema)` | $ref to OtherSchema |
| `dump_only=True` | readOnly: true |
| `load_only=True` | writeOnly: true |

**Flask-Smorest（如果使用）：**
```python
from flask_smorest import Blueprint, abort

blp = Blueprint('users', 'users', url_prefix='/users', description='用户管理')

@blp.route('/')
class UserList(MethodView):
    @blp.arguments(UserQuerySchema, location='query')
    @blp.response(200, UserSchema(many=True))
    def get(self, args):
        ...

    @blp.arguments(CreateUserSchema)
    @blp.response(201, UserSchema)
    def post(self, data):
        ...
```

Flask-Smorest 的 `@blp.arguments` 和 `@blp.response` 装饰器提供了明确的模型定义。

### 扫描位置

1. `app.py` / `main.py` / `__init__.py` — 应用入口
2. `routes/` / `views/` / `blueprints/` — 蓝图和路由
3. `resources/` — Flask-RESTful 资源
4. `schemas/` / `models/` — Marshmallow schema 和数据模型
5. `api/` — API 模块
