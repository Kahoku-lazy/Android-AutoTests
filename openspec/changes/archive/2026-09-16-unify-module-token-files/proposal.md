## Why

`frontend-l0-design-tokens` 的既有要求「模块令牌按模块落文件」规定：拥有模块级场景令牌的模块 SHALL 在本模块目录提供 `tokens.css` 并覆盖**全部**模块级令牌。实测违约两处：`element-locator` **没有 tokens.css**，其 `--locator-header-icon-end` 在 **3 个页根**各内联声明一次（且注释写"tokens.css 未登记 #c4b5fd"，而实际值早已是 `var(--color-indigo-84)`，注释失真）；`case-manager` 虽有 tokens.css，但 `--case-icon-accent` 仍在 3 个页根重复声明。本变更为既有要求的实现修复，不改变任何 spec 级行为，故 `skip_specs`。

## What Changes

- 新建 `modules/element-locator/tokens.css`：把 `--locator-header-icon-end` 声明在模块页面根类 `.locator-workbench` 下；为该模块 3 个页根统一补上 `locator-workbench` 类（现状 3 个页根类各不相同，无共同模块根类）
- `main.ts` 注册新的模块 tokens.css
- 删除 `element-locator` 3 处内联声明块（含失真的注释）
- 把 `case-manager` 的 `--case-icon-accent` 迁入 `modules/case-manager/tokens.css` 的 `.case-workbench` 块，删除 3 个页根处的重复声明
- **保留**（并登记理由）：`--case-sheet-grid/head-bg/head-fg/head-border` 是 `.case-sheet__table` **表元素局部**登记；`--case-menu-shadow` 在浮层元素**自身**登记（Teleport 到 body 后模块根不再是祖先，必须在元素上声明）
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §5.9 与 §八·批次 C（变更 13）
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 2 · `unify-module-token-files`
- 既有要求：`openspec/specs/frontend-l0-design-tokens/spec.md`「模块令牌按模块落文件」「模块令牌作用域保持在模块页面根类」

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 本变更把代码修复到既有要求，`.openspec.yaml` 已置 `skip_specs: true`）

## Impact

- `frontend/src/modules/element-locator/tokens.css`（新建）、`main.ts`（注册）、`element-locator` 3 个页根（补模块根类 + 删内联块）
- `frontend/src/modules/case-manager/tokens.css`（新增 1 条）、`case-manager` 3 个页根（删内联块）
- 零视觉变化：迁移民的值全部原样，作用域覆盖等价或更宽（模块根类仍是 3 个页面的祖先）
- 不影响：`--case-sheet-*` / `--case-menu-shadow` 的元素局部登记、接口与数据

## 登记为后续变更的输入（本变更不做）

- 本轮扫描发现**同类碎片化还存在于 `report-generator`（5 条 `--rg-*`）与 `dashboard`（5 条 `--ch-*`）**，两者都无 tokens.css 且页根不统一 —— 超出本变更范围，登记进变更 14 清退批次的输入（附页根统一的前提工作）