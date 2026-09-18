## Context

动机见 `proposal.md` - Why。

现状：`NAV_CATEGORIES` 第四组 `ai-tools` 的 `label` 为「AI助手」，组内唯一项为带 `children` 的「AI 助手」。`AppSidebar.vue` 在 `cat.label` 非空时渲染 `.sidebar__group-label`。第一组 `main` 的 `label` 为空，因此仪表盘上方无分组标题。

## Goals / Non-Goals

**Goals:**
- 把 AI 助手父项并入 `main` 组、排在仪表盘之后
- 去掉独立 `ai-tools` 分组，从而去掉「AI助手」标题

**Non-Goals:**
- 不改子路由、Lucide icon、折叠点击跳第一子页的逻辑
- 不改 doodle 侧栏样式

## Decisions

### 1. 只改 `NAV_CATEGORIES`，不改模板条件

- **选择**：把 AI 助手 item 挪进 `main.items`，删除 `ai-tools` 整组
- **理由**：分组标题由 `cat.label` 控制；`main.label` 已是空字符串，不会多出标题
- **备选**：保留分组但把 label 设空 — 会多一层无标题 group 间距，拒绝

## 模块防火墙自检

- 跨 App / 写库 / 前端直连 DB：不涉及
- 仅 L1 `sidebarNavConfig.ts` 与文档行

## Risks / Trade-offs

- [「数据」分组视觉上与 AI 助手相邻] → 可接受；用户明确要求紧挨仪表盘
- [折叠态父项仍跳第一子页] → 行为不变，不在本变更范围
