## MODIFIED Requirements

### Requirement: Section summaries use chips instead of raw gray meta lines
章节级汇总信息 SHALL 以 chip（近直角墨边标签）呈现。AI 用量章节头 MUST 只保留分角色 Token 摘要 chip；MUST NOT 再展示与下方 KPI 卡重复的累计 Token、任务数量、费用 chip。其它章节（平台运营等）的设备/任务/工作流类 chip 不受本条约束。AI 用量的分角色 Token 摘要 MUST NOT 再以多行未样式化灰字堆叠。

#### Scenario: AI role breakdown renders as chips
- **WHEN** 后端返回分角色 Token 汇总且前端已格式化为可读字符串
- **THEN** 「累计 / 今日」角色摘要以 chip 形式出现在 AI 用量章节头或紧邻摘要区，页面上不出现「分角色 Token（累计）：…」这类多行裸灰字标签

#### Scenario: AI chapter head omits duplicate metric chips
- **WHEN** 用户查看仪表盘「AI 用量」章节头
- **THEN** 不可见文案含「累计 Token」「任务」或「费用」且带对应汇总数字的 chip
- **AND** 角色·累计 / 角色·今日（或语义等价）chip 仍可见（有角色汇总数据时）
