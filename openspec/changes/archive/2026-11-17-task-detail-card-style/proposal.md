## Why

任务详情页仍是涂鸦风（`2.5px dashed` + 硬投影 + 粗描边），而仪表盘的「任务执行结果」已经是纯净卡片风；同一个人在同一天用两套视觉语言审计同一次任务。加上刚上线的四层耗时把它画成青色 `2px` 描边块，比 PASS/FAIL 更抢眼，密集步骤里视线先落在时间上。

## What Changes

- 步骤行改为**卡片**：左侧 28px 状态方块（✓ / ✗ / △ / ○）+ 动作 + 右侧「天蓝时间片 + 结果标签」。
- **BREAKING（视觉）**：结果由「只有一个 PASS/FAIL 描边徽标」改为「状态方块 + 文字标签」两处一致表达；方块用 ✓/✗/△/○，不使用 emoji `✅`/`❌`。
- 用例卡、摘要四格、过程块全部去虚线 / 去硬投影 / 去 2px 描边，统一 `1px solid` + 圆角；展开体改浅底内嵌。
- 耗时 chip 保留天蓝填充（`--color-cyan-74`），描边收细到 1px，数字等宽（`tabular-nums`）。
- 过程卡左侧 3px 角色色条（执行紫 / 验收蓝），次数标签改胶囊。

## 关联文档

- 无独立 PRD 编号：纯视觉调整，对齐既有 OpenSpec 规格 `agent-task-flow-report` 与仪表盘 `TaskResultPanel.vue` 的卡片语言。
- 设计依据：`temps/task-detail-card-style-proto.html`（方案稿 v1，含现状/方案可点对照）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-task-flow-report`: 「步骤行标题与结果徽标」改为卡片化 + 状态方块与文字标签双通道；补充结果图标映射，明确不使用 emoji `✅`/`❌`。

## Impact

- 前端：`task-list/components/CaseStepList.vue`、`RoundProcess.vue`、`TaskDetailPage.vue` 与三个 `.style.css`。
- 测试：`tests/task-list/p0/task-detail-round-title.spec.ts` 补状态方块与耗时断言；既有徽标断言保持。
- 后端 / 接口 / 数据 / 折叠逻辑：无改动。
