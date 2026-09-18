## Why

令牌分层（变更 A/B）已收敛，但**样式资产卫生**仍是敞口：`ChatView.css` 全仓 0 引用却留在源码树（`--chat-*` 一并成死数据）；`views/shared/` 与平台 `shared/` 命名撞车，同一份认证样式被 3 个组件用非 scoped `@import` 注入 5 次；`DoodleNote.vue` 有 7 处 `var(--x, #字面量)` 双真相源兜底 —— 兜底与令牌一旦漂移就会静默改色。

## What Changes

- `modules/ai-assistant/ChatView.css`（0 引用、0 `--chat-*` 引用）移出源码树，隔离到 `temps/quarantine/`（可恢复，不直接删除）
- `views/shared/` → **`views/styles/`**，消除与 `shared/` 的命名撞车；5 处 `@import` 路径同步更新
- `DoodleNote.vue` 的 **7 处** `var(--x, #字面量)` 兜底改为 `var(--x)`（逐个确认被引用变量在 T0/兼容层中存在）
- 登记未完成项（不属本变更，另立 C-2）：模板/属性/JS 侧 400+ 处令牌字符串的边界溯源 · 23 处跨仓 `var(--x, #lit)` 兜底 · `workflow/index.vue` 非 scoped 块的补充理由注释

## 关联文档

- 架构方案：`dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md`（§3.1 溯源判定树 / §10 顺带清理清单）
- 前置变更：`2026-09-15-atomize-shared-design-tokens` · `2026-09-15-module-token-files`
- 无 PRD/ARCH 编号：样式资产卫生治理，无功能与视觉变化。

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `frontend-l0-design-tokens`: **ADDED** 2 条需求——无引用样式文件 MUST NOT 留在源码树 · 共享样式目录唯一（`shared/` 命名不得被 views 复用）。

## Impact

- 删除（隔离）：`modules/ai-assistant/ChatView.css`
- 移动：`views/shared/{login-card,auth-form-card}.css` → `views/styles/`；改 3 个组件的 5 处 `@import`
- 改值：`shared/components/DoodleNote.vue` 7 处兜底
- 不受影响：后端、API、组件结构、视觉（引用与值均已校验）