## Why

元素定位仍按 Android / Web / API 三个侧栏入口与三套树管理，与已落地的用例管理「项目 → 目录 → 文件」工作台不一致；需要统一信息架构，同时保留三域资产差异与下游按叶子 ID 的引用。

## What Changes

- **BREAKING**：侧栏「元素定位」收成单项；去掉并列子菜单；`/elements/android|web|api` 重定向到系统项目工作台。
- 新增系统内置三项目（`android` / `web` / `api`）：不可新建、删除、改名；点击进入目录工作台。
- 项目内统一无限目录树；叶子按域沿用现有类型：Android=页面、Web=Web 元素、API=接口端点。
- **BREAKING**：停止用 `Page.is_folder` / `WebGroup` / `ApiGroup` 作为工作台写路径；分组写接口改为 410。
- 迁移：旧文件夹/分组变成目录，叶子迁入对应项目，**叶子 ID 尽量不变**。
- 跳转流（PageFlow / WebPageFlow）本期隐藏入口，数据保留。
- 下游：检查器导入挂 Android 目录；workflow 只读适配；dashboard 按项目汇总。

## 关联文档

- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（`element_locator` 职责、表前缀 `el_`）
- 接口：`dev_docs/05-开发与测试/接口文档/API-元素定位.md`（实现时需改写）
- 方案正文：`dev_docs/05-开发与测试/设计方案与报告/设计方案-元素定位项目化重构.md`
- UI：Doodle Craft（`doodle-craft` skill / `tokens.css`）；不新造令牌
- 对照：`设计方案-用例管理项目化重构.md`（流程同构，项目为系统内置）

## Capabilities

### New Capabilities

- `element-locator-projects`: 系统三项目列表、项目工作台目录树、按域文件编辑与标准信封 API、旧树写路径停用与迁移

### Modified Capabilities

- （无现行 `openspec/specs/` 能力文件；行为以本变更的新 spec 为准）

## Impact

- 后端：`apps/element_locator`（models / api / views / urls / migrations）
- 前端：`frontend/src/modules/element-locator`、`sidebarNavConfig.ts`
- 下游：`device_inspector` 导入、`workflow` 素材只读、`dashboard` 计数、检查器选页对话框跨模块 api 收敛
- 通道：无 WS 变更
- 测试：element_locator 契约与前端树/项目单测
