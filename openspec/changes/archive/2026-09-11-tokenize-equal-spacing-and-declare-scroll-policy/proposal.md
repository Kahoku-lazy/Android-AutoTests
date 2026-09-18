## Why

设计系统的"令牌化率"实测只有 **32%**（间距字面量 667 处 vs 令牌引用 315 次），而滚动策略存在**三层口径并存**（`.main-content` / `.doc-page` / `.doc-page.wb-shell → .doc-body`）+ **39 处**手写滚动容器——规则写着"二选一、不混用"，代码里却没有显式声明。批 2 只做两件**可验证**的事：把与令牌**逐字符等值**的间距字面量收敛到令牌（视觉零变化，属构造性等价），把滚动策略**显式写明**并加一层兜底，避免"页面忘了套骨架 → 内容被裁"（本会话搭试验台时实际踩到该坑）。

## What Changes

- **2a · 等值令牌替换**：57 个文件 / **316 处**间距字面量 → `var(--app-space-*)`
  映射（**逐字符相等**，故视觉零变化）：`4px→xs · 8px→sm · 16px→md · 24px→lg · 32px→xl · 48px→2xl`
- **2b · 滚动策略显式化**：`style.css` 的「文档站风格页面布局」一节补两种口径声明（① 页面整体滚动 ② 视口固定 + 内层滚动，**二选一禁止混用**）；`#app` 增加 `overflow: auto` 兜底（`.app-shell` 恰好 100vh 时不会触发，仅在页面缺骨架时把"被裁"降级为"可滚"）
- **无 BREAKING**：2a 为构造性等值替换；2b 兜底在正常路径下不生效
- **明确不做**（需浏览器视觉回归后逐页迁移）：把 13 个 `.doc-page` 页面按口径归类迁移、回收 39 处手写滚动容器

## 关联文档

- 无 PRD/ARCH 关联：设计系统批 2/3，依据 = frontend.md CSS 铁律第 3 条（滚动策略二选一）+ tokens.css 间距刻度
- 承接批 1 归档变更 `2026-09-11-dead-token-cleanup-and-type-floor`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 等价替换 + 注释声明 + 兜底，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 2a：**57 文件 / 316 处**；`var(--app-space-*)` 引用 **315 → 631**；剩余 `padding: <刻度>px` 3 处、`gap: <刻度>px` 8 处（共 11 处，全在**模板内联 style**，被"含引号跳过"规则有意保留，建议随规则 13 的组件拆分一起处理）
- 2b：`style.css` 1 个注释块 + 1 行兜底
- 验证：postcss 全量解析 **95 个样式块 → 0 语法错误**；Vite dev server（5173 在跑）对 4 个改动样式返回 **200** 且 `var()` 生效；`vue-tsc` **35 条既有错误不变**；字号门禁通过
- **登记待办（批 3 / 后续）**：
  - 滚动策略逐页迁移：`.doc-page` **13 处**（其中 `wb-shell` 8 · `detail-page` 3 · 纯 `doc-page` 1 · `workflow-workbench` 1）；内层滚动 **39 处 / 30 文件**（集中 `TaskDetailPage` 4 · `SkillViewerPage.style.css` 3 · `report-generator/index` 2 · `device-inspector/index` 2 · `DevicePoolView.style.css` 2）
  - **case-manager 与 element-locator 的页面根本未使用 `.doc-page`**（走自己的容器类）→ 迁移前需先统一骨架
  - 非等值间距/圆角字面量（需设计决策）、11 处模板内联 style
