## Why

用例 / 元素定位 / 页面流三处入口网格仍是实线大圆角 + 顶部 4px 色条（`project-card__accent` / `proto-card__accent`），与 principles 撕纸卡（虚线近直角、色块图标、马克笔硬阴影、微倾）不是同一套语言。三处结构几乎相同却各写一份样式。评审已确认：配色用 cycle，本轮只改这三处。

## What Changes

- 新增共享 `SketchCard`（不扩 `KpiCard`）：撕纸入口卡壳 + title / description / meta / lucide 图标 / 删除可选
- 网格 accent 按 index 循环 8 个 `--c-*` 模块色（cycle），微倾按固定角度表循环
- 替换三处列表私有卡样式：`case-manager/ProjectList.vue`、`element-locator/ProjectList.vue`、`workflow/PrototypeList.vue`
- 同步 doodle-craft 组件规格与 `frontend/AGENTS.md` 共享件说明；补 `SketchCard` 单测
- **BREAKING**：无 API/路由破坏；视觉为有意换皮。进入 / 删除业务逻辑仍留在各模块

## 关联文档

- 参考：`temps/hand-drawn-doodle-sidebar.html` `#page-principles` article[1]
- 方案原型：`temps/doodle-sketch-card-prototype.html`
- 归档副本：`dev_docs/05-开发与测试/设计方案与报告/设计方案-手绘涂鸦入口卡.html`

## Capabilities

### New Capabilities

- `frontend-doodle-sketch-card`：共享撕纸入口卡的 doodle 视觉、cycle 配色与三处资源网格消费契约

### Modified Capabilities

（无既有 spec 覆盖这三处列表卡）

## Impact

- 新增：`frontend/src/shared/components/SketchCard.vue` 与 cycle 辅助函数
- 消费方：用例项目列表、元素项目列表、页面流原型列表
- 文档：`doodle-craft/references/components.md`、`frontend/AGENTS.md`
- 测试：`frontend/tests/shared/p0/SketchCard.spec.ts`、`cd frontend && npm run typecheck`
- 不影响：`AppCard`、`KpiCard`、`DeviceCard`、后端 API
