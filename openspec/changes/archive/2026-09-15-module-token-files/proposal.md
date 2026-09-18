## Why

变更 A（`atomize-shared-design-tokens`）把全部字面量色值收敛为 T0 主 token 原子，但**模块令牌仍散落在共享文件里**：`.ai-workbench`(42) 与 `.case-workbench`(2) 声明在 `shared/styles/tokens.css`，workflow 私有的 `--ac-*`(30) 声明在 `shared/styles/workbench-theme.css`；同时 85 处模块/组件级载体直写字面量色值。模块无法自己回答「我的样式令牌在哪」，也没有可静态检查的 T1 边界。

## What Changes

- 新增 3 份模块令牌文件：`modules/ai-assistant/tokens.css`(42) · `modules/case-manager/tokens.css`(2) · `modules/workflow/tokens.css`(30)，由 `main.ts` 统一 import
- 从 `shared/styles/tokens.css` 迁出 `.ai-workbench` / `.case-workbench` 两块；从 `shared/styles/workbench-theme.css` 迁出 30 条 `--ac-*`
- 模块/组件级载体 **85 处字面量色值**改为 `var(--color-*)`（模块内 85 处，值零变化）
- T1 文件的字面量色值归零（10 处 `--ac-*` 同步转换）
- 作用域不变：模块令牌仍声明在模块页面根类（`.ai-workbench` / `.case-workbench` / `.workflow-workbench`）
- 零视觉变化：不改任何色值

## 关联文档

- 架构方案：`dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md`（§2 边界与职责 / §3 数据链 / §4 作用域表）
- 前置变更：`openspec/changes/archive/2026-09-15-atomize-shared-design-tokens`（T0 原子与门禁）
- 口径真相源：`openspec/specs/frontend-l0-design-tokens/spec.md`
- 无 PRD/ARCH 编号：纯前端样式层结构重构，无功能与视觉变化。

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `frontend-l0-design-tokens`: **ADDED** 3 条需求——模块令牌按模块落文件 · 模块令牌值 MUST 引用主 token（字面量 = 0）· 模块令牌作用域保持在模块页面根类。

## Impact

- 新增：`modules/{ai-assistant,case-manager,workflow}/tokens.css`
- 修改：`shared/styles/tokens.css`（645→593 行）· `shared/styles/workbench-theme.css`（迁出 30 条）· `main.ts`（+3 import）· 33 个模块/views 组件的载体行（85 处值）
- 不受影响：后端、API 契约、组件模板结构、视觉表现（值等价校验 0 mismatch）
- `views` 无模块级令牌（其载体均为单组件消费），故不新建空文件；如需由调用方补