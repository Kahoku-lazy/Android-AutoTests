## Context

三个函数均为纯通用逻辑（无 App 内部状态）：resolve_username=User 查询、require_auth=user_id 检查、filter_agents_for_user=queryset 过滤。平移不改函数体；原处 re-export 保 App 内兼容；dashboard/evaluator 改走合法通道（shared / api.py）。

## Goals / Non-Goals

**Goals:**

- 三处跨 App 内部 import 清零（grep 验证）
- 行为等价（pytest 全绿）

**Non-Goals:**

- 不去重 test_runner 自己的 require_auth（登记）
- 不动 gateway 中间件

## Decisions

- **filter_agents_for_user 归属**：`apps/ai_assistant/api.py`（跨 App 合法通道，读助手进 `__all__`）；不放 shared（AI 所有权语义属领域）
- **require_auth 归属**：`shared/auth/`（通用鉴权，与 jwt_auth/drf_auth 并列）；ai_assistant.decorators 保留 re-export
- **resolve_username 归属**：`shared/users.py`（通用能力；test_runner 的 resolve_creator 语义相近，登记为后续去重）

## 模块防火墙自检

- 收敛后：dashboard/evaluator 只 import shared.* 与对方 api.py（合法通道）
- 无 ORM 写变化；通过

## Risks / Trade-offs

- [re-export 期被误当跨 App 通道] → 与 algorithms re-export 同策略：只保 App 内兼容
- [循环 import] → 已核实 api.py 不 import permissions，无环
