## Context

动机见 proposal.md - Why。当前实现事实：

- `BugDetailDrawer.vue:151-154`：无失败步骤时 `<pre class="bug-detail__body">{{ bug.detail || bug.detail_preview || "—" }}</pre>` 直出。
- `BugDetailDrawer.style.css:122-144`：卡片皮肤在 `.bug-detail__body`；行级 `.bug-detail__line`（`white-space: pre-wrap` + `overflow-wrap: anywhere`）与 `.bug-detail__line-key`（`var(--app-font-weight-bold)`）已入库但无模板消费。
- `helpers/errorDetail.ts::splitErrorDetail(text)` 返回 `{label, text}[]`：label 为含冒号的行首标签（无标签时空串），text 为冒号后正文或整行原文；前导空白保留；`""` 输入返回 `[]`。
- 仓库约束：组件只做 UI 渲染与事件绑定，解析 MUST 走模块内纯函数（bug-manager/AGENTS.md 与主规格一致）；样式不得新增裸字面量。

## Goals / Non-Goals

**Goals:**

- 错误内容分支逐行渲染，行首标签 700 字重、正文 400，字号与卡片几何不变。
- 三条规格场景（字段名加粗 / 堆栈行整行正文 / URL 不拆标签）有组件级测试兜底。

**Non-Goals:**

- 不改 `splitErrorDetail` 判定规则与其既有单测。
- 不改失败步骤（四问）分支、抽屉其它区块、状态操作。
- 不新增样式令牌或改卡片皮肤；不动后端。

## Decisions

1. **容器 `<pre>` → `<div class="bug-detail__body">`，行用 `<p class="bug-detail__line">`。**
   理由：行级 `pre-wrap` 已在 CSS 就位，`<p>` 逐行与归档设计一致；卡片皮肤类留在容器上，几何零变化。
   备选：保留 `<pre>` 内嵌 `<span>`——被否，`<pre>` 内块级行结构不自然，且与已入库的行级 CSS 不匹配。
2. **标签渲染：`line.label` 非空才出 `<span class="bug-detail__line-key">{{ line.label }}</span>`，其后紧跟 `{{ line.text }}`。**
   理由：无标签行（堆栈 / 纯文本）整行正文，不产生空 span；文本插值天然转义，不引入 `v-html`。
3. **空文本占位：`splitErrorDetail` 结果为 `[]` 时渲染单行「—」。**
   理由：保持现状 `bug.detail || bug.detail_preview || "—"` 的占位语义。
4. **测试落点：`tests/bug-manager/p0/BugDetailDrawer.spec.ts` 新增**，挂载抽屉（`failure_steps` 缺省）断言：标签 span 文本与存在性、堆栈行无 span、URL 行无 span、空 detail 出「—」。Element Plus 按既有 bug-manager spec 的 stub 口径处理。
   理由：现有 `errorDetail.spec.ts` 只测纯函数，接线回归必须发生在组件层，防止再次"函数在、接线丢"。

## 模块防火墙自检

- 仅前端 bug-manager 模块内改动：组件 import 模块内 `helpers/errorDetail`，无新增跨模块依赖。
- 不新增 HTTP 调用，不触碰 `api.ts` 出口；无数据库 / 仪表盘写操作。
- 不触碰任何 AGENTS 红线条款；样式复用既有令牌类，无新字面量。

## Risks / Trade-offs

- [长行 / 多行文本折行行为与旧 `<pre>` 有细微差异] → 行级 `pre-wrap + overflow-wrap: anywhere` 已覆盖；测试含堆栈缩进行断言前导空白保留。
- [误伤四问分支] → 只改 `v-else` 分支；四问分支模板不动。
- [样式门禁新增违规] → 不新增任何字面量，跑 `npm run lint:styles` / `lint:lines` 验证。

## Migration Plan

纯前端模板变更，随 PR 合并即生效；回滚 = revert 该提交。无数据迁移、无接口变更。
