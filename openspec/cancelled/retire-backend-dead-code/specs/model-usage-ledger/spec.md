# model-usage-ledger Delta

## REMOVED Requirements

### Requirement: Voice 用量图表

**Reason**: 语音通道已随知识助手整体退役（retire-engines-agents），`source=voice` 无任何生产写入方，图表数据恒空，前端切换按钮与数据链属死 UI，随退役清扫一并删除。

**Migration**: 无需数据迁移——历史 voice 账行保留在 `ai_usage_records` 作归档，平台费用汇总口径不变；前端不再渲染 Voice 图表与切换按钮。

## MODIFIED Requirements

### Requirement: 用量来源过滤

`usage_summary` SHALL 支持按 `source` 过滤。仪表盘 MUST NOT 再提供 `voice_today` / `voice_total` 字段（语音来源已退役，无生产写入方）。

#### Scenario: 查询 Voice 汇总

- **WHEN** 调用 `usage_summary("today", source="voice")`
- **THEN** 只返回 `source=voice` 的历史账行（语音退役后无新写入，当日通常为空），MUST NOT 混入其他来源

#### Scenario: 仪表盘不再含语音口径

- **WHEN** 前端请求仪表盘用量汇总
- **THEN** 响应不含 `voice_today` / `voice_total` 字段