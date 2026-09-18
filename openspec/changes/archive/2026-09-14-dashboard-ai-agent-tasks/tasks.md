## 1. 仪表盘聚合

- [x] 1.1 用 `_task_qs` 口径实现近 12 日 `AITask` 成功/失败分日序列，替换 `_daily_execution_series` 恒零；验证：有成功卡的日期柱非 0
- [x] 1.2 `execution_summary` 与 `_recent_tasks` 改为同一 queryset 的成功/失败计数与最近卡片（id/title/status/time）；验证：stats JSON 不再恒空

## 2. 仪表盘前端

- [x] 2.1 `TrendBarChart` 图例改为任务成功/任务失败；区块说明改为助手任务卡趋势；验证：与数据同源
- [x] 2.2 `TaskResultPanel` 空态指向平台小助手；有 id 时跳转 `/ai-assistant/tasks/:id`；验证：不再进 `/reports`
- [x] 2.3 按需映射 `completed` → 面板 `success`；验证：成功卡显示 ✓ 而非未执行

## 3. 助手任务卡

- [x] 3.1 `TaskBoard` 单卡仅标题 + 详情；去掉目标/设备/时间/结果/删除；验证：头栏筛选、分组、新建、清空仍在

## 4. 门禁

- [x] 4.1 相关 pytest / vitest；验证：聚合与卡片展示覆盖主路径
- [x] 4.2 目视仪表盘第一行趋势 + 助手任务区；验证：与助手页任务一致
