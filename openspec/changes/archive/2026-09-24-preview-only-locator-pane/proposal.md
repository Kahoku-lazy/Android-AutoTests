## Why

上一单 `relayout-locator-workspace` 把元素表整个搬进了工作台右栏，于是右栏具备了行内编辑、勾选、新增行、批量删除与测试点开关——这等于把「编辑入口」从一个页面变成了两个页面：同一份数据有了两套写入口，用户也不清楚自己是在浏览还是在改数据。需求方明确：**右栏只做预览，编辑仍必须进入页面**。

## What Changes

- 工作台右栏改为**只读预览**：仍复用同一张七列表纸与同一套硬边按键皮肤，但 MUST NOT 提供行内编辑、行勾选、新增行、批量删除与测试点开关。
- 右栏新增**唯一动作**「进入页面编辑」，跳到该页面的文件详情页 `/elements/projects/:code/files/:fileId`；编辑、新增、删除、测试点在详情页进行（行为与端点不变）。
- 右栏预览只呈现该页元素的**首屏若干条**并如实标注总条数，不假装呈现全部（整页与分页留在详情页）。
- 窄屏退化与目录树紧凑呈现口径不变。

## 关联文档

PRD-04 · ARCH-04

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 「元素表在工作台右栏复用」改为只读预览口径（新增只读约束与进入编辑的入口）

## Impact

- 前端模块：`frontend/src/modules/element-locator/`
  - 新增 `components/LocatorPagePreview.vue`（只读预览表 + 进入编辑入口）
  - `ProjectWorkspace.vue` 右栏由可编辑的 `LocatorFilePanel` 换成该预览件（`LocatorFilePanel` 仍由文件详情页使用，不改）
- 零后端改动：端点、信封、写库路径全部不变
- 不在本单：把预览做成可编辑（上一单已否决）、深链落进并置态、工具栏按钮皮肤统一
