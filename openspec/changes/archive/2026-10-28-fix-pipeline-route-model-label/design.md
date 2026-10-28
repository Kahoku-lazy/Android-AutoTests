## Context

`modelLabel` 当前只用 `session` 或 `status`；未开始时没有 session，于是用后端默认 Omni 的 `status.model`。路线选择只改了 `selectedRoute`，没有参与模型行计算。

## Decisions

1. 后端 `build_runtime_status()` 返回 `pipeline_llm_model`、`pipeline_tts_model`、`pipeline_tts_voice`，避免前端硬编码模型名。
2. 前端 `modelLabel`：
   - 有 session：`session.model · session.voice`（实际值）；
   - 无 session 且 `selectedRoute === "pipeline"`：用 status 的 pipeline 字段拼接；
   - 否则用 status 的 Omni 模型。
3. 不改 ready 事件或会话行为。

## Risks

- 状态接口未就绪时 pipeline 字段缺失 → 前端回退到默认 `deepseek-flash + sambert-zhichu-v1 · 知厨`。
