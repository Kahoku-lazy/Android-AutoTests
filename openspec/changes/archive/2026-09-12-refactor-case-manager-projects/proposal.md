## Why

用例管理按 Android / Web / API / 业务四分，入口碎、表单不统一，且绑定可执行步骤结构；当前需要改成「项目 → 无限目录 → 文档型用例」的管理台，只维护测试文档，不再驱动自动执行。

## What Changes

- **BREAKING**：去掉侧栏四个子模块及 `/cases/ui|web|api|storage` 路由；统一入口 `/cases`。
- **BREAKING**：清空并废弃四类可执行用例（含 `ApiTestCase` / `StorageTestCase` / `WebTestCase` 及 `TestDefinition` 的步骤 JSON / 锁 / YAML 导出）。
- 新增「项目」：无项目时空状态引导创建；有项目则卡片列表，点击进入项目工作台。
- 项目内无限层级目录树：新建目录/用例、多选/全选、目录与用例拖拽、单删与批删。
- 去掉预览；仅点击用例后展示统一文档表单（ID、测试类型、业务类型、时间、标题、模块、前置、步骤、预期）。
- 测试类型：`APP` / `WEB` / `API` / `FUNC`；业务类型：`家电` / `照明` / `APP`。
- 步骤与预期结果为两段独立文本，不强制逐步配对。
- `test_runner` 不再把这些记录当可执行定义；dashboard 统计改为文档用例口径。
- 去掉编辑锁 WebSocket 与 `/cases/step-types`、YAML 导出。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（`case_manager` 职责、表前缀 `cm_`、编辑锁 WS 将下线）
- 接口：`dev_docs/05-开发与测试/接口文档/API-用例管理.md`（实现时需整篇改写）
- 产品需求：无独立 PRD-05 现行稿；本次需求以对话确认的文档型用例管理为准，对照 `PRD-00-需求总纲.md` 中「用例管理」定位将从「编排可执行步骤」改为「项目化文档用例」
- UI：前端 Doodle Craft（`doodle-craft` skill / `tokens.css`）；本变更不改主题令牌
- 方案正文：`dev_docs/05-开发与测试/设计方案与报告/设计方案-用例管理项目化重构.md`

## Capabilities

### New Capabilities

- `case-manager-projects`: 项目列表/空状态、项目工作台目录树（无限层级、拖拽、多选删除）、统一文档用例表单与标准信封 API

### Modified Capabilities

- （无现行 `openspec/specs/` 能力文件；行为以本变更的新 spec 为准）

## Impact

- 后端：`apps/case_manager`（models / api / views / urls / consumers）、迁移清空旧数据
- 前端：`frontend/src/modules/case-manager`、`sidebarNavConfig.ts`、相关 vitest
- 下游：`apps/test_runner` 读定义路径、`apps/dashboard` 用例统计、`apps/ai_assistant` 写用例 Tool（改为文档字段或停用结构化步骤写入）
- 通道：删除 `/ws/case-editing/{case_id}` 生产点后，全站 WS 生产点从 2 减为 1（须同步 ARCH / `gateway/routing.py`）
- 测试：`tests/` 下 case_manager 契约与 frontend case-manager 单测
