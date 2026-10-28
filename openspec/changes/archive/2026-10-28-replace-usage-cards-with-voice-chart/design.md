## Context

当前 `usage_ledger.today/total` 是全部来源；图表需要只统计 Voice，所以后端增加 source 过滤，并在 dashboard stats 返回 voice_today/voice_total。

## Decisions

1. `usage_summary(period, recent_limit, source="")`：source 非空时 `filter(source=source)`。
2. Dashboard 增加 `voice_today` / `voice_total`，前端映射为 `voiceToday` / `voiceTotal`。
3. 前端用 `SeriesBarChart`：x 轴分类顺序固定为 LLM/TTS/Realtime/Embedding/ASR，取当天与累计分类并集；两个系列当天/累计。
4. 移除原卡片、表格及无用样式；空数据时显示「暂无 Voice 用量」。

## Risks

- 只显示有记录的分类；没有 TTS/ASR 记录时 x 轴不出现这些标签，符合实际用量。
- 累计可能包含历史 task；source=voice 过滤避免混入。
