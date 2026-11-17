# 设计：标签加粗的表达方式

## Context

`.bug-detail__body` 现在是 `<pre>{{ bug.detail || bug.detail_preview || "—" }}</pre>`，正文是后端给的自由文本（`来源任务：…\n任务状态：failed\n…`，也可能是整段堆栈）。要用 CSS 只加粗「冒号前那一段」做不到——文本节点没有可选择的边界。

## Goals / Non-Goals

**Goals**：字段名加粗、值不变；堆栈/缩进/超长串的换行行为与现在一致；不做任何业务解释。

**Non-Goals**：不改卡片的底色/描边/影/字号；不解析含义（不重算任务状态、不判断成功失败）；不引入富文本或 markdown 渲染。

## Decisions

### D1 用「一行一段 + 行首 span」拆，不用富文本渲染

模板从 `<pre>` 改成 `<div>` 里 `v-for` 出 `<p class="bug-detail__line">`，行首标签放 `<span class="bug-detail__line-key">`。行级 `white-space: pre-wrap` 接手原来 `<pre>` 的缩进与折行，所以堆栈行的前导空格不会丢。

### D2 解析下沉到 `helpers/errorDetail.ts`（纯函数 + 单测）

组件只管渲染（`frontend/AGENTS.md` 硬规范）。识别规则写死在该模块：

```ts
const LABEL_RE = /^([^\s：:/]{1,12}[：:])[ \t]?(.*)$/
```

- 不含空白：`at run (runner.js:12)` 这类堆栈不会被当成标签；
- 不含斜杠 + 冒号后 `//` 排除：`https://…` 不被拆成 `https:` + `//…`；
- 中英冒号都认；冒号后的单个空格不并入值，中文全角冒号后面的文本原样保留。

### D3 字重走令牌，不写字面量

`font-weight: var(--app-font-weight-bold)`（700）。标签仍是 14px 等宽，与值同字号——分开靠字重，不再动字号（抽屉已收成 16/14 两档）。

## Risks / Trade-offs

- [自由文本里恰好出现「12 字内 + 冒号」的行会被误判成标签] → 误判的代价只是那几个字变粗；规则里已排除 URL 与堆栈两种最常见误判。
- [`<pre>` → `<p>` 后行高可能变] → 行级 `margin: 0` + 容器 `line-height` 保持，实测行高一致。

## Migration Plan

新增 helper 与单测；模板与样式各一处改动。回退 = 恢复 `<pre>` 单段渲染。

## Open Questions

无。
