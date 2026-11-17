# 设计：标签回到 14px

## Context

`.bug-badge, .bug-status { font-size: var(--app-size-md); }` —— 上一变更按"头部行整行 16"统一了。标签是 `inline-flex` + `padding: 2px var(--app-space-xs)` + `1.5px` 描边，16px 时两个标签的横向占位明显大于编号，视觉重量反超 `BUG-0066`。

## Goals / Non-Goals

**Goals**：编号仍是最先被读到的身份，标签退成附注；抽屉里仍只有 16 / 14 两档。

**Non-Goals**：不改标签颜色、描边、内边距；不改编号与标题；不改错误内容卡。

## Decisions

### D1 只回退标签，不回退整行

`--app-size-sm`（14px）是抽屉的正文档。头部行由"编号 16 + 标签 14"组成仍是两档内，且与元信息块同档，标签读起来是"注释"而不是第二个标题。

### D2 不改内边距与描边

16 → 14 会让标签自然收窄，`padding: 2px 8px` 与 `1.5px` 描边在 14px 下正好是列表页标签的比例；动内边距会把两个页面的标签比例拉开。

## Risks / Trade-offs

- [编号与标签重新出现字号差] → 这正是需求方要的层次；差别只有 2px，不会回到上一版"12 vs 14"那种割裂。

## Migration Plan

一处 `font-size` 回退，回退 = 改回 `--app-size-md` 并同步 spec。

## Open Questions

无。
