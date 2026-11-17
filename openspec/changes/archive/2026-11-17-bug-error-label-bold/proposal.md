# BUG 单详情：错误内容行首标签加粗

## Why

错误内容卡里的正文是一整段等宽文本，`来源任务：`、`任务状态：`、`失败原因：`、`任务结果：` 这些字段名与后面的值同字重同色，扫读时得逐行读到冒号才知道哪段是字段、哪段是值。需求方要求把字段名加粗，与正文分开。

## What Changes

- 错误正文从「一个 `<pre>` 整段」改成「一行一段」，行首「标签：」渲染为加粗（`--app-font-weight-bold`）的 `span`，冒号后的值保持常规字重。
- 标签识别规则落到纯函数 `helpers/errorDetail.ts::splitErrorDetail`：行首不含空白/冒号/斜杠、最长 12 个字符 + 一个中英冒号才算标签；冒号后紧跟 `//` 的按 URL 处理，整行当正文。
- 没有标签的行（堆栈、缩进片段）整行当正文，保持等宽与缩进不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：新增「错误内容行首标签加粗」要求。

## Impact

- 前端 `bug-manager`：新增 `helpers/errorDetail.ts`；`components/BugDetailDrawer.vue` 模板与 `BugDetailDrawer.style.css` 各改一处。
- 新增单测 `tests/bug-manager/p0/errorDetail.spec.ts`（5 例）。
- 卡片几何、字号、颜色均不变；不动接口。
