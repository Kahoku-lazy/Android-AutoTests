---
name: css-block-comment-star-slash
description: CSS 块注释内禁止出现字面量 */，否则会提前闭合并把后续 :root 令牌全部吃掉
metadata:
  node_type: memory
  type: feedback
  project: project
---

# CSS 块注释禁嵌 `*/`

**Why:** 2026-08-21 登录页「渐变 + 白纸卡 + 手写标题」全部消失。DOM 结构完好，但 `.hero__content` 无边框、背景透明、标题变成 Times New Roman。根因不是 LoginView，而是 `frontend/src/shared/styles/tokens.css` 文件头块注释写了：

```
--app-duration-*/--app-ease/--app-spring
--app-border-*/--app-highlight
```

CSS 解析器在第一处 `*/` 结束注释，后面的 `:root { --ink: ... }` 变成非法规则，整表令牌不生效。`var(--ink)` 等全部解析失败。

**How to apply:**

1. 写/改任何 `/* ... */`（尤其 `tokens.css` 头部）时，注释正文里不要出现 `*/`。列举 token 用顿号或 `、`，不要用 `/` 拼接。
2. 全站无样式、`--ink` 为空、字体退回 Times New Roman → 先查 `tokens.css` 注释是否提前闭合，不要先改登录页布局。
3. 改完 `tokens.css` 必须在浏览器确认 `document.documentElement` 上 `--ink` 有值。

落点：`frontend/AGENTS.md` §2 · `.claude/rules/frontend.md` 样式工程约束。
