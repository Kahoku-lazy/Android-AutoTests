# 轮次标题去掉角色类别文字，序号只给执行轮，角色徽章按角色分色并加固定标记

## Why

上一轮已经把中文步骤序号与模型名从标题里拿掉，但标题仍是「1. 执行模型 ［executor_role］：动作」。两处还不够清楚：

- 「执行模型 / 验收模型」是把 `role_kind` 翻成中文再念一遍——角色徽章已经写着 `executor_role` / `verifier_role`，类别文字只是重复占宽；本轮要能看到的是「谁在做、第几步、结果如何」。
- 序号目前给每一轮都编（执行、验收各占一个号），读起来像"4 步"，实际只有 2 个执行步骤。序号应当只标执行步骤，验收轮的开头应当是结果。

## What Changes

- 轮次标题 MUST NOT 再出现「执行模型 / 验收模型 / 规划模型」这类类别文字。
- 序号只给**执行轮**：按该用例内的执行步骤计，同一执行步骤的重试共用同一个序号，跨分页不变。验收轮 MUST NOT 带序号。
- 角色名徽章按角色分色：执行角色与验收角色 MUST 用不同的底色（执行取 `--c-ai`，验收取 `--c-workflow`，与该轮左侧强调色同源）。
- 角色徽章前 MUST 有固定标记：执行轮为 `➡️`；验收轮按其判决为 `✅`（PASS）或 `❌`（FAIL），尚无判决的验收轮不给该标记。
- 有判决的验收轮继续在标题上标 PASS / FAIL（保持不变）。
- 序号与重试次数的计算进 `helpers/task-detail.ts`，组件只渲染。

## 关联文档

无关联 PRD：本次仍是任务详情报告页的展示层调整，验收判据是「标题文本构成」「序号只出现在执行轮」「两角色徽章不同色且有固定标记」三项，不涉及接口、存储与计费。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-flow-report`: 「步骤标题标明模型在做什么」改为——不出现角色类别文字、序号只给执行轮且按执行步骤去重、角色徽章按角色分色并带固定前置标记、验收轮以结果标记开头。

## Impact

- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`、`TaskDetailPage.style.css`、`helpers/task-detail.ts`、`tests/task-list/p0/task-detail.spec.ts`、`tests/task-list/p0/task-detail-round-title.spec.ts`。
- 后端、接口、数据库不变：`data.rounds[].role` / `role_kind` / `step_seq` / `verdict` 照旧下发，只是前端换了编排方式。
