# 轮次标题去掉中文步骤序号与模型名，角色名改为徽章

## Why

任务详情的轮次标题把序号写了两遍：行首已有「1.」「2.」这样的阿拉伯数字，标题正文又写「步骤一」「步骤二」。同一行还平铺出模型名（一个任务只用一个模型，每行重复）和角色名 `executor_role`，与「执行模型」糊成一段纯文本，扫读时分不清类别与实例，窄屏还要多折一行。

## What Changes

- 轮次标题 MUST 不再出现中文步骤序号（「步骤一」…「步骤十」）与模型名；行首的数字序号是唯一序号。
- 角色名（`executor_role` / `verifier_role` 等）由纯文本改为徽章呈现，与 PASS / FAIL 徽章同一视觉族。
- 「执行模型 / 验收模型 / 规划模型」中文类别、重试「第 N 次」与该步动作 / 结果仍留在标题内。
- 标题拼装从 `TaskDetailPage.vue` 迁到 `helpers/task-detail.ts` 的纯函数并补单测，组件只做渲染。

## 关联文档

无关联 PRD：本次为任务详情报告页的展示层调整，判据限于「标题文本构成」与「角色名以徽章呈现」两项，不涉及接口、存储与计费口径。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-flow-report`: 「步骤标题标明模型在做什么」改为标题不含中文步骤序号与模型名、角色名以徽章呈现，其余构成（类别、重试、动作/结果、PASS/FAIL）不变。

## Impact

- 前端：`frontend/src/modules/task-list/TaskDetailPage.vue`、`TaskDetailPage.style.css`、`helpers/task-detail.ts`、`tests/task-list/p0/task-detail.spec.ts`。
- 后端、接口、数据库、事件存储均不改：`GET /api/tasks/{id}/report/` 的 `data.rounds[].role` / `role_kind` / `model` 保持下发，前端只是不再渲染 `model`。
