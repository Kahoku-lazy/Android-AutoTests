## Why

元素定位元素行的「收敛口径」刚落地上线，评审代码时发现三处前后端口径不一致的行为问题：更新时可以把元素名称清空，但清空主定位会被拒（`element_fields.py` 只校验 `primary_xpath` 非空）；单格更新失败后的重载会顺带清空用户已勾选的行（`usePageElements.ts#load` 无条件重置 `selectedIds`）；手动新增撞上同页既有 `(resource_id, bounds)` 时只回一句泛化中文原因，用户无法知道撞的是哪一行。同时模块内留着一批死代码与类型债：5 个接口封装返回 `any`（调用侧只能就地断言）、`createdLeafId` 有一条永不命中的分支、`primary_stable` 无任何消费、文件详情页为执行一次删除构造整套目录树状态并在删除后白拉一次树。趁口径刚收敛、改动面小，现在一次清掉。

## What Changes

- 写入校验收口：更新元素时**元素名称 MUST 非空**（与主定位同口径），空值返回 HTTP 400 带中文原因且 MUST NOT 写库（**BREAKING**：此前允许把元素名称清空）。
- 手动新增撞去重键（同页相同 `resource_id` 与 `bounds`）时的 HTTP 409 文案 MUST 指出既有元素（元素名称与 id），不再只给泛化原因。
- 表格行内校验补「元素名称非空」，与后端同口径；双击清空后拒绝并恢复原值。
- 单格更新失败后的重载 MUST NOT 清空用户已勾选的行（只保留仍存在的 id）；批量删除成功后仍清空勾选。
- 前端清理：5 个 legacy 端点封装补 wire DTO 类型（消除 `any` 与就地断言）；删 `createdLeafId` 死分支、`primary_stable` 死字段、`apiGetPages` 死导出、新增弹窗里的死校验分支；`LocatorFileView` 不再构造 `useLocatorTree`（消除进入详情页的重复目录树请求）；`LocatorFilePanel` 去掉从未生效的身份块与派生自单值 `kind` 的标签；清 `tokens.css` 注释残留。
- 文档：补 `frontend/src/modules/element-locator/AGENTS.md`（模块红线、信封双轨登记、拖拽双通道、关单附加项）。
- **不改**：目录树能力（拖拽 / 批量移动 / 级联删除）、元素表七列呈现口径、`el_elements` 表结构与唯一约束、检查器快照导入链路。
- **不做**：触摸拖拽交互增强（长按反馈、边缘自动滚动）；两条前端零调用后端端点（`POST /api/elements/move/`、`POST /api/elements/files/batch-delete/`）的下线（属 API 面收缩，另开变更）；给元素表补 resource-id / 坐标列（与已同步的七列口径冲突，改由 409 文案指认既有行）。

## 关联文档

- PRD-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-element-fields`: 写入必填口径（更新时元素名称非空）与手动新增撞去重键时的拒绝告知内容。
- `element-locator-page-workbench`: 行内校验补元素名称非空、单格更新失败后保留勾选、撞车的提示呈现。

## Impact

- 后端：`apps/element_locator/element_fields.py`（更新白名单的必填校验）、`apps/element_locator/api.py`（新增冲突文案带出既有元素）、`apps/element_locator/views_page_elements.py`（文案透传，状态码不变）。
- 前端：`frontend/src/modules/element-locator/` 下的 `api.ts`、`types.ts`、`helpers/elementRowValidation.ts`、`composables/usePageElements.ts`、`composables/useLocatorTree.ts`、`components/PageElementsWorkbench.vue`、`components/PageElementFormDialog.vue`、`components/LocatorFilePanel.vue`、`components/LocatorTree.vue`、`LocatorFileView.vue`、`tokens.css`，并新增模块 `AGENTS.md`。
- 测试：`tests/graybox/integration/test_element_row_crud.py`（补「清空元素名称被拒」与「409 文案含既有元素」用例）、`frontend/tests/element-locator/p0/`（校验纯函数与工作台用例）。
- 文档：元素定位接口文档同步错误文案口径；PRD-04 不因本变更改动。
- 兼容性：**BREAKING** 仅一处 —— 若已有客户端依赖「更新时把元素名称置空」，该调用将开始被拒；库中已存在的空名称行照常展示，本变更不做数据清理。
