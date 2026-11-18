## Why

关键词对照表已落库（serial-log-keyword-db-scope，已归档），但页面仍只读：新增型号专用词或修正词条只能走后端维护函数，运营无法自助。需求方要求提供页面维护能力——**新建、编辑、删除**日志关键词，权限与端口自定义增删改同口径（仅超级管理员）。

## What Changes

- 新增三个超管接口（沿用端口 CRUD 先例：POST 201 / PATCH / DELETE，错误给可读 400）：
  - `POST /api/serial-log/keywords/`：新建条目（keyword / module / feature 必填，scope 缺省通用，feature_id 缺省续编）；同唯一键重复 → 可读拒绝。
  - `PATCH /api/serial-log/keywords/<int:row_id>/`：部分更新；唯一键撞车 / 条目不存在 → 可读拒绝。
  - `DELETE /api/serial-log/keywords/<int:row_id>/`：删除单条（二次确认在前端）；不影响日志文件与采集。
- `GET /api/serial-log/keywords/` 的功能点条目**新增 `row_id`**（编辑/删除的定位键），其余口径不变。
- `api.py` 增 `create_keyword`（重复拒绝）/ `update_keyword`（部分更新 + 撞车守卫）；`delete_keyword` 已有；唯一写点纪律不变。
- 前端关键词 Tab：超管可见「新建关键词」按钮 + 行内编辑/删除操作列 + 模块私有 `KeywordFormDialog.vue`（el-dialog + sketch-kit，沿用 PortFormDialog 范式）；**非超管仍恰四数据列、零写控件**。
- 范围输入：下拉（通用 + 已有 SKU 范围）允许创建新 SKU 值，后端白名单校验兜底。
- **BREAKING**（规格口径）：关键词表「只读」红线放开为「非超管只读、超管可增删改」；表格由「恰四列」改为「四数据列 + 超管操作列」。接口路径、信封与既有读口径不变。
- 红线变更申请（随 design 提交，经需求方确认后才动 AGENTS）：前端 serial-log AGENTS「关键词表只读」条款、后端 serial_log AGENTS 接口表与职责段。

## 关联文档

关联《PRD-平台总需求》§1.2 功能介绍第 6 条（验收证据：串口日志关键词命中）与 §3.2 数据业务流。PRD 为大纲体无编号；本变更来源于需求方 2026-11-18 口头需求「日志关键词需要一个新建的功能」，经决策确认为**完整 CRUD、仅超级管理员**，并先行归档上一单再立本单。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `serial-log-module`: 新增「关键词维护接口（仅超管）」需求（三个写端点 + 目录带 row_id + 权限与错误口径）。**不改「串口日志接口路径与契约」**——该需求正被实施中的 add-serial-log-custom-ports 修改，本单以 ADDED 新需求承接关键词端点，避免 delta 交叉。
- `device-log-keyword-catalog`: 「表格只读且如实说明生效时机」改名为「表格维护权限与生效时机」并改写（非超管只读、超管增删改）；「表格列、范围筛选与搜索口径确定」增加超管操作列口径（四数据列不变）。
- `serial-log-page`: 「页内以两个 Tab 承载无线端口与日志关键词」放开关键词维护入口（仅超管），切 Tab 不发写请求等口径保留。

## Impact

- **后端**：`backend/apps/serial_log/`（`api.py`、`views.py`、`urls.py`、`keywords.py` 目录组装带 row_id）；无新表、无迁移。
- **前端**：`frontend/src/modules/serial-log/`（`api.ts`、`constants.ts`、新增 `helpers/keyword-form.ts` / `composables/useKeywordCrud.ts` / `components/KeywordFormDialog.vue`、`LogKeywordPanel.vue` 及其样式、页面入口传 can-manage）。
- **规格**：三份 delta（见上）；与 add-serial-log-custom-ports **零需求重叠**（已逐条核对：其改端口开关状态 / 接口契约 / 字号呈现 / 页内权限边界，本单改关键词维护 / 目录权限 / Tab 入口）。
- **测试**：`tests/serial_log/{unit,integration,api}`（CRUD 权限、重复拒绝、撞车守卫、row_id 契约）；`frontend/tests/serial-log/`（表单校验、弹窗编排、面板操作列与只读边界）。
- **规则变更申请**：两份 AGENTS 条款（design.md 四要素），获批后才动。
- **不动的部分**：`sl_log_keywords` 表结构、迁移、engines、采集链路、`sl_log_ports` 与端口 CRUD。
