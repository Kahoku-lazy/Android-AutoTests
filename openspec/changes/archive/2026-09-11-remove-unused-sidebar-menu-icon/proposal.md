## Why

平台侧边栏的 `AnimatedMenuIcon.vue`（247 行）在 V6 glassmorphism 主题迁移（commit `cc721d74`）中，唯一渲染点 `<AnimatedMenuIcon :name="item.icon" :size="20" :active="isActive(item.path)" />` 已被删除（图标改走 lucide `<i :data-lucide>`），但 `AppSidebar.vue` 的 import 与 `frontend/AGENTS.md` 的"侧边栏代码文件"清单都还留着它。结果：一个 247 行组件既无渲染、也无测试或样式引用，却仍被文档描述为侧边栏的构成部分，使"侧边栏由哪些文件构成"这一事实失真。

## What Changes

- 删除 `frontend/src/shared/components/AnimatedMenuIcon.vue`（247 行，零渲染点）
- 移除 `frontend/src/shared/components/AppSidebar.vue` 中的死 import（`import AnimatedMenuIcon from './AnimatedMenuIcon.vue'`）
- `frontend/AGENTS.md` 的"平台前端侧边栏代码文件"清单移除该行（4 条 → 3 条），使文档与渲染事实一致
- **无 BREAKING**：无渲染点、无 props 传入方、无测试/样式引用，可见行为零变化

## 关联文档

- 无 PRD/ARCH 关联：纯死代码清理 + 文档与代码对齐，无需求级行为变化
- 成因判据来自 git 历史（`cc721d74` 删除渲染点、保留 import）

> 记录时点：改动已先行完成（用户选择方案 A），本变更为实施后补录，tasks.md 逐条附验证证据

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯删除零引用组件与文档对齐，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 删除：`frontend/src/shared/components/AnimatedMenuIcon.vue`
- 修改：`frontend/src/shared/components/AppSidebar.vue`（去 import）、`frontend/AGENTS.md`（清单 4→3）
- 产品行为零改动：侧边栏动画由仍在使用的 `AnimatedMascot`（`AppSidebar.vue:11,227`）承担
- 仍登记未处理（文档同步另行安排）：`dev_docs/项目笔记/1.md:464` 表格仍列出该文件
