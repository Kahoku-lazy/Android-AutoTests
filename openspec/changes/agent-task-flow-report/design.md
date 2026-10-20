## Context

事件已写入 `ai_task_events`。测试报告列表原先禁止跳转，任务卡「详情」指向 `/ai-assistant/tasks/:taskId`。见 proposal.md 的 Why。本文件记录已经落地的读法，供规格与代码对齐。

## Goals / Non-Goals

**Goals:**

- 只读拼出一轮回复的阶段块，并把连续增量收成一条。
- 两个入口都打开 `/reports/task/:taskId`。
- 页上时间到秒，并给出整次耗时。

**Non-Goals:**

- 不改事件折叠，不为开始类事件补行。
- 不从文本日志回读判决原文。判决取验收结构化输出里的 `passed` 与 `message`，展示在报告页头下方。
- 不改仪表盘最近任务的跳转。
- 不删除旧任务详情路由。

## Decisions

1. 流程接口放在既有 `GET /api/reports/task/{id}`，继续平铺信封。报告模块只读 `AITask` / `AITaskEvent`，与列表同一可见范围。备选是新建 `/api/ai/...` 读接口，会让报告页直打助手接口，与报告模块约定相反。
2. 连续同类型、同一步骤与尝试的增量在服务端合并，`count` 为次数。备选是前端逐条渲染，任务 115 一类会有数百行参数碎片。
3. 阶段块在阶段字符串变化时切开，所以一轮里推理和执行可以交替，仍按时间先后。
4. 年月日时分秒与执行耗时在报告页本地格式化，不改列表的分钟级时间列。

## 模块防火墙自检

- `apps/report_generator` 只读 `apps.ai_assistant` 的模型与已有只读函数（可见范围、助手名），不 import service / runner / consumer。
- 本变更没有 INSERT / UPDATE / DELETE。
- 前端只走本模块 `api.ts` 的 `/reports/task/{id}`，不直连数据库。

## Risks / Trade-offs

- [折叠时未落库的开始事件不会出现在报告里] → 用结束行的正文、参数和 `count` 表示，不回补历史行。
- [旧详情路由仍可手动打开，卡片不再进入] → 规格把两条路径分开写，避免把日志证据要求从旧页删掉。
