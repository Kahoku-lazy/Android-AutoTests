## Why

真机验证发现 2 项：

**#1（P1）尾斜杠 401**：`GET /api/devices`（无尾斜杠）被 CommonMiddleware 301 重定向到 `/api/devices/`，部分客户端（PowerShell/curl 默认）重定向时丢弃 Authorization 头 → JWT 中间件返回 401"请先登录"。跨 App 尾斜杠约定不一致（devices 带斜杠 / runner 不带），任何非 axios 客户端都会踩。

**#2（P2）预检日志分辨率 `?x?`**：真机 Airtest `display_info` 的宽高键与引擎读取的 `displayWidth/displayHeight` 不符，日志显示 `✓ Connection verified · ?x?`（u2 info 中宽高正常）。

## What Changes

- 新增 `gateway/normalize_slash.py`：`NormalizeTrailingSlashMiddleware`——`/api/` 路径无尾斜杠且带斜杠版可 resolve 时直接重写 `path_info`（避免 301）；无斜杠版路由存在（如 `/api/runner/tasks`）则不动。挂 MIDDLEWARE 最前（CommonMiddleware 之前）
- `engines/android/airtest_u2.py::_verify_display`：display_info 缺 `displayWidth/displayHeight` 时从 u2 info 补齐（同 productName/brand/sdkInt 逻辑）
- 单测：middleware 双向规范化 + 引擎宽高补齐契约用例

## 关联文档

- 真机验证发现 #1/#2（`tests/functional/test_runner/` 脚本与 artifacts）
- Bug 修复，无需求级行为变化：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- `gateway/normalize_slash.py`（新）、`config/settings.py`（MIDDLEWARE 最前插一行）、`engines/android/airtest_u2.py`、`tests/`（middleware + 契约各一）
- 前端零改动
