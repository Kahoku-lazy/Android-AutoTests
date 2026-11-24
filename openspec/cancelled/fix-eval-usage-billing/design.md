# Design: fix-eval-usage-billing

## Context

动机与变更申请四要素见 proposal.md。代码事实（亲验）：

- `live_runner._ask_model`（:158-165）usage 硬编码 0 token；`eval_billing.record_eval_usages` 本身已支持逐次 model/provider/tokens 入账——**缺陷只在供给端**。
- `usage_ledger/api.py:111` `model=model or str(item.get("model_name") or "")`：run 级覆盖逐次 + 兜底键名错误（逐次记录实际键是 `model`，见 engines usage.py 与 task_runner 死函数 _price_call_costs 的正确读法对照）。
- `pricing.py:101-114` lookup_rate（rates.py）优先，json 兜底读 `input_per_million/output_per_million/per_10k_chars`；pricing.json 的 4 个 deepseek 条目用另一套键名且永不可达。
- 参照范式：`assistant_threads._reply`（:247-257）用 AgentEventRecorder 累积 `record.usages`，`as_dict()` 即事件层用量形状（含 model 键）。

约束：不改单价/倍率/汇率；历史账行不自动改写；provider 语义=密钥归属（spec model-usage-ledger 已明确）。

## Goals / Non-Goals

**Goals**
- 评测账行携带真实 token 与逐次模型；任务账行模型归属逐次优先；消除 pricing.json 死条目与键名地雷。

**Non-Goals**
- 不动 rates.py 任何数值；不处置 omni-realtime 两表冲突与语音历史条目（显式重算仍需）；不删 cache_creation 参数/字段（登记事实，处置另行裁决）；不改 engines（_is_peak_time 私有访问另行立项）；不改 AGENTS 文本（归变更⑤）。

## Decisions

### D1 评测用量提取复用 AgentEventRecorder 累积范式
`_ask_model` 内以 AgentEventRecorder 包裹 reply_stream（与 chat 路径同范式），`record.usages` 逐次映射为 eval 事件：`model=item.model or context.model_name`、`provider=context.provider`（密钥归属，替代 eval_billing 的 deepseek 硬编码兜底供给）、真实 input/output/cache tokens、occurred_at 取逐次时间。recorder root 随评测运行过程目录；不渲染 HTML 报告（评测过程产物由既有 eval 链承载）。
- 备选：手工解析 reply_stream 的用量事件——重复 recorder 的累积逻辑（含 cache 拆分），易漂移，弃。
- eval_billing 增 cache_input_tokens 透传（record_usage 已支持该参数），其余不动。

### D2 任务入账一行修复：逐次优先 + 正确键名
`model=str(item.get("model") or "") or model`。run 级 model 参数保留为兜底（chat 单角色路径依赖它），SopRunResult 形状不动。
- 备选：在 task_runner 侧拆双 model 传入——改结果形状牵连前端契约，弃（前报告 A4 最佳修复同结论）。

### D3 pricing.json 死条目删除的零行为变化论证
lookup_rate 优先 ⇒ 4 个 deepseek 条目在计价与显式重算两条路径都不可达；删除前后对任意输入（含历史重算）输出恒等。以回归测试钉死： fixture 含 deepseek 历史账行，删条目前后 `recalculate_usage_costs` 结果一致。语音条目保留（历史 voice 账行显式重算仍需价目）。

### D4 时序
变更②（usage_ledger 死代码删除）先合并，本变更基于其后工作树改 api.py/pricing.json，避免同文件冲突。

## Risks / Trade-offs

- [评测入账金额从 0 变为真实值，仪表盘 assistant_eval 来源费用「上涨」] → 这是恢复正确记账而非口径变更；proposal 影响面已声明，发布说明注明。
- [recorder 引入评测过程文件 IO] → 与 chat 路径同量级；评测低频，可接受。
- [逐次 model 缺失的旧事件形状] → run 级兜底保留，旧数据路径不回归。

## Migration Plan

无数据迁移。历史账行不改写；如需修正历史错账，由运维显式执行 recalc（既有命令，规格允许）。回退 = 还原提交。

## Open Questions

无。omni 冲突、cache_creation、语音条目处置均已明确划出并登记，不影响本设计。