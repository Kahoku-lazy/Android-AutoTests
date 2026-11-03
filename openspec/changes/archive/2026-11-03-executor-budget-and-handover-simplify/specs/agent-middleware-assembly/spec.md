## MODIFIED Requirements

### Requirement: 中间件统一装配入口

引擎 SHALL 通过单一入口为每个角色装配中间件，并按固定顺序挂载：链路追踪在最外层，其后依次为 RAG 上下文、语音合成，模型重试与回退在最内层。每个能力 MUST 由独立开关控制；开关未开启时 MUST NOT 出现在装配结果里。装配入口 MUST NOT 抛错阻断角色创建：某个能力配置非法时 MUST 记一条警告并跳过该能力。装配结果里 MUST NOT 包含按 token 量禁用工具或注入收尾提示的中间件；角色单次答复的收敛 MUST 只由轮次上限决定。

#### Scenario: 默认只装重试

- **WHEN** 只保留默认环境变量创建角色
- **THEN** 装配结果里只有模型重试中间件，没有追踪、RAG、语音与记忆

#### Scenario: 顺序固定

- **WHEN** 同时开启追踪、RAG、语音与重试
- **THEN** 装配顺序为「追踪 → RAG → 语音 → 重试」

#### Scenario: 单项配置非法不影响创建

- **WHEN** 某个能力的配置无法解析（例如语音开关写成非数字）
- **THEN** 角色照常创建，被跳过的那项留下一条警告

#### Scenario: 不再装配 token 预算

- **WHEN** 环境里仍残留旧的 token 预算变量（`AGENT_REPLY_TOKEN_BUDGET` 等）并创建角色
- **THEN** 装配结果里没有任何按 token 量干预工具选择的中间件，该变量不产生影响

## REMOVED Requirements

### Requirement: 单次回复的 token 预算

**Reason**: 该护栏在设备操作场景下会与 SOP 的交卷契约互斥。执行者每轮都携带截图，单轮输入 45k–90k token，600,000 加权上限在第 7–14 轮即被耗尽；耗尽后中间件把工具选择强制为「不调用工具」，而该步仍要求用 `GenerateStructuredOutput` 交卷，模型只能把工具调用写进正文，交卷永远无法完成，空转直到轮次上限。2026-11-03 TASK-177 三次尝试因此烧掉约 801 万加权 token（占全任务 73%）仍判失败。

**Migration**: 删除 `engines/agents/middleware/budget.py`、装配入口中的预算项与包导出；单步收敛改由 ReAct 轮次上限承担（执行者 `max_iters=60`，另有 5 轮结构化输出宽限），任务级兜底仍由 `SOP_MAX_MODEL_CALLS`（默认 600 次）与 `SOP_MAX_RUN_SECONDS`（默认 7200 秒）承担。`AGENT_REPLY_TOKEN_BUDGET` / `AGENT_REPLY_INPUT_WEIGHT` / `AGENT_REPLY_OUTPUT_WEIGHT` 三个环境变量退役：继续配置不会报错，但不再产生任何效果；`.env.example` 中的对应说明同步删除。需要按成本收紧的上限，改为调整执行者角色的 `max_iters`。
