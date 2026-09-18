## Why

`gateway/normalize_slash.py` 只为**一个方向**兜底：无斜杠请求若「带斜杠版路由存在」则补斜杠
（避免 `CommonMiddleware` 的 301 丢 `Authorization` 头）。反方向无人处理 ——
带斜杠请求遇到无斜杠路由，直接 **404**。

而本平台的路径约定**并不统一**：各 App 之间不一致，同一 App 内也混用。

```
accounts             login | register | refresh        ← 无斜杠
dashboard            dashboard/stats/                  ← 带斜杠
element_locator      move/ | files/batch-delete/ | pages   ← 同 App 内混用
```

实测基线（带真实令牌，避免 JWT 中间件先于路由解析返回 401 的干扰）：

| 请求 | 结果 |
|---|---|
| `POST /api/auth/login` | 400（已解析） |
| `POST /api/auth/login/` | **404（未解析）** |
| `GET /api/dashboard/stats` | 200 ← 中间件补斜杠，反方向有效 |
| `GET /api/auth/me/` | **404（未解析）** |
| `/api/no-such-route` / `/api/no-such-route/` | 404 / 404（正确） |

调用方多打一个 `/` 就得到 404，且**平台自身无法给出统一写法**（约定因 App 而异）。
该中间件此前**没有任何测试**。

## What Changes

- `gateway/normalize_slash.py`：补上反方向 —— 带斜杠请求若「无斜杠版路由存在」则去斜杠
- **改写只在原路径无法解析时发生**：若路径本身可解析（例如同一资源同时注册了两种写法，
  `element_locator` 的 `batch-move` 与 `batch-move/` 即如此），一律不改写，按原路径命中
- 抽出 `_resolves()` 辅助函数，使「先判能否解析、再决定是否改写」的意图直白
- 新增 `tests/graybox/unit/test_trailing_slash_tolerance.py`（该中间件此前零覆盖）

**Non-goals**：
- **不统一各 App 的路径约定**：那会改 API 契约、OpenAPI schema、接口文档与前端调用点，属独立变更
- 不改 `CommonMiddleware` 的 `APPEND_SLASH` 行为
- 不改 `request.path`（仅改写 `path_info`，与既有实现一致；鉴权白名单按前缀匹配，两种写法均命中）

## Capabilities

### New Capabilities

- `api-path-normalization`：`/api/` 前缀请求的尾斜杠双向容错（补/去斜杠、原路径可解析时不改写、非 `/api/` 前缀不受影响）

### Modified Capabilities

（无）

## Impact

- 后端：`gateway/normalize_slash.py`
- 前端 / API 契约 / 依赖 / 数据库：**无**（不改任何路径定义）
- 行为变化：`/api/**/xxx/` 形式的请求从 404 变为命中（当 `xxx` 存在时）
- 测试：新增 `tests/graybox/unit/test_trailing_slash_tolerance.py`
- 证据产物：`temps/login-backend-map/` 需重跑（D 节尾斜杠实测由 404 变为命中）
