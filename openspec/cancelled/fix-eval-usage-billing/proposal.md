# Proposal: fix-eval-usage-billing

## Why

审计与前报告复核确认两处正在发生的计费失真：① 助手评测（A1 探针）是真模型调用，但 usage 硬编码 0 token，`assistant_eval` 来源账行费用恒 0；② 任务入账 `record_run_usages` 的模型归属双重缺陷——run 级 model 覆盖逐次 model，且兜底键名 `model_name` 不存在（实际键 `model`），双模型任务账本按执行侧模型错计，与任务正文费用分叉。另登记计价双轨的结构性事实（rates 遮蔽 pricing.json 条目、键名失配地雷）。需求方已批准钱口径变更申请打包。

## What Changes

**钱口径变更申请四要素（已获需求方批准，2026-11-19）：**
- **改什么**：评测入账改按真实 token；任务入账模型归属改逐次优先 + 修键名；pricing.json 删除被 rates 完全遮蔽的 4 个 deepseek 死条目（零行为变化）。**不改任何单价、倍率、汇率与预算默认值。**
- **为什么必须改**：真模型调用按 0 入账 = 平台少记账；双模型错账 = 验收侧用贵模型时账本静默少记，任务正文与账本两个数字分叉，违反「账本是平台费用唯一汇总源」规格。
- **影响面**：ai_assistant/services/live_runner.py（usage 提取）、eval_billing 映射；usage_ledger/api.py 一行（模型归属）；pricing.json 死条目；对应单测。仪表盘/任务费用展示口径不变（汇总源不变），历史账行不自动改写。
- **怎么回退**：还原对应提交即回旧行为；历史已写入账行不受影响（规格禁止自动改写）。

具体：
- **评测真实 token**：`live_runner._ask_model` 改用 AgentEventRecorder 收集 `record.usages`（与 assistant_threads._reply 同范式），逐次带回真实 model/input_tokens/output_tokens；删除硬编码 0 的 usage 字典；docstring「用量带回给账本」变为事实。
- **任务入账模型归属**：`record_run_usages` 改 `model=str(item.get("model") or "") or model`（逐次优先，run 级仅兜底；修键名）。SopRunResult.model 汇总字段保留，不动结果形状。
- **pricing.json 死条目清理**：删 4 个被 RATES 完全遮蔽的 deepseek 条目（lookup_rate 优先，json 兜底永不可达；recalc 同优先级，删除零行为变化），同时消除其键名失配地雷（input_cache_hit vs input_per_million）。**保留**语音历史条目（sambert/tts/asr 等）——显式重算历史 voice 账行仍需其价目；omni-realtime 两表口径冲突与 cache_creation 死参数仅登记事实，不在本变更处置。
- 单测：双角色双模型 usages → 账本各行保留各自模型、按各自价目计费；评测一轮真调用 → 账行 token 非 0；recalc 回归（删条目前后历史重算结果一致）。

## 关联文档

无新增 PRD 需求编号——钱口径缺陷修复。问题来源：后端审计报告 P0-6 / M1 与前报告 A4（复核已证实双重缺陷）。usage_ledger/AGENTS.md 红线 2 厂商文本修订归 align-backend-docs-with-code（已批准），本变更不重复改文档。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `assistant-live-eval`: 「评测用量按次入账且失败不阻断」增补真实用量义务——入账 MUST 携带该次调用的真实 token 与模型名，MUST NOT 以 0 token 占位。
- `model-usage-ledger`: 新增「逐次模型归属优先」requirement——账行 model 取逐次用量记录，run 级模型仅作缺失兜底。

## Impact

- **backend/apps/ai_assistant**：services/live_runner.py、services/eval_billing.py（映射核对）。
- **backend/apps/usage_ledger**：api.py:111 一行、pricing.json 死条目。
- **tests**：tests/ai_assistant/unit（live_run/eval_billing）、tests/task/unit/test_usage_ledger.py（双模型 + recalc 回归）。
- **不影响**：单价/倍率/汇率、仪表盘汇总口径、历史账行、engines 计费公开口（_is_peak_time 私有访问问题另行立项）。
- **协调**：fix-agentscope-usage-defects 已归档，无在途冲突；与变更②（usage_ledger 死代码删除）建议②先合并，避免同文件冲突。