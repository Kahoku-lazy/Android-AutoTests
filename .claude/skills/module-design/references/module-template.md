# Module Template — 新建模块参考模板

## 后端 App 新建 4 步

### 1. 创建目录 + 文件

```bash
mkdir -p apps/{app_name}/migrations
touch apps/{app_name}/__init__.py
touch apps/{app_name}/migrations/__init__.py
```

### 2. models.py 模板

```python
""" {AppName} ORM models — {prefix}_ prefix tables."""
from django.db import models


class MyModel(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '{prefix}_my_model'
        indexes = [
            models.Index(fields=['name']),
        ]
```

### 3. api.py 模板

```python
""" {AppName} API — 跨模块调用的公共接口。"""
__all__ = [
    "get_xxx",
    "create_xxx",
    "delete_xxx",
]


def get_xxx(id: int):
    from .models import MyModel
    try:
        return MyModel.objects.get(id=id)
    except MyModel.DoesNotExist:
        return None


def create_xxx(**kwargs):
    from .models import MyModel
    return MyModel.objects.create(**kwargs)
```

### 4. views.py 模板

```python
""" {AppName} API endpoints."""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .api import get_xxx
from .serializers import validate_xxx_input
from .permissions import check_can_access


@csrf_exempt
def list_items(request):
    user_id = getattr(request, 'user_id', None)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    # ...
    return JsonResponse({'ok': True, 'data': items})
```

### 5. 注册 4 处

| 文件 | 操作 |
|------|------|
| `config/settings.py` | INSTALLED_APPS 加 `'apps.{app_name}'` |
| `config/urls.py` | 加 `path('api/{prefix}/', include(...))` |
| `frontend/src/router.js` | 加模块路由汇总 |
| `frontend/src/shared/components/AppSidebar.vue` | 加导航菜单项 |

## 前端模块新建 3 步

### 1. 创建目录

```bash
mkdir -p frontend/src/modules/{module-name}/components
```

### 2. api.js 模板

```js
import client from '@/shared/api-client.js'

export function listItems() {
  return client.get('/{prefix}/')
}

export function createItem(body) {
  return client.post('/{prefix}/', body)
}

export function deleteItem(id) {
  return client.delete(`/{prefix}/${id}`)
}
```

### 3. routes.js 模板

```js
export default [
  { path: '/{module-name}', name: 'ModuleName', component: () => import('./index.vue') },
]
```

### 4. 注册 1 处

| 文件 | 操作 |
|------|------|
| `frontend/src/router.js` | `import xxx from './modules/{module-name}/routes.js'` → `routes.push(...xxx)` |
