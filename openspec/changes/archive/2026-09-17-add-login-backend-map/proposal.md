## Why

登录模块的后端没有任何可视化梳理：它的设计事实分散在 `config/urls.py`、`gateway/*`、`shared/auth/*`、`apps/accounts/*`，且有若干条**只有实测才能发现**的事实（登出后 refresh 仍可换新 access；DRF 请求被校验两次且重复查同一行 `auth_user`；写口 `api.create_user` 无重名兜底）。

本变更以 **运行时内省 + 真实请求实测** 产出一份自包含 HTML，按后端自身的分层梳理：
**模型层 / 模板层 / 视图层** 三层为骨架，另加**横切面**（信任与运行）。图里每一个状态码、每一句文案、
每一次调用计数与 SQL 次数都是**跑出来的**，不是读代码推的。

## What Changes

- 新增 `temps/login-backend-map/` bundle：
  - `collect_backend_facts.py` —— 在 pytest（`config.test_settings`，事务回滚，不碰真实库）里做两遍采集：
    ① **静态内省**（路由表 / DRF 范式 / 中间件链 / `PUBLIC_PREFIXES` / `api.py` `__all__` / 表归属 /
    序列化器字段与校验文案 / 契约层证据）；② **真实请求实测**（无令牌、有效令牌、登出后 access、
    登出后 refresh、重名注册、校验次数与 SQL 次数）
  - `login-backend-map.cjs` —— 单入口编排：调采集 → 渲染 → 写自包含 HTML → 内嵌源码指纹；`--check` 秒级判过期（**不跑采集**）
  - `login-backend-map.template.html` —— 七节版式
  - `verify-backend-map.cjs` —— 自检器
  - `README.md` —— 同步规则
- 七节内容：**A** 分层总览（模型/模板/视图 + 横切）· **B** 模型层（数据面与写面）·
  **C** 模板层（校验器 + 信封 + OpenAPI 形状，含「Django 模板渲染在本工程为空」的实测证据）·
  **D** 视图层（路由 + 视图 + 权限 + 错误码映射 + 请求流水线）· **E** 端点实测卡 ·
  **F** 横切面（信任：闸门/TTL/黑名单/会话时间轴断点；运行：配置与日志）· **G** 图例索引

**Non-goals**：
- **不做全后端**（实测 275 条 API 路由）——仅登录模块：`/api/auth/*` 5 个端点及其模型/模板/视图/横切面
- **不做前端关联**：不把页面元素与后端功能做 join（前一版曾尝试，已按用户要求移除）
- 不修改任何生产代码、不新增依赖、不动 API 契约
- 不把 bundle 移出 `temps/`
- 不自动修正手写的 `file:line`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯工具与产物：`.openspec.yaml` 已设 `skip_specs: true`。不改变任何运行时行为。

## 关联文档

- `dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md` §1.3 分层 / §1.4 四条通信通道 / §1.5 统一机制 —— 本产物对 §1.5「范式分布」表做实测对账
- `apps/AGENTS.md`（分层与模块边界、契约规则）、`tests/AGENTS.md`（测试口径）

## Impact

- 工具与产物：`temps/login-backend-map/`（新建，全部位于 gitignore 的 `temps/`）
- 生产代码 / 后端 / API / 依赖 / 数据库：**无**
- 验证范围：采集可复现；`--check` exit 0；`verify-backend-map.cjs` 无 errs；HTML 可离线打开（除字体）
