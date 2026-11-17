# 设计：模型配置页分页

## Context

`model-configs.vue` 的 `visibleConfigs` 已是「全量 + 前端关键字过滤」的结果，直接喂 `AppTable`。表格已 `table-layout="fixed"`，五列宽度合计 960px，容器约 1130px。底部那条横向滚动条来自 `el-scrollbar__wrap`：它的 `scrollWidth` 比 `clientWidth` 大 10px（`<table>` 与 wrap 的取整差），而 EP 自绘的横向条 `display: none`，于是浏览器把原生横条画了出来。

## Goals / Non-Goals

**Goals**：每页 10 条、翻页键常驻可见；计数只出现一次；表底不再有无用的横向滚动条。

**Non-Goals**：不改接口分页；不改列结构、抽屉表单与搜索行为（搜索仍是前端过滤）。

## Decisions

### D1 前端切片，分页接在过滤之后

`pagedConfigs = visibleConfigs.slice(...)`——先过滤再分页，所以搜索结果也会分页，页码文案统计的是过滤后的条数。`OPS_MODEL_PAGE_SIZE = 10` 落在 `constants.ts`，与用户管理、Agent 配置同口径。

### D2 关键字变化回第 1 页；删除后夹回末页

`watch(keyword)` 里 `page = 1`，避免停在过滤后不存在的页码。`load()` 末尾把 `page` 夹到 `max(1, ceil(n / 10))`，删除最后一条不会停在空白页。

### D3 横向滚动条用 `overflow-x: hidden`，不加宽度 hack

固定布局下列宽由 EP 计算、内容超长走 tooltip，横向滚动本来就无意义。EP 自绘的 `.el-scrollbar__bar.is-horizontal` 实测 `display: none`，所以隐藏原生横条不会丢掉可达内容。

```css
.ops-workbench :deep(.el-table .el-scrollbar__wrap) { overflow-x: hidden !important; }
```

放模块皮肤（`table.style.css`）而不是单页，三张运营表共享同一口径。

### D4 间距与另外两页统一

`.ops-section { gap: var(--app-space-md) }`（scoped 覆盖），搜索行 / 翻页行 / 表格之间 16px，与 Agent 配置页一致。

## Risks / Trade-offs

- [窄屏下横向滚动被禁用]：`table-layout: fixed` 会把列压缩，不会产生需要滚动的溢出；确实压不下时由 tooltip 兜底。
- [搜索 + 分页叠加]：用户可能先搜再翻页，页码只统计命中项——与用户管理（服务端过滤）语义一致。

## Migration Plan

纯前端。回退 = 还原 `model-configs.vue` / `constants.ts` / `table.style.css` 并回滚本 spec 条目。

## Open Questions

无。
