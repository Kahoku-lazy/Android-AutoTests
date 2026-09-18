## Context

见 `proposal.md` Why。现行契约把 `WorkbenchCrumbs` 挂在 `WorkbenchHeader` 的 `#nav`，`frontend-l2-page-region` 明确禁止 `.doc-body` 顶部再放回退条。用户指定全量子页改放置区。元素定位 `ProjectWorkspace.vue` 已按目标布局改过，其余 9 个页面仍用 `#nav`。`CaseFileSheet.vue` 同时使用 `#nav` 与 `#actions`。

## Goals / Non-Goals

**Goals:**

- 统一挂载：面包屑作为 `.doc-body` 的第一个可见子节点（或等价的顶部插槽），加载/错误态也能回退。
- 页头在这些页面上不再渲染 `#nav`；无消费方后删除槽位。
- 水平内边距仍与页头共用 `--app-space-lg`（`.doc-body` 已有同等 padding）。
- 固定视口页（`.doc-page--fixed`）目录树/表格仍占满剩余高度：面包屑 `flex-shrink: 0`，主体 `flex: 1 1 0; min-height: 0`。

**Non-Goals:**

- 不改祖先链文案、路由、`WorkbenchCrumbs` 视觉令牌。
- 不把 `#actions` 迁出页头。
- 不改 L0/L1、侧栏、页面流画布页头。
- 不新增第二套页头组件。

## Decisions

1. **页面各自把 Crumbs 挪进 `.doc-body`，不新增布局包装组件。** 子页骨架已有 `.doc-body`；再抽 `WorkbenchSubpage` 会扩大共享面。备选：共享 layout 组件 —— 否决，改动面大于收益。
2. **加载/错误/空态也渲染 Crumbs。** 参考已落地的元素项目工作台：单一 `.doc-body` + 顶部 Crumbs + 下方主区三态。备选：仅成功态显示 —— 否决，错误时无法按可见回退离开。
3. **保留 `#actions`。** 用户本轮范围是 `#nav` 面包屑；用例文件页保存/新建行仍属页头操作。备选：页头绝对只留标题、按钮进正文 —— 超出本变更。
4. **删除空闲 `#nav`。** 符合「无消费方不得保留声明」。备选：留槽给以后 —— 否决，与 L2 零消费规则冲突。
5. **报告三页（非 `--fixed`）只需把 Crumbs 放到现有 `.doc-body` 顶部。** 它们走页面整体滚动，不必套 `*-main` flex 壳。固定高度树/表格页才需要主区 flex 填充。

## 模块防火墙自检

- 跨 App import：不涉及后端。
- 禁止跨 App import service/runner/consumer/state_machine：不涉及。
- INSERT/UPDATE/DELETE 收敛到 api.py：不涉及写库。
- 前端不直连数据库：仍走既有 `djangoClient`；本变更无新 HTTP。

## Risks / Trade-offs

- [固定视口页高度被面包屑吃掉导致树/表裁剪] → 主区 `flex: 1 1 0; min-height: 0; overflow: hidden`，树/表内部滚动；对照已改的 locator 工作台。
- [报告页 `.doc-body` 已有 top-bar，面包屑叠两行] → Crumbs 作为第一子节点，既有 summary pill 仍在下方，不合并、不删除。
- [ErrorState 原先在 `.doc-body` 外] → 收进 `.doc-body` 主区，保证 Crumbs 始终在同一滚动/固定壳内。
- [与旧 spec 冲突直到 archive] → 本变更 delta 显式 REMOVED 旧需求；apply 前以本 change 的 specs 为准。

## Migration Plan

1. 按任务清单逐页迁移；locator 项目工作台视为已完成，仅回归。
2. 最后删除 `WorkbenchHeader` `#nav`。
3. 回滚：把 Crumbs 移回 `#nav` 并恢复槽位（无数据迁移）。
