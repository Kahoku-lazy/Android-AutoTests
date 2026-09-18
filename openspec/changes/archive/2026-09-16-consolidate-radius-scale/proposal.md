## Why

设计语言要求圆角为**不对称手绘几何**（`--radius-sm: 4px 8px` / `--radius-md: 6px 10px` / `--radius-lg: 8px 14px` / `--radius-pill: 4px 10px 6px 8px`），但实测仍有约 118 处圆角字面量，分两类：① 与已登记令牌**完全等价**的 4 值展开写法（`4px 8px 4px 8px` 14 处、`3px 6px 3px 6px` 16 处、`6px 10px 6px 10px` 9 处、`2px 6px 2px 4px` 1 处）—— 纯令牌绕过；② 可见盒子上的**对称单值**（`999px` 19 处、`8px` 31 处、`6px` 8 处、`10px` 7 处、`12px` 7 处、`14px` 4 处、`4px` 14 处、`18px` 1 处）—— 与不对称几何冲突，其中 `999px` 被设计语言明文点名。已登记的 `--app-radius-pill` 在 modules 内**零引用**。

## What Changes

- ① 类等价写法按令牌替换：`4px 8px 4px 8px` → `var(--app-radius-sm)`、`6px 10px 6px 10px` → `var(--app-radius-md)`、`3px 6px 3px 6px` → `var(--el-border-radius-small)`、`2px 6px 2px 4px` → `var(--comp-sheet-radius)`（**零视觉变化**）
- ② 类对称单值按最接近的不对称令牌替换：`4px`/`6px` → `--app-radius-sm`；`8px`/`10px`/`12px` → `--app-radius-md`；`14px`/`18px` → `--app-radius-lg`；`999px` → `--app-radius-pill`
- 前缀 !important 原样保留
- 登记保留项：`50%`（真实圆点/图钉/头像）、`2px`（已登记的 2px 纸角）、`1px`/`3px`/`5px`（细线/滚动条等图形量）、`0`（重置）、方向性几何（`0 3px 3px 0` 等）、登录页自有圆角（`l3-content-block` 已登记为独立视觉）
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §5.1 与 §八·批次 C（变更 10）
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 2 · `consolidate-radius-scale`
- 令牌真相源：`openspec/specs/frontend-l0-design-tokens/spec.md`（`--radius-*` 规格原子）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增要求「可见盒子的圆角取自不对称规格令牌」

## Impact

- 约 40 个文件（`modules/**` 与 `shared/**` 的 `.vue` / `.css`，含 `style.css` 与 `workbench-theme.css`）
- 观感变化：对称圆角盒子变为不对称手绘几何（`8px` → `6px 10px` 等）；`999px` 胶囊变为 `4px 10px 6px 8px`
- 不影响：`50%` 圆点/图钉/头像、`2px` 纸角、细线几何、登录页独立视觉、布局与色彩

## 登记为后续变更的输入（本变更不做）

- `WorkbenchHeader` 的 `8px 16px 6px 14px` 与 `SkeletonCard` 的 `3px 5px 3px 5px`（已不对称的图形量，待统一档位）