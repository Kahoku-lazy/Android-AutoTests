# Proposal: fix-agentscope-usage-defects

## Why

AgentScope 2.0.9 用法审计（2026-11-19，只读）确认：仓库存在 1 个实测缺陷（两个工具域把 lambda 传给 `FunctionTool(permission=...)`，权限检查返回函数对象而非 `PermissionDecision`，写工具接真模型即触发）、1 处重试叠加（模型层内置默认 4 次尝试 × 自研中间件 3 次，最坏 12 次调用）、1 处私有 API 补丁可换官方扩展点（openai 关思考）、1 处报告角色归属靠 reply 顺序奇偶推断（脆弱）。需求方已确认本批只修这 4 项，功能级改造全部暂缓。

## What Changes

- **P0 权限缺陷修复**：`tools/document/tools.py` 与 `tools/case_library/tools.py` 的 `permission=` 由 lambda 改传 `PermissionDecision` 实例（对齐 adb 域既有正确写法）；补「写工具权限检查返回类型与放行行为」单测。
- **重试单层化（方案 A）**：`agents/models.py` 的 `create_model` 新增可选关键字参数 `max_retries`，默认 **1**（原框架默认 3），透传给三家模型构造器；自研 `ModelRetryMiddleware` 保持不变（保留错误分类、指数退避抖动、流式首块前兜底）。最坏尝试次数由 12 降为 6。`create_agent` 签名不变。
- **openai 官方扩展点**：`OpenAIGatewayChatModel` 增加 `_get_disable_thinking_kwargs()` 覆写（返回 `extra_body.thinking.type=disabled`，与官方 DeepSeek 实现同款），使框架结构化输出策略阶梯的 `no_think` 档对 openai 生效；现有 `_call_api` 重发兜底**保留不删**（SOP 交付路径是否被阶梯覆盖需真网关实测，未实测前不删）。
- **SOP 角色归属去顺序推断**：`AgentEventRecorder` 新增可选入参 `sop_roles`（agent 名 → executor/verifier 映射），`ReplyStartEvent` 优先按映射归属角色；未提供映射时沿用既有奇偶推断（向后兼容）。消费 `SOP_STEP_STARTED` 的 `attempt` 字段记录尝试序号并写入 `StepRecord.sop_attempt`；`run_sop` 装配时传入两角色名字映射。
- 不做：取消机制改官方 `task.cancel()`（CR-1 未获批）、`create_agent` 暴露配置对象/timezone（CR-2 未获批）、官方预算中间件/备用模型/RAGMiddleware 准入（CR-3 暂缓）、GoalPipeline 生产接线/会话持久化/向量库切换（需求方明确暂缓）。

## 关联文档

无关联 PRD 编号：本变更为审计驱动的缺陷修复与可靠性收敛，不引入新需求。审计依据为 2026-11-19 的 AgentScope 用法盘点报告（dev_docs/DEV_TEST 下），官方口径钉在 agentscope 2.0.9 文档站。

## Capabilities

### New Capabilities

- `harness-tool-permission`: 域门面产出的函数工具在无人值守运行下的权限放行契约——工具必须携带有效的静态放行决策，权限检查必须返回 `PermissionDecision`，写工具不得落入「询问用户」兜底。

### Modified Capabilities

- `agent-model-resilience`: 新增「模型层内置重试与中间件重试分层」需求：模型层 `max_retries` 默认 1 且可经 `create_model` 显式配置；中间件重试规则不变。（既有「回退备用模型」「重试与回退写入任务事件流」两条需求描述的是已退役实现，与现行 ae_harness 代码不符，属存量欠账，本变更不改动、不清理，另行立项。）
- `openai-thinking-tool-choice`: 新增「关思考参数经官方扩展点声明」需求：openai 通道必须向框架结构化输出策略阶梯提供关思考参数；既有重发规则全部不变。
- `ae-harness-event-full-record`: 新增「SOP 角色归属按名字映射」需求：提供映射时角色归属必须按 agent 名判定，不得依赖 reply 顺序；步骤尝试序号必须取自官方 `SOP_STEP_STARTED` 事件并落进工具记录。

## Impact

- 代码：`engines/ae_harness/tools/document/tools.py`、`tools/case_library/tools.py`、`agents/models.py`、`event/record.py`、`workflow/sop/runner.py`；`engines/ae_harness/workflow/AGENTS.md` 的「已知限制 2」随实现更新（非红线条款）。
- 测试：新增/更新 `tests/engines/ae_harness/unit/` 与 `tests/engines/backend_bridge/unit/` 相关用例（权限返回类型、max_retries 透传、openai 扩展点、SOP 角色映射与尝试序号）。
- 行为面：瞬时故障最坏调用次数 12→6；写工具权限检查由「返回函数对象（潜在报错）」变为「静态放行」；SOP 报告角色归属在重试/无验收者等场景下不再错配。成功路径调用次数与参数不变。
- 不动：计费规则、token 统计口径、预算默认值、取消异常口径、依赖方向、任何 AGENTS 红线条款。
- 风险：openai 扩展点仅影响 `generate_structured_output` 阶梯路径，SOP 交付路径覆盖情况未实测——兜底保留，零回归风险；`StepRecord` 新增带默认值字段，渲染器与既有测试不受影响。