## Why

`ae_harness` 的模型支出目前只能看到一个汇总数字：`summary.tokens` 只有输入 / 输出 / 缓存三项，既没有「这次用的是哪把密钥」，也没有逐次明细与绝对时间。而平台既有的 `model-usage-ledger` 要求每条用量都带来源标识与时间，ae_harness 侧一条都产不出来。

根源是一处信息丢失：`create_model` 在内部已经解析出密钥环境变量名（`ChatModel.api_key`），但只重建了模型实例就把它丢掉。于是下游没有任何标签可以把「这次花的 token」归到「这把密钥」上。

## What Changes

- **BREAKING** 模型创建出口交出模型时顺带交出密钥环境变量名：`create_model` 的返回值由「模型实例」改为「模型实例 + `api_key_env`」两段。只有 `create_agent` 一个调用方。
- **BREAKING** 角色创建出口的返回值由 `Agent` 改为两段：`.agent` 是可运行智能体，`.api_key_env` 是本次用的密钥环境变量名。4 个既有调用点改为解包。
- 新增 `engines/ae_harness/event/usage.py`：`TokenUsage`（一次模型调用一条：密钥环境变量名 + 轮次 + 起止时刻 + 四类 token）与按 `api_key_env` 归组的汇总函数。
- 事件记录器接收密钥环境变量名（`str`，默认空）；`RunRecord` 增加 `usages` 与 `api_key_env` 两个字段。
- JSONL 的 `summary` 行补写 `api_key_env`。
- `engines/backend_bridge/token_usage/` 本期保持空目录：本变更只做采集与产出，不实现上报。

**不记录的东西**（刻意）：`provider`、`base_url`、配置短名、正式模型名。它们能区分「官方直连 vs 第三方网关」，但记账只需要「哪把密钥」，多记四项就多四处要维护的字段。

## 关联文档

- 需求来源：需求方直接决策——token 采集只允许在 `engines/ae_harness/event/` 内实现；记账标签只用密钥环境变量名，由模型创建出口顺带返回。
- 受影响主 spec：新建 `ae-harness-token-usage`。
- 口径对齐（本变更不修改其需求）：`model-usage-ledger`（`occurred_at` / 三类 token 的字段语义）、`agent-reply-usage`（一次模型调用一组用量，不得跨轮加总，缓存写入不计入三项）。
- 前序变更：`ae-harness-token-usage` 的首版（五项身份方案）已被本次修订取代，未归档。

## Capabilities

### New Capabilities

- `ae-harness-token-usage`: 覆盖 `engines/ae_harness/` 的两件事——模型创建出口顺带交出密钥环境变量名；事件层为每次模型调用产出一条可归组、可审计的 token 用量记录。

### Modified Capabilities

无。`model-usage-ledger` 与 `agent-reply-usage` 的需求不变：前者管平台账本表与入账口径，后者管用量三元组解析；本变更只在其上游补产出。

## Impact

- 代码（全部在 `engines/ae_harness/` 内）：
  - 新增 `event/usage.py`
  - 修改 `agents/models.py`（返回值加一段）、`agents/creator.py`（返回值改两段）
  - 修改 `event/record.py`、`event/__init__.py`、`event/AGENTS.md`
  - 修改 `agents/AGENTS.md`、`agents/README.md`
  - 修改 4 个调用点：`assistant/agent_executor.py`、`assistant/agent_verifier.py`、`workflow/sop/runner.py`、`workflow/sop_runner.py`
- 依赖方向：`event/` 保持零内部依赖，只收一个 `str`；标签由创建层产出、事件层消费，无环。
- 兼容性：`create_model` 只有 `create_agent` 一个调用方，`create_agent` 全仓无其它模块 import；破坏性影响仅限包内。
- 测试：新增 `tests/engines/ae_harness/unit/`，覆盖标签透传、一次一条、时间锚点、缓存不计重、观测层零依赖。
- 数据与接口：不动数据库、不动后端 API、不动前端；`backend_bridge` 无代码。
