# BUG 单详情：「错误内容」改成红色渐变卡片

## Why

详情抽屉里「错误内容」那段现在只是一块浅底 `<pre>`：1.5px 的近纸色描边几乎看不见、白底与上面的元信息块同色、四周无影，读起来像正文的延续而不是「一段独立贴出来的错误记录」。需求方要求把它做成卡片，底色用红色渐变（错误语义），卡内文字 14px。

## What Changes

- `.bug-detail__body` 从「浅底 + 近纸色边」改成卡片：`1.5px solid var(--app-border-strong)` 描边、`--app-radius-md` 圆角、`4px 4px 0 0 var(--ink)` 硬偏移影。
- 填充改为浅红渐变 `--comp-bug-error-fill`：135° 斜向，标记红 18% → 6%（浓度刻意压低，正文压在上面不抢字）。
- 卡内文字字号 = 14px（`--app-size-sm`，上一变更是 12 → 14，本次保持）。
- 元信息块（关联任务 / 任务状态 / 创建时间 / 解决时间）与两个处理按键不动。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：新增「BUG 单详情错误内容卡」要求。

## Impact

- 前端 `bug-manager`：`components/BugDetailDrawer.style.css`（一个规则块）。
- 令牌：`shared/styles/tokens.css` 新增 `--comp-bug-error-fill`（两端 `color-mix` 自 `--color-red-69`，不新增颜色原子）。
- 样式登记：`.agents/skills/doodle-craft/references/tokens.md` 与 `references/components/cards.md` 记录这条已批准的渐变卡。
- 不动模板、不动接口。
