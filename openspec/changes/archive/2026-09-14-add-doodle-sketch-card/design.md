## Context

三处入口网格（用例 `ProjectList`、元素 `ProjectList`、页面流 `PrototypeList`）各自实现顶条 accent 卡。KpiCard 已是 doodle 壳，但信息结构是指标/仪表盘入口，不能再塞第三变体。评审原型 `temps/doodle-sketch-card-prototype.html` 已确认 cycle 配色、本轮只改这三处。

## Goals / Non-Goals

**Goals:**

- 新建共享 `SketchCard`，DNA 对齐 `#page-principles` article[1]
- accent 按 index cycle 八模块色；微倾按固定角度表
- 三处列表替换私有卡，业务 enter/delete 仍在模块

**Non-Goals:**

- 不改 `AppCard` / `KpiCard` / `DeviceCard`
- 不套 AI 任务卡、报告失败卡
- 不改后端 API、路由表

## Decisions

### 1. 新建 SketchCard，不扩 KpiCard

- **选择**：`frontend/src/shared/components/SketchCard.vue`
- **理由**：KpiCard 是指标；SketchCard 是可进入资源项。混在一个 variant 会糊职责。
- **备选**：KpiCard 第三变体 —— 评审已排除。

### 2. cycle 由父级注入 index 派生值

- **选择**：`sketchToneAt(i)` / `sketchTiltAt(i)` 纯函数，父级 `v-for` 传入 `tone` / `tilt`。
- **理由**：组件无列表上下文；单测可直接断言 CSS 变量。
- **备选**：组件内 nth-child —— 插槽/删除后序号与视觉错位，放弃。

### 3. Lucide 图标走已登记子集

- **选择**：用例 `layers`、元素 `crosshair`、页面流 `git-branch`（均已在 `lucide-registry.ts`）。
- **理由**：不扩包；与侧栏/页头一致。
- **备选**：每张卡换不同图标 —— 非本轮需求。

### 4. 删除为可选 prop

- **选择**：`deletable` 默认 false；元素列表不传。删除按钮 `@click.stop` 后 `emit('delete')`。
- **理由**：元素系统项目不可删。

## Risks / Trade-offs

- 网格 gap 需略大于硬阴影 4px，避免阴影互相裁切；沿用现有 `--app-space-md`。
- 元素列表曾有父级 `nth-child` 旋转，会与卡内 tilt 叠乘；替换时去掉父级 transform。
