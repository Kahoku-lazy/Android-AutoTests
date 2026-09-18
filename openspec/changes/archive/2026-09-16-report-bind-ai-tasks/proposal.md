## Why

执行引擎卸表后，`GET /api/reports` 固定返回空壳，测试报告页图表与表格无数据；PRD 要求 AI 助手任务执行结果进入测试报告，但列表仍绑在已消失的 Run 上。现在要把报告工作台接到助手任务卡，并去掉已 404 的详情跳转。

## What Changes

- `GET /api/reports` 改为只读聚合当前用户可见的 `AITask`：填充 `summary`、`trend`、`runs`（一行一张任务卡）
- 统计单位改为任务卡：成功 = `completed`/`success`，失败 = `failed`（与仪表盘助手任务口径一致）
- 报告列表去掉用例向列（用例数/通过/失败/通过率）；任务 ID 纯文本，**不再**跳转 `/reports/:id` 或用例分解
- 空态与页头文案改为指向 AI 助手发任务，不再提执行引擎
- **BREAKING**（本页契约）：`runs[]` 字段从旧 Run 形状改为任务卡形状（无 `case_count`/`passed`/`failed`/`rate`）；KPI 不再表示用例迭代

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-需求总纲.md` §3.3 / §3.4（AI 输出执行报告 → 测试报告；`PRD-07-测试报告.md` 文件不存在）
- ARCH：`dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md`（报告只读、跨 App 读 Model、写必须走对方 `api.py`）
- 模块约束：`apps/report_generator/AGENTS.md`、`frontend/src/modules/report-generator/AGENTS.md`（`/reports/*` 平铺信封保持）

## Capabilities

### New Capabilities

- `report-ai-task-list`：测试报告列表/KPI/趋势以 AI 助手任务卡为数据源，且列表与 KPI 不跳转详情页

### Modified Capabilities

- （无）`openspec/specs/` 下无既有测试报告能力可改

## Impact

- 后端：`apps/report_generator/views.py`（及必要时本 App 只读查询辅助）；只读 `apps.ai_assistant.models.AITask` + `apps.ai_assistant.api` 可见性/助手名函数；不写 `ai_tasks`
- 前端：`frontend/src/modules/report-generator/index.vue`、`constants.ts`；列表列、筛选文案、KPI 点击、空态
- 不改：助手看板/详情、仪表盘、`/reports/run|task|cases` 空壳与文件下载端点形态
- 测试：报告列表 API 单测；前端报告页列与跳转相关断言
