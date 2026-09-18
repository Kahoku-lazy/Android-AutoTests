## Why

D0（边界与配置）两处安全开关默认 **fail-open**，且都不区分环境——本地开发与生产共用同一套宽松默认值：

| # | 位置 | 现状 | 风险 |
|---|------|------|------|
| D0-5 | `config/settings.py:58` | `ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")` | 未设环境变量即接受任意 `Host` 头（虚拟主机投毒 / 密码重置链接投毒的前置条件） |
| D0-6 | `config/settings.py:133-137` | `CORS_ALLOW_ALL_ORIGINS` 默认 `"True"`；`:138 CORS_ALLOW_CREDENTIALS = True` | 任意来源可发**携带凭据**（JWT Header / Cookie）的跨域请求；代码注释自己写着「生产环境应设为 False」而默认值相反 |

附带事实（本就存在，不是猜测）：

- `CORS_ALLOWED_ORIGINS` 在代码中**从未接线**（全仓 0 命中），即生产即使显式设 `CORS_ALLOW_ALL_ORIGINS=False`，也没有任何来源被放行、且没有白名单入口——当前默认值实际是「要么全放开，要么全封死」。
- `.env.example`（**已跟踪**）仍列着上一个变更删除的 `SCREENSHOT_INTERVAL=0.5`（:12）与 `AGENTSCOPE_PORT=8000`（:29）；两键全仓代码**零消费**（`grep` 已核，`.env.example` 自身除外），属 `2026-09-14-remove-dead-d0-config` 的收尾遗漏。

## What Changes

1. `ALLOWED_HOSTS` 默认值按 `DEBUG` 分档：`DEBUG=True` → `*`（本地起服务免配置）；`DEBUG=False` → `127.0.0.1,localhost`。**显式 `DJANGO_ALLOWED_HOSTS` 仍然优先。**
2. `CORS_ALLOW_ALL_ORIGINS` 默认值按 `DEBUG` 分档：`DEBUG=True` → `True`；`DEBUG=False` → `False`。**显式环境变量仍然优先**（生产需要放开的场景有逃生门）。
3. 接线 `CORS_ALLOWED_ORIGINS`（逗号分隔，默认空）：关闭 allow-all 后可按来源白名单放行。
4. `.env.example`：补 `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` 两个新开关说明；删除 `SCREENSHOT_INTERVAL`、`AGENTSCOPE_PORT` 两行死键。
5. `ARCH-00` §七「关键开关（环境变量）」同步：补上述三项及其 DEBUG 分档默认值。
6. **BREAKING（部署侧）**：若某环境以 `DEBUG=False` 运行且**未设** `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS`、却依赖旧的宽松默认值，升级后请求会被拒绝。迁移方式：显式设 `DJANGO_ALLOWED_HOSTS=<域名/IP 列表>`、`CORS_ALLOWED_ORIGINS=<前端来源列表>`（或显式 `CORS_ALLOW_ALL_ORIGINS=True`）。仓库内 `.env` 为 `DJANGO_DEBUG=True`，**本地开发行为不变**。

## 关联文档

- 依据：本会话 D0 层代码检测（问题项 D0-5 / D0-6）
- `dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html`（D0 层定义：只做进程装配 / 路由总表 / 外部资源根 / 插槽开关）
- `config/settings.py` · `.env.example`（已跟踪模板）· `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七
- 前序变更：`openspec/changes/archive/2026-09-14-remove-dead-d0-config/`（本次收尾其 `.env.example` 遗漏）
- 范围外登记（本次不修）：D0-7~13（`CSRF_TRUSTED_ORIGINS` 缺失、`config/api_docs.py` 三份真相源等）· `CORS_ALLOW_CREDENTIALS` 保持 `True`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；`openspec/specs/` 下无「配置 / 安全默认值」类能力可改，`.openspec.yaml` 已声明 `skip_specs: true`，不变量以 design.md「Decisions」+ ARCH-00 §七 承载）

## Impact

- **修改**：`config/settings.py`（`ALLOWED_HOSTS` 1 行 → 2 行；CORS 块 +白名单接线）· `.env.example`（+2 键说明 / −2 死键）· `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七
- **不影响**：`apps/` · `engines/` · `gateway/` · `frontend/` · API 契约 · 路由 · DB · `openspec/specs/`
- **部署侧**：见 What Changes #6（需显式配置环境变量）
- **测试范围**：`python manage.py check` · 生产档位断言（`DJANGO_DEBUG=False` 下默认值与显式覆盖）· `pytest -m "unit or integration"` · `ruff check config/` · `openspec validate --strict`
