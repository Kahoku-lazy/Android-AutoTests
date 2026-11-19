# Design: fix-agentscope-usage-defects

## Context

动机见 proposal.md - Why。现状约束：

- 本机 agentscope 2.0.9。官方 `ChatModelBase.__call__` 对 provider 声明的瞬态异常重试 `max_retries+1` 次（三家模型构造默认 `max_retries=3`），不包流式迭代中段；`FunctionTool.permission` 只收 `PermissionDecision` 实例，`check_permissions()` 原样返回；`ChatModelBase.generate_structured_output` 内置 `forced → auto → no_think → none` 策略阶梯，`no_think` 档取 `_get_disable_thinking_kwargs()`（OpenAIChatModel 未覆写，DeepSeek 覆写返回 `extra_body.thinking.type=disabled`）。
- 仓库红线：`create_agent` 唯一出口且签名不加能力型参数；中间件三类准入不变；event/ 不引用具体工具名、不读配置；不新增自定义异常；不动计费与 token 口径。
- SOP 交付/验收走 `reply_stream(structured_schema=...)` + 内置 `GenerateStructuredOutput` 工具，**是否被策略阶梯覆盖未实测**——govee 兜底因此保留。

## Goals / Non-Goals

**Goals:**

- 消除写工具权限检查返回非法类型的缺陷。
- 重试分层：模型层默认 1 次重试可配置，中间件规则不变，最坏 12→6。
- govee 关思考参数接入官方扩展点，兜底不删。
- SOP 角色归属按名字映射，尝试序号取自官方事件；无映射向后兼容。

**Non-Goals:**

- 不改取消机制（CR-1 未获批）、不暴露 create_agent 配置对象（CR-2 未获批）。
- 不删 govee `_call_api` 兜底（待真网关实测后另行决策）。
- 不清理 `agent-model-resilience` 主规格里描述已退役实现的存量需求（回退备用模型 / 重试事件流），另行立项。
- 不动渲染器视觉、用量口径、StepRecord 既有字段语义。

## Decisions

1. **权限修复传实例而非改框架用法**：`_ALLOW` 由 lambda 改为 `PermissionDecision(behavior=ALLOW, message=...)` 模块级常量，与 adb 域完全同款。备选「覆写 check_permissions 的 ToolBase 子类」被否：FunctionTool 静态决策已满足需求，子类化徒增复杂度。
2. **重试单层化选 A（模型层调低 + 中间件保留）**：`create_model(..., max_retries: int = 1)` 关键字参数透传三家构造器；`create_agent` 签名不变（吃默认 1）。备选 B（删中间件调用错误重试）被否：会失去错误细分类与抖动，且中间件流式兜底是官方缺口。默认 1 而非 0：保留一次模型层快速重试吸收瞬时抖动，最坏 2×3=6 已有界。
3. **govee 只加扩展点覆写**：`_get_disable_thinking_kwargs()` 返回 `{"extra_body": {"thinking": {"type": "disabled"}}}`，与官方 DeepSeek 实现逐字一致。`_call_api` 三段兜底原样保留——SOP 路径覆盖未实测前删除违反「禁止带着不确定性行动」。
4. **SOP 角色归属：名字映射优先、顺序推断兜底**：recorder 新增可选 `sop_roles: dict[str, str] | None`（与 `role_api_keys` 同款「调用方传入绑定」模式，不违反 event/ 零配置依赖）；`run_sop` 用 `getattr(executor, "name", "")` / verifier 同名构造映射传入。`SOP_STEP_STARTED` 的 `value.attempt` 存入 `_sop_attempt`，`StepRecord` 新增 `sop_attempt: int = 0`（带默认值，渲染器与既有构造点零改动）。备选「完全删除顺序推断」被否：未传映射的调用方（含既有测试）行为会回归。
5. **提交拆分**：四个修复各自独立提交（Conventional Commits，逐文件暂存），同一 OpenSpec 变更下四个任务组；任一修复可独立 revert。

## 模块防火墙自检

- 跨 App import：本变更全部落在 `engines/`，不新增任何 `apps.*` / `django.*` import；backend 零改动。
- 依赖方向：`backend_bridge → ae_harness` 不变；`run_sop`（workflow/sop）向 recorder（event）传映射，属既有依赖边（runner 已 import event），无新增跨包边。
- event/ 红线：不引用具体工具名（映射键是 agent 名，由调用方传入）；不读配置、不 import agents；用量按 reply_id 反查角色密钥的口径不变。
- agents/ 红线：`create_agent` 签名与唯一出口不变；`create_model` 新增关键字参数属模型配置面，非角色第四要素；不新增第二配置来源。
- 异常：不新增自定义异常类；权限修复不改异常面。
- 钱与配额：计费规则、token 统计口径、预算默认值零改动；重试次数变化只影响失败路径调用次数，不改计费口径。
- AGENTS 文档：仅更新 `workflow/AGENTS.md`「已知限制 2」的事实描述（非红线/禁止/准入/依赖条款），不触「改规则必须先请示」。

## Risks / Trade-offs

- [模型层默认重试 3→1 改变失败路径时延特征] → 中间件退避兜底仍在；最坏次数下降是收益；成功路径零变化，单测覆盖默认值与显式配置。
- [govee 扩展点使策略阶梯 no_think 档生效，可能改变 generate_structured_output 路径行为] → 该路径此前对 govee 跳过 no_think；新增档位只在 forced/auto 失败后进入，属官方设计的兜底顺序；既有 govee 单测全量回归。
- [StepRecord 新字段影响下游序列化消费方] → 字段带默认值 0，JSONL 多一个键属 additive；渲染器不读该键，报告视觉不变。
- [名字映射依赖 agent.name 与 ReplyStartEvent.name 一致] → 两者同源于 Agent 构造的 name 字段（既有 role_api_keys 已按此口径工作）；映射缺失时兜底顺序推断，不会更差。
- [SOP 模块官方标实验性] → 本变更只消费其公开事件与 state 字段，升级复核清单沿用 workflow/AGENTS 已知限制 3。

## Migration Plan

纯代码修复，无数据迁移。部署即生效；回退按提交粒度 revert 任一修复即可，四个提交互不依赖（SOP 映射与尝试序号同属一个提交）。