## Why

知识库页把「检索配置」当成一张常驻卡片平铺在左栏顶部，抢走了模块列表的首屏位置：全局检索策略一年改不了几次，却天天占着用户第一眼，而每天要用的勾选、编辑、预建索引被挤到下面。配置本身是「改一次、存一次」的表单，常驻展示既没有信息价值，也让左栏同时承载「全局策略」与「模块清单」两件事。

## What Changes

- 左栏不再渲染「检索配置」卡片（`RetrievalSettingsCard.vue` 从 `ModulePanel` 的页面流里移除）。
- 「知识模块」卡头部的「新增」按钮左侧新增「配置」按钮（仅超管可见，与「新增」同一权限口径）；点击后弹出「检索配置」对话框。
- 检索配置的字段与保存口径不变：向量模型、默认返回条数、相似度阈值、切块大小、切块重叠；保存成功后仍提示「已保存，切块已变，需重建索引」或「检索配置已保存」。
- 对话框每次打开时重新拉取当前配置与向量模型列表（不再依赖页面挂载时加载），加载失败在弹窗内给可读原因，不阻塞模块列表。
- **BREAKING**：无。接口、字段与校验口径不动，仅改变入口位置与展现形态。

## 关联文档

- 无关联 PRD 编号：本变更只是把既有能力（`openspec/specs/knowledge-retrieval-settings`）的入口从常驻卡片收进弹窗，不新增产品功能、不改字段与校验。
- 既有规格：`openspec/specs/knowledge-retrieval-settings/spec.md`（配置字段、校验、改切块作废索引、仅超管可写）与 `openspec/specs/knowledge-search-entry/spec.md`（知识库页左栏模块列表与权限显隐）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `knowledge-search-entry`: 新增「检索配置以弹窗入口承载」要求——配置不再平铺在页面，入口在「知识模块」卡头部、与「新增」并列，仅超管可见；弹窗打开即读当前配置，含输入故点遮罩不关闭。

## Impact

- 代码：`frontend/src/modules/knowledge-search/`（`components/ModulePanel.vue`、`components/RetrievalSettingsCard.vue` → `components/RetrievalSettingsDialog.vue`、`constants.ts`）。
- API：无改动。仍走 `GET/PUT /api/knowledge-search/settings/` 与 `GET /api/ai/model-configs/`。
- 测试：前端无 `knowledge-search` 用例目录；按门禁跑 `npm run typecheck` / `lint` / `lint:styles` / `lint:lines` / `build` / `test`。
- 文档：无模块文档需要同步（`frontend/AGENTS.md` 未登记 knowledge-search 模块文档）。
