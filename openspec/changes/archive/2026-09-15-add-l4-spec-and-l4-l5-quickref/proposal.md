## Why

L4（表格 / 卡片网格 / 表单）与 L5（覆盖层）是 `frontend/AGENTS.md`「布局区域与归属」表里唯二没有「层速查」的两层：L0–L3 各有 6 段式速查与对应 spec（`frontend-l2-page-region` / `frontend-l3-container` / `frontend-l3-content-block`），L4/L5 只有表格里两行口径。结果是接手者读不到「表格什么时候可以用原生 `el-table`、分页走哪一套、表单要不要写 `:rules`」。L5 契约已在上一变更 `converge-l5-overlay-language` 沉淀为 `frontend-l5-overlay` spec；L4 尚无 spec。本变更把 L4 契约规格化，并补齐两层速查。

## What Changes

- 新增能力 spec `frontend-l4-data-surface`（4 条需求）：表格首选共享件与能力边界例外、分页唯一实现、表单校验口径、卡片与网格零件口径
- 在 `frontend/AGENTS.md` 的「L3 层速查」之后、「跨模块共享文件：`shared/`」之前，新增「### L4 层速查：表格 / 卡片网格 / 表单」与「### L5 层速查：覆盖层（阻塞 / 非阻塞）」，体例与 L0–L3 速查对齐（① 元素链 ② 代码范围 ③ 能写什么 ④ 不能写什么 ⑤ 契约与验收 ⑥ 破约如何被发现）
- L5 速查的真相源指向既有的 `openspec/specs/frontend-l5-overlay/spec.md`；本变更**不新增 L5 需求**
- 在两层速查的 ⑥ 登记 3 类真实缺口：3 处原生 `el-table` 例外（`PageElementsPanel` / `StructureAnalysisPanel` / `PageElementsWorkbench`）、1 处手写分页（`report-generator/ReportDetail.vue`）、11 处仅 `required` 无 `:rules` 的表单项
- 修正 `frontend/AGENTS.md` L0 §⑥ 的失效计数：原文「**30 个文件**是显式 `import { ElMessageBox }`」；实测显式 `from 'element-plus'` 为 **36 文件**、`import { ElMessageBox }` 为 **17 文件**（原文把两类混为一谈，结论方向仍成立）
- **BREAKING**：无。本变更不改任何代码，行为、接口、路由、测试与构建均不变

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md`：L5 速查的真相源（上一变更创建）
- `openspec/changes/archive/2026-09-14-converge-l5-overlay-language/`：L5 收敛的实施与归档记录
- `dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L4-L5现状复盘.html`：L4 / L5 现状基线，本变更的全部计数均取自该报告的实测口径并已复核
- `openspec/changes/archive/2026-09-14-docs-l2-quickref/`：速查补写体例的先例
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更属前端分层契约的规格化与文档补齐，不改业务需求

## Capabilities

### New Capabilities

- `frontend-l4-data-surface`: L4 数据展示面的实现口径与边界——表格首选共享件的能力边界与登记例外、分页唯一实现、表单校验口径、卡片与网格零件口径

### Modified Capabilities

（无）

## Impact

- 文档：`frontend/AGENTS.md` 新增两节（约 120 行）+ 修正 1 处失效计数
- 规格：`openspec/specs/frontend-l4-data-surface/spec.md`（归档时由 delta 生成）
- 不影响：任何前端代码、后端 API、路由表、`openspec/specs/` 既有能力、测试与构建
