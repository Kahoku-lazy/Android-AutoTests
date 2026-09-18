## Context

- `_resolve_enabled_tools`：智能体有 AITool(platform) 记录时只注入记录内名字——新增的 `sleep` 工具不在智能体 04 的历史回填记录里，17:02 构建 `tools=25` 证明其从未进入工具箱。
- 智能体 04：`system_prompt` 为空（模型无流程锚点，全靠工具描述发挥）；`max_iters=20`。
- 模型行为（msg 411 blocks）：9 次无间隔 `get_run_status` + capture_page + 重存用例 + 重跑 → 迭代耗尽；之后转向"稍后可问我"的被动话术。动机见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- sleep 工具真正进入智能体 04 工具箱（构建日志 tools=26）。
- 智能体 04 拥有执行 SOP 提示词与足够迭代预算（40），一轮对话内完成"执行→等待→报告"。
- 工具描述补"禁止连续查询"硬指引。

**Non-Goals:**

- 不改平台默认（新建智能体仍为纯对话、max_iters 默认不变）。
- 不改 ReAct 引擎、SSE 协议、前端。
- 不调整 TC-NAV-004 数据（当前 xpath=com.govee.home 已可 pass）。

## Decisions

**D1：回填复用 `migrate_platform_tools`（只补缺），不手写插记录。**
命令幂等且按"缺失名"补齐；执行后仅新增 sleep 记录，既有 26 条不动。

**D2：系统提示词写入智能体 04（而非平台默认）。**
平台"新建智能体无默认提示词"是 PRD 口径，不动；仅对当前问题智能体配置 SOP。内容要点：run_test（无需 acquire）→ sleep 10 → get_run_status 循环 ≤8 次 → get_run_results 总结；禁止连续查询/改用例/重复执行；超时报告当前状态。

**D3：max_iters 20→40 作为预算安全垫。**
SOP 流程本身约 8-12 轮，40 给足余量且不显著增加失控成本（每轮仍受工具上限约束）。

**D4：验证走真实对话端到端。**
仅静态验证无法证明模型行为；用对话 211 实际请求"执行 TC-NAV-004"，检查最终回复完整（非 ExceedMaxIters）、含 pass 结论、blocks 中使用了 sleep。

## 模块防火墙自检

- 无写库新增：回填走既有管理命令；智能体配置走 `api.update_agent`（api 层）。✅
- 无跨 App import、无通道变更。✅

## Risks / Trade-offs

- [模型仍可能不遵循 SOP（提示词是软约束）] → sleep 工具已真实注入 + 描述硬指引 + max_iters 余量，三层叠加；端到端对话验证把关。
- [max_iters 提高后失控轮询成本上升] → SOP 明确轮询上限（≤8 次），风险可控。
