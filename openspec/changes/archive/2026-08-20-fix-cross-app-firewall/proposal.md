## Why

防火墙三处违规（ARCH-00 标注 TD-03，总纲 §六 6.2 承诺修复，七步序列未覆盖）：`dashboard→ai_assistant.permissions.filter_agents_for_user`、`dashboard→case_manager.views_helpers.resolve_username`、`evaluator→ai_assistant.decorators.require_auth`——跨 App import 内部实现，其中 require_auth 与 gateway 中间件鉴权职责重叠。修复后 `--check-boundaries` 与 import 扫描双重转绿。

## What Changes

- 新增 `shared/users.py`：`resolve_username(user_id)`（自 case_manager/views_helpers 平移，纯 User 查询通用能力）
- 新增 `shared/auth/require_auth.py`：`require_auth` 装饰器（自 ai_assistant/decorators 平移，sync/async 双支持，与 gateway 中间件同语义）
- `apps/case_manager/views_helpers.py`：改 re-export（App 内 7 个消费文件零改动）
- `apps/ai_assistant/decorators.py`：改 re-export（App 内 chat_views 零改动）
- `apps/ai_assistant/api.py`：新增 `filter_agents_for_user`（读助手，进 `__all__`）；`permissions.py` 改 re-export（views_drf 零改动）
- `apps/dashboard/views.py`：改 `from shared.users import resolve_username`、`from apps.ai_assistant.api import filter_agents_for_user`
- `apps/evaluator/views.py`：改 `from shared.auth.require_auth import require_auth`
- 范围外登记：`test_runner/views/helpers.py` 自有的 `require_auth`（第 60 行）为同义重复，不在本变更（另立去重项）

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-目标架构-设备交互协议与引擎分层.md`（§六 6.2 防火墙修复）
- 落地实测：`设计-现状架构-重构落地实测.md`（差距 #8）
- 纯重构（函数平移 + re-export，行为等价）：`.openspec.yaml` 已设 `skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- 新增：`shared/users.py`、`shared/auth/require_auth.py`
- 修改：`apps/case_manager/views_helpers.py`、`apps/ai_assistant/{decorators,api,permissions}.py`、`apps/dashboard/views.py`、`apps/evaluator/views.py`
- 行为零变化；前端/数据库零改动
