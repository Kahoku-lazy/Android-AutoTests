## Why

`openspec/specs/bug-ticket-management/spec.md:328` 是一条**活着的 MUST**：BUG 单「错误内容」的行首标签识别「MUST 走模块内纯函数（`helpers/errorDetail.ts::splitErrorDetail`），MUST NOT 在组件里写解析逻辑」。

实际情况是**半套功能**：纯函数 `splitErrorDetail` 存在（39 行）、P0 用例存在（5 条）、连 `.bug-detail__line` / `.bug-detail__line-key` 的 CSS 都已进库——但 `BugDetailDrawer.vue:153` 仍是 `<pre class="bug-detail__body">{{ bug.detail || bug.detail_preview || "—" }}</pre>` 直出，全文件没有一次 `splitErrorDetail` 调用。归档变更 `2026-11-17-bug-error-label-bold` 只落地了 helper 与 CSS，模板接线从未入库。

后果是双向的：规格声明了一个用户看不见的效果；而 helper 与那 5 条 P0 用例在为一个没人调用的函数持续跑绿。需求方裁决：**补接线**，让实现满足既有 MUST。

## What Changes

- `modules/bug-manager/components/BugDetailDrawer.vue` 的「错误内容」段由 `<pre>` 直出改为**逐行渲染**：
  - 通过 `computed` 调 `splitErrorDetail(bug.detail || bug.detail_preview || "")` 取行；
  - 每行一个 `<p class="bug-detail__line">`，有标签时行首标签包进 `<strong class="bug-detail__line-key">`，其余为正文；
  - 文本为空时仍显示「—」占位（与现状一致）。
- **不改** `helpers/errorDetail.ts` 的判定规则（那是规格正文，本单只接线）。
- **不改** 卡片底色、描边、硬影与行高（规格明确：加粗 MUST NOT 改变这些）；仅把容器标签从 `<pre>` 换成 `<div>`，靠既有 `.bug-detail__line { white-space: pre-wrap }` 保折行与前导空白。
- 新增组件级用例：① 有标签的行，标签文本落在 `.bug-detail__line-key` 里且加粗；② 无标签的行整行当正文；③ 空文本显示「—」。
- **不动**：`splitErrorDetail` 的 PA 级用例（保留）、BUG 单其余字段与操作按钮。

## 关联文档

- 需求：`openspec/specs/bug-ticket-management/spec.md` 的「错误内容行首标签加粗」要求（原文已规定该行为，本单不改变 Requirement 文本）。
- 前置：归档变更 `2026-11-17-bug-error-label-bold`（只落地 helper + CSS，模板未接）。
- 发现来源：2026-11-19 前端审计 A1 项、2026-11-24 复杂度体检。
- **`.openspec.yaml` 设 `skip_specs: true`**：本单是「把代码修到规格已有要求」，规格不新增、不修改任何 Requirement。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 规格已要求该行为且不需要改动，故 `skip_specs: true`。若实现过程中发现规格正文与实际想要的效果不符，另开 spec delta 单，不在本单偷偷改。）

## Impact

- **修改**：`frontend/src/modules/bug-manager/components/BugDetailDrawer.vue`（模板 + 一个 `computed` + import）。
- **新增**：`frontend/tests/bug-manager/p0/bug-detail-error-lines.spec.ts`（3 条用例）。
- **不动**：`helpers/errorDetail.ts`、`BugDetailDrawer.style.css`（所需类已存在）、BUG 单接口、后端与引擎、其它模块。
- **门禁**：`npm run typecheck` + `npm run build` + `npm run lint:styles` + `npm run test`。
