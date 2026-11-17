# 设计：抽屉字号两档

## Context

`components/BugDetailDrawer.style.css` 现在给五处不同的字号：

| 元素 | 现值 | 令牌 |
| --- | --- | --- |
| `.bug-detail__no`（编号） | 14px | `--app-size-sm` |
| `.bug-badge` / `.bug-status`（分类 / 状态标签） | 12px | `--app-size-xs` |
| `.bug-detail__title`（单据标题） | 24px | `--app-size-xl` |
| `.bug-detail__subtitle`（「错误内容」） | 14px | `--app-size-sm` |
| `.bug-detail__body`（错误正文） | 12px | `--app-size-xs` |

抽屉标题「BUG 单详情」由 EP 头部给 16px，按键由 `DoodleBtn` 自持 14px。

## Goals / Non-Goals

**Goals**：抽屉内只剩两档字号——信息层级由 16（头部行 / 标题 / 小节标题）与 14（其余）区分，不再出现 12px 标签与 24px 标题。

**Non-Goals**：不改间距、不改颜色、不改标签边框与配色；不动抽屉标题与按键；不改列表表格的字号（那是另一条已归档要求 `BUG 表格的留白与可读字号`）。

## Decisions

### D1 用既有刻度令牌，不写字面量

16px = `--app-size-md`（"卡片标题、表单标签、模块标题"档），14px = `--app-size-sm`（UI 正文档）。符合字号只取 7 档刻度的硬规则，且 `lint:styles` 的字号下限（≥12px）继续满足。

### D2 头部整行同字号，标签跟着编号走

标签原本比编号小两档，在 16px 的一行里会显得"贴上去的补丁"。需求方明确"这一行都是"，故 `.bug-badge` / `.bug-status` 一并提到 16px；标签的内边距与 1.5px 描边不动，靠行内 `gap` 维持呼吸。

### D3 正文回落到正文档

错误正文是等宽 `<pre>`，12px 在高分屏上偏小；提到 14px 与元信息块同档，同时保留 `max-height: 46vh` 与 `white-space: pre-wrap`。

## Risks / Trade-offs

- [16px 的标题在 520px 抽屉里可能显得平] → 层级改由**字重**（标题 700 / 小节标题 800 / 正文 400）与间距承担，已在截图核对。
- [标签变大后头部行变高] → 头部是 `flex-wrap` 行，宽度不足时换行，不会挤压标题。

## Migration Plan

纯样式改动，回退 = 五处 `font-size` 还原。

## Open Questions

无（"这一行都是 16" 已确认包含分类与状态标签）。
