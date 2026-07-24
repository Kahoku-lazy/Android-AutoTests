# Backend Rules — Android-AutoTests

## 技术栈

Django + Daphne + Django Channels + Django ORM

## Django App 结构约定

每个业务模块的 App 遵循统一结构：

```
apps/{app_name}/
├── models.py     # ORM Model 定义（表结构）
├── views.py      # HTTP 请求入口（解析 JSON → 逻辑 → 返回 JsonResponse）
├── api.py        # 可被跨模块调用的公共写操作函数（__all__ 白名单）
├── urls.py       # URL 路由（app_name + urlpatterns）
├── consumers.py  # WebSocket Consumer（如有）
└── service.py    # 内部业务逻辑（不影响跨模块边界，可省略）
```

## 文件职责分工

### models.py — 只定义表结构

```python
class Device(models.Model):
    serial = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='ONLINE')

    class Meta:
        db_table = 'dp_devices'  # 必须显式指定表名
        indexes = [models.Index(fields=['status'])]
```

- 表名必须带正确前缀（`grep -rn "db_table" apps/*/models.py` 查看当前所有前缀）
- 外键使用 CASCADE 或 SET_NULL，不删除关联数据用 SET_NULL
- JSON 字段优先用 `models.JSONField`

### views.py — HTTP 入口

```python
@csrf_exempt  # JWT 鉴权替代 CSRF
def list_devices(request):
    user_id = getattr(request, 'user_id', None)  # 由中间件注入
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': '无效的 JSON'}, status=400)

    # 业务逻辑...
    return JsonResponse({'ok': True, 'data': devices})
```

**编写规范**：
- 所有 view 用 `@csrf_exempt` 装饰器
- 从 `request.body` 解析 JSON，失败返回 400
- 通过 `request.user_id` 获取当前用户（中间件注入）
- 始终返回 `JsonResponse({'ok': True/False, ...})`
- 错误必须带 HTTP 状态码：400/401/403/404/409/500

### api.py — 跨模块写操作

```python
# __all__ 控制白名单
__all__ = ['acquire_device', 'release_device', 'join_device_queue']

def acquire_device(serial, user_id, timeout=300):
    """锁定设备。由 views.py 或 AgentScope Tool 调用。"""
    device = Device.objects.get(serial=serial)
    # 确保状态合法，创建锁记录...
    return lock_record
```

**编写规范**：
- 文件头 `__all__` 显式声明导出函数白名单
- 函数接收简单参数（字符串/数字/字典），不接收 `request` 对象
- 查询函数返回 `dict` 或 `list[dict]`，不返回 ORM 对象（防止跨模块 Model 依赖）
- 写操作可能 `raise ValueError`，调用方需自行 try/except
- 内部做完整的参数校验和状态检查
- 不返回 JsonResponse（那是 views.py 的职责）
- AgentScope Tool 和 views.py 都通过 api.py 写入 DB

### urls.py — 路由注册

```python
app_name = 'devices'

urlpatterns = [
    path('', list_devices, name='list'),
    path('<str:serial>/lock', lock_device, name='lock'),
]
```

- `app_name` 必须与 URL 前缀一致
- 命名使用 snake_case
- 避免通配符路由在具体路由之前

## 中间件和鉴权流程

```
请求 → JWTAuthenticationMiddleware
     → 检查 URL 是否在公开路径列表
     → 公开路径：直接放行
     → 需鉴权：从 Authorization header 提取 Bearer token
              → JWT 验证（共享 SECRET_KEY）
              → 注入 request.user_id
              → 放行
```

**公开路径**：`/api/ai/auth/*` `/admin/` `/static/`
**开发模式**：无 token 也放行（`request.user_id = None`）

## 配置约定

| 配置项 | 文件 | 说明 |
|--------|------|------|
| INSTALLED_APPS | `config/settings.py` | 新增 App 在此注册；jazzmin 在 admin 前 |
| 数据库引擎 | `config/settings.py` | `DB_ENGINE` 环境变量切换 sqlite/mysql |
| CORS | `config/settings.py` | 开发环境 `CORS_ALLOW_ALL_ORIGINS = True` |
| 时区 | `config/settings.py` | `LANGUAGE_CODE='zh-hans'` `TIME_ZONE='Asia/Shanghai'` `USE_TZ=False` |
| URL 分发 | `config/urls.py` | `include('apps.{name}.urls')` |
| ASGI 入口 | `config/asgi.py` | HTTP → URLRouter, WS → 中央路由 |
| WS 中央路由 | `gateway/routing.py` | 所有 WebSocket consumer 在此注册 |

> 注意：Token 黑名单当前使用内存 `set()`，生产环境应迁移到 Redis。

## 错误处理模式

```python
# 资源不存在 → 404
if not device:
    return JsonResponse({'ok': False, 'error': 'not found'}, status=404)

# 状态冲突 → 409
if device.status != 'ONLINE':
    return JsonResponse({'ok': False, 'error': '设备不可用'}, status=409)

# 外部服务不可用 → 502/503
except ConnectionError:
    return JsonResponse({'ok': False, 'error': '设备连接失败'}, status=502)
```

## 异步处理

- 同步视图：默认模式，Daphne 工作线程中执行（uiautomator2 阻塞调用适用）
- async 视图：仅 `POST /api/runner/run` 用 `async def`，`asyncio.create_task()` 后台执行测试
- AgentScope 桥接：`db_helper.run_sync()` 封装 `sync_to_async`，8s 超时
