# 设计：Agent 配置页的分页与间距

## Context

`agents.vue` 用 `listOpsAgents()` 一次取回全部 Agent（`GET /api/ai/roles/` 返回数组），直接喂 `AppTable`；顶部只有一行 `.doc-section__header`（「共 N 条」+「新建配置」），其 `margin-bottom` 是 4px（`style.css` 全局）。运营另外两页（用户管理、模型配置）已改成「控制区 + 固定条数」。

## Goals / Non-Goals

**Goals**：翻页键常驻且永远可见；每页固定 10 条；控制区与表格之间留出可读的间距。

**Non-Goals**：不给 `/api/ai/roles/` 加分页参数（数据量与接口契约都不需要）；不改表格列、抽屉表单与增删改逻辑。

## Decisions

### D1 前端切片，不碰接口

`OPS_AGENT_PAGE_SIZE = 10`（`constants.ts`），`pagedAgents = agents.slice(...)`。接口保持全量返回——运营配置的 Agent 是十几个量级，加服务端分页只会让「删除后夹回末页」这种逻辑分散到两端。

### D2 翻页键常驻，只有一页也可见（置灰）

与用户管理同口径：`第 X / Y 页 · 共 N 条` + `上一页 / 下一页`，`totalPages = max(1, ceil(n / 10))`，首 / 末页对应键 `disabled`。不采用「多页才显示」——那样页面会因数据量不同在两个版式之间跳。

### D3 间距靠分区间距，不写死 margin

`.ops-section` 在运营模块骨架里是 `gap: 8px`。本页用 scoped 覆盖成 `--app-space-md`（16px），于是「新建配置行 → 翻页行 → 表格」三段都拉开；按键与表头的实际距离由 4px 增到约 69px（含翻页行高度）。改的是分区间距而不是给按钮加 `margin-bottom`——后者会在窄屏换行时变成多余的空白。

### D4 引入模块骨架样式，顺带清死代码

`agents.vue` 原本没引 `index.style.css`，靠 `.doc-section__header` 的全局样式撑着；这次要复用 `.ops-toolbar` / `.ops-controls` / `.ops-page-info` / `.ops-page-nav`，所以引入模块骨架。随之 `.ops-count` 在三个页面都已无消费方，删除该规则。

## Risks / Trade-offs

- [表格仍是 `.doc-section` 带框 + 表纸橙影（双层）]：与用户管理/模型配置页不同——本次只处理分页与间距，表纸统一另开改动。
- [删除后页码可能越界]：`load()` 里把 `page` 夹回末页，避免停在空白页。

## Migration Plan

纯前端。回退 = 还原 `agents.vue` / `constants.ts` / `index.style.css` 并删掉 `ops-agent-config` spec。

## Open Questions

无。
