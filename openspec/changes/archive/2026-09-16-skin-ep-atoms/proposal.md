## Why

主题对 Element Plus 的覆盖只做了"部分原子"，导致**未被覆盖的原子直接回落到 EP 默认调色板与默认几何**，其中最严重的是可读性缺陷。本次用 Chromium 实测计算样式，得到的事实基线：

| 探针 | 计算对比度 | 计算圆角 | 结论 |
|---|---|---|---|
| `el-button--danger is-plain` | **1.52** | 4px/8px/4px/8px | 浅桃字（#ffb5a7）压近白底（#fef0f0），**近乎不可读** |
| `el-button--danger`（实心） | **1.69** | 同上 | 白字压浅桃底 —— 首份报告遗漏，同样不可读 |
| `el-radio-button__inner`（首/中/末项） | 16.58 | **0px / 0px / 0px / 0px** | 圆角全部退化为直角 |
| `el-skeleton__item` | — | 4px/8px/4px/8px | 底色 #f0f2f5 冷灰，与暖白纸面（#fffef5）不同源 |
| `el-switch__core` | — | 10px 对称 | 轨道圆角非主题几何 |
| `el-alert`（type=error） | — | — | 使用 EP 默认 `--el-color-error: #f56c6c` / `-light-9: #fef0f0`，tokens.css **完全未覆盖** |

**根因**：`tokens.css` 把 `--el-border-radius-base` 设为**两个值** `4px 8px`；EP 有 3 处把该变量与额外值组合（如 `.el-radio-button:first-child .el-radio-button__inner { border-radius: var(--el-border-radius-base) 0 0 var(--el-border-radius-base) }`），替换后成为 **6 值非法声明**，在 computed-value 阶段失效并回落 initial(`0`)；且因该声明已在层叠中胜出，低特异性规则无法接管，故修复需 `!important`。同时 `--el-color-danger-light-5/-light-9`、`--el-color-error*`、`--el-fill-color*`、`--el-switch-*` 均未覆盖。

## What Changes

- **危险色改为可读的项目危险文字色**：`--el-color-danger` 由 `--color-red-83`（浅桃 #ffb5a7）改为 `--color-red-46`（深红 #b23838，即 `--app-status-danger-text`），并补齐 `--el-color-danger-light-3/5/7/8/9`。一并修正实心 `danger` 按钮、`plain` 变体与表单校验错误文本（EP 的 `.el-form-item__error` 用的是 `--el-color-danger`）
- **补齐 `--el-color-error*`（6 条）**：让 `el-alert type="error"` 等错误面落到已登记的红色族，不再渲染 EP 离板色
- **补齐 `--el-fill-color` / `--el-fill-color-darker`**：骨架与占位底色由冷灰改为登记在案的暖灰族
- **补齐 `--el-switch-on-color` / `--el-switch-off-color`**：开=成功色、关=离线灰，替代 EP 默认的"开=primary、关=border-color(墨色)"
- **修 `el-radio-button` 的圆角退化**：在全局皮肤中显式给 `.el-radio-button__inner` 取 `--app-radius-sm`，并按项目分段控件口径（对齐 `.ac-tabs .is-active`）设置选中态为"柠黄底 + 墨字"，解决 0 圆角与"白字压柠黄"
- **修 `el-switch` 的轨道几何**：轨道圆角取 `--app-radius-sm`、描边取墨色 2px
- **BREAKING**：无。纯主题层覆盖，不涉及接口、路由、鉴权或数据；实心 danger 按钮由"浅桃底白字"变为"深红底白字"，plain danger 由"浅桃字压近白底"变为"深红字压浅红底"

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.8 与 §八·批次 A（P0-5）
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 1 · `skin-ep-atoms`
- 既有要求：`openspec/specs/frontend-l0-design-tokens/spec.md`「Element Plus 覆盖引用主 token 原子」（本变更沿用该约束并新增"覆盖完整性与可读性"）
- 既有正确范式：`style.css` 的 `.el-button--primary` 皮肤、`workbench-theme.css` 的 `.ac-tabs .el-tabs__item.is-active`（黄底墨字）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增要求「Element Plus 原子被覆盖到主题内且交互文本可读」

## Impact

- `frontend/src/shared/styles/tokens.css`：新增/修正 `--el-color-danger*`（6 条）、`--el-color-error*`（6 条）、`--el-fill-color`、`--el-fill-color-darker`、`--el-switch-on-color`、`--el-switch-off-color`
- `frontend/src/style.css`：新增 `.el-radio-button__inner` 及其选中态的几何与配色、`.el-switch__core` 的轨道几何
- 观感变化：全站 danger 按钮与 danger plain 按钮、表单校验错误文字、`el-radio-button` 分段控件（形状与选中态）、`el-switch` 轨道、`el-skeleton` 占位底色、`el-alert` 错误面
- 测试范围：`npm run lint:styles`（EP 覆盖不得出现字面量）、`npx vite build --mode development`，以及 Chromium 计算样式/对比度断言（本变更的核心验收）
- 不影响：`AppTable` / `AppCard` / `KpiCard` 等共享件皮肤；`el-button--primary` 现有皮肤；各模块自有的 `.el-tag--*` / `.el-table` 覆盖

## 登记为后续变更的输入（本变更不做）

- 把 `element-locator/PageElementsWorkbench.vue` 的 `el-alert` 错误态替换为共享 `ErrorState`（调用点统一）→ 变更 6 `unify-loading-states`
- `FilterTabs` 的 `999px` 对称圆角与其余圆角字面量 → 变更 10