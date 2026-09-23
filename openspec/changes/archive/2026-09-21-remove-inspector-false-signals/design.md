## Context

- testid 现状（真机探针 `temps/dbg-save-dialog.mjs`）：弹窗内 `[data-testid]` 仅有 `save-page-select`、`save-confirm-btn`；`.el-cascader` 节点存在 1 个、`input` 4 个、表单项标签为「目录路径 / 保存目标 / 选择页面」——弹窗渲染正常，只是 `data-*` 没有到达 DOM。
- 成因：Element Plus 的 `el-cascader` 不把未声明的 `data-*` 透传到可查询的根节点，挂在它上面的 testid 属于「声明了但永不生效」的钩子。
- store 现状：`analyzeSnapshot` 被 `capture()` / `viewSnapshot()` / `retry()` 调用；`clearChecked` 被 `applySnapshot()` / `deleteSnapshot()` 调用——均为模块内部调用，组件侧 0 命中。
- 前置一致性：上一轮 `purge-inspector-dead-code` 已把同样「对外暴露但无消费」的 `devices` 从 `return` 移除；本变更是同一口径的收尾。

## Goals / Non-Goals

**Goals:**

- 让 `save-folder-cascader` 这个测试钩子真实可用
- 让 store 的对外面只保留有外部消费者的成员

**Non-Goals:**

- 不改任何交互、样式视觉与请求行为
- 不为钩子补用例、不引入 e2e
- 不重命名既有正常 testid（`save-page-select` / `save-confirm-btn` 不动）

## Decisions

**D1 用普通 `<div data-testid=...>` 包裹，而不是把 testid 挪到 `el-form-item`**
理由：普通 HTML 元素必定渲染 `data-*`，行为确定且可当场真机验证；`el-form-item` 是否透传 `data-*` 取决于 Element Plus 版本与 `inheritAttrs` 设置，属于换个地方再赌一次。
备选：挪到 `el-form-item` → 否决（不确定，且语义指向表单项而非控件）；备选：删掉该 testid → 否决（将来仍需要定位这个控件，删掉等于放弃钩子）。

**D2 `analyzeSnapshot` / `clearChecked` 只从 `return` 移除，函数本体保留**
理由：它们仍服务 store 内部流程；移除后模块内调用点不变，组件侧本就没有调用点，因此是零风险的公开面收窄。
备选：连函数一起内联 → 否决（`retry()` 与 `deleteSnapshot()` 都要用，内联会造成重复实现）。

## 模块防火墙自检

- 跨 App import：零新增
- 写库收敛 api.py：不涉及（无后端改动）
- 前端不直连数据库：不涉及
- HTTP 出口：不变（不新增/修改请求）
- 共享层：不动 `shared/**`；只改本模块的弹窗组件与 store
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [包裹层影响弹窗布局] → 包裹层 `width: 100%`；`el-cascader` 自带 `.save-folder { width: 100% }` 不变；真机复核弹窗与控件宽度
- [移除 store 成员若被漏检的消费方引用] → `frontend/src` 全量检索两名字：除 store 内部定义与调用外 0 命中（模板访问不存在的 store 键不会在构建期报错，故以检索为判据）

## Migration Plan

1. 包裹 testid → 真机确认 `[data-testid="save-folder-cascader"]` 可查到、控件宽度不变
2. store 收窄公开面 → 检索两名字确认组件侧 0 命中 + `vitest tests/device-inspector` 通过
3. 门禁：`lint:styles` + `vite build`
4. 回滚：`git revert`；无数据迁移

## 伴随发现（已登记，未在本单处理）

- **`.save-folder { width: 100% }` 从未生效**：本单加包裹层时真机核宽度发现，`.el-cascader` 根节点上**没有 `data-v-*` 作用域属性**（`attrs = ["class", "tabindex"]`），因此 `.save-folder[data-v-9e59799a] { width: 100% }` 这条 scoped 规则永不匹配；实测「目录路径」控件宽 **218px**，而同一弹窗的「选择页面」下拉为 **394px**（全宽）。
  - 影响：该处一行 CSS 属「声明了但永不生效」（与本单一类），且同弹窗两个字段宽度不一致；
  - 未在本单修的原因：修好它会让控件从 218px 变为全宽（**用户可见的视觉变化**），超出「零行为变化」的轻量卫生单边界，属产品取舍；
  - 可选修法：`.save-folder-field :deep(.el-cascader) { width: 100%; }`（包裹层带作用域属性，`:deep()` 可穿透到子组件内部）。

## Open Questions

（无）
