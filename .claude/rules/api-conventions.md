# API Conventions — Android-AutoTests

> 获取端点列表：Read 各 App 的 `urls.py`，这是唯一真相源。

## 写操作收敛原则

```
前端只能通过 Django View 写数据 → View 调用 api.py 函数写 DB
AgentScope Tool 只能通过 api.py 函数写数据 → 同进程直接调用
禁止任何组件直接 ORM INSERT/UPDATE/DELETE（只读 ORM 查询除外）
```

## 响应格式

```json
{"ok": true, "data": {...}}  // 成功
{"ok": false, "error": "..."}  // 失败
```

## 鉴权

`Authorization: Bearer <JWT>`（除 `/api/ai/auth/*` `/admin/` `/static/` 外全部需要）。所有业务视图使用 `@csrf_exempt`。

## 新增 App 注册（4 文件各 1 行）

`config/settings.py` → `config/urls.py` → `frontend/src/router.js` → `frontend/src/shared/components/AppSidebar.vue`
