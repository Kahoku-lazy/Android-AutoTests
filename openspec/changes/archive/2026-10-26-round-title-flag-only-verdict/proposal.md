# 验收轮的判决只由 ✅ / ❌ 表示，标题不再挂 PASS / FAIL 徽章

## Why

上一轮按目标格式把「✅ ／ ❌」标记与 PASS / FAIL 徽章并排放在验收轮标题里，同一件事说了两遍：标记已经一眼给出通过与否，紧跟的 PASS 徽章只是把同一个布尔再说一次，还多占一格宽度、多一种颜色干扰。执行轮的 `➡️` 保留——它标的是角色，与判决不重复。

## What Changes

- 验收轮标题 MUST NOT 再渲染 PASS / FAIL 徽章；判决只由 `✅`（PASS）或 `❌`（FAIL）标记表示。
- 无判决的验收轮维持现状：没有标记，也没有徽章。
- 执行轮的 `➡️` 标记、序号、角色徽章与配色全部不变。
- 用例标题与页头摘要里的 PASS / FAIL 徽章不受影响（那是用例级结果，不是单轮判决）。

## 关联文档

无关联 PRD：任务详情报告页的展示层微调，判据是「验收轮标题里只有 ✅/❌、没有 PASS/FAIL 文字」。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-flow-report`: 「步骤标题标明模型在做什么」里「验收轮在有判决时 MUST 同时在标题上标 PASS 或 FAIL」改为「判决 MUST 只由 ✅ / ❌ 标记表示，MUST NOT 另挂 PASS / FAIL 徽章」。

## Impact

- 前端：`TaskDetailPage.vue`、`TaskDetailPage.style.css`、`helpers/task-detail.ts`（删 `roundOutcomeText`）、两个 `tests/task-list/p0` 用例。
- 后端、接口、数据库不变：`verdict.passed` 照旧下发。
