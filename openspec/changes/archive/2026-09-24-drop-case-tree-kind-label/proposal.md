## Why

用例管理项目工作台的目录树在每一行右侧都渲染一个「目录」/「文件」文字标签，而该行的图标（📁 / 📄）与尾部信息（目录「N 项」/ 文件更新时间）已经表达了同一件事，标签属重复信息并挤占行内宽度。需求方要求去掉。

## What Changes

- 目录树行**不再渲染**「目录」/「文件」文字标签（含其样式规则）；节点类型仍由图标与尾部信息区分。
- 行的其余信息与交互（目录子项数、文件更新时间、进入提示、拖拽、右键菜单、批量选择）**全部不变**。

## 关联文档

PRD-05 · ARCH-05

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `case-manager-workspace-preview`: 新增「目录树行不重复标注节点类型」要求

## Impact

- 前端模块：`frontend/src/modules/case-manager/components/ProjectTree.vue`（模板一处 + 三条样式规则）
- 零后端改动；不影响元素定位的目录树（那边本来就没有类型文字标签）
- 不在本单：树行其他信息的增删、树皮肤与元素定位对齐
