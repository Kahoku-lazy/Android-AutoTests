## Context

- `helpers/errorDetail.ts` 已实现 `splitErrorDetail(text): ErrorDetailLine[]`，规则与规格逐条对应：行首 1–12 个「非空白、非冒号、非斜杠」字符 + 一个中英冒号；冒号后紧跟 `//` 视为 URL 协议段、整行当正文；无标签行 `label` 为空串、`text` 为整行原文。
- `BugDetailDrawer.style.css` 已有：`.bug-detail__body`（浅红渐变 + 墨色硬影 + 46vh 滚动容器）、`.bug-detail__line`（`white-space: pre-wrap` + `overflow-wrap: anywhere`）、`.bug-detail__line-key`（`font-weight: var(--app-font-weight-bold)`）。
- 现有 P0 用例 `bug-detail-steps.spec.ts` 断言 `plain.text()).toContain("来源任务：#18")`；逐行渲染后 `wrapper.text()` 会把标签与正文拼回去，该断言仍然成立（这是本单不改它的依据，但要跑一遍确认）。
- 模板现状（第 151–154 行）：无失败步骤快照时渲染 `<pre class="bug-detail__body">`，有快照时渲染四问、根本不显示 error detail。

## Goals / Non-Goals

**Goals:**

1. 让 `bug-ticket-management` 的 MUST 有可观察的落点：错误内容逐行渲染、行首标签加粗。
2. 不动视觉：底色、描边、硬影、行高、字号一律沿用既有声明。
3. 补 3 条能抓住「接线是否真发生」的组件用例。

**Non-Goals:**

- 不改 `splitErrorDetail` 的判定规则（规格正文说了算，改它要走 spec delta）。
- 不改「有快照时显示四问、不显示原文」的现有分支逻辑。
- 不改 BUG 列表页的 `detail_preview` 截断行为。

## Decisions

**D1：解析放在 `computed`，不在模板里写逻辑。**
规格要求「MUST NOT 在组件里写解析逻辑」。`const errorLines = computed(...)` 只做取值与兜底，解析仍由 helper 完成，符合「组件只渲染」。

**D2：容器 `<pre>` 换 `<div>`，折行责任下沉到 `.bug-detail__line`。**
`<pre>` 自带 `white-space: pre`，套 `v-for` 的 `<p>` 后语义混乱且会双重保留空白；既有 `.bug-detail__line` 已声明 `pre-wrap`，正好承接「保留前导空白与折行」这条规格要求。容器类名不变，故底色/描边/硬影/`max-height` 全部不动。

**D3：标签用 `<strong>` + 既有 `.bug-detail__line-key`。**
该 class 已在库、无字号声明，只加粗，满足「加粗 MUST NOT 改变行高」。不用 `<b>`（语义弱）也不用 inline style（破坏令牌口径）。

**D4：空文本兜底保持「—」，不渲染空行。**
`text` 为空串时 `splitErrorDetail` 返回 `[]`，若直接 `v-for` 会得到空容器；故模板保留 `v-if="errorLines.length"`，否则显示「—」。与现状 `<pre>—</pre>` 的可见结果一致。

**D5：用例断言「结构 + 文本」两层，而不是只断言文本。**
只断言 `wrapper.text()` 无法区分「接线成功」与「仍用 `<pre>` 直出」——两者文本相同。故必须断言 `.bug-detail__line` 数量 ≥ 2、且 `.bug-detail__line-key` 的文本恰为「来源任务：」。

## 模块防火墙自检

- **跨 App import**：不涉及，只动 `frontend/src/modules/bug-manager/`。
- **禁跨层依赖**：组件只依赖本模块 helper 与 Vue，无新增跨模块 import。
- **写库收敛**：不涉及写操作（本段为只读展示）。
- **前端不直连数据库**：维持。
- **仪表盘只读**：不涉及。

## Risks / Trade-offs

- **[逐行渲染与 `<pre>` 的空白处理差异导致长堆栈对齐变化]** → `.bug-detail__line` 用 `pre-wrap` 保留前导空白；用例里加一条「缩进行保留前导空白」的断言。
- **[`wrapper.text()` 类断言在改造后仍通过，给人「没改」的错觉]** → D5 要求结构断言，单靠文本不足以判绿。
- **[有失败快照时该段不渲染，接线后仍看不到]** → 保持现状分支（有快照看四问），在关单说明：加粗只作用于「无快照退回原文」这一支。
