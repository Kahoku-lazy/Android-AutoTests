## 1. 模板接线

- [ ] 1.1 `frontend/src/modules/bug-manager/components/BugDetailDrawer.vue` 引入 `splitErrorDetail`，加 `const errorLines = computed(() => splitErrorDetail(props.bug?.detail || props.bug?.detail_preview || ""))`。验证：`npm run typecheck` 通过；组件内无正则、无 inline 解析逻辑（规格：MUST NOT 在组件里写解析）。
- [ ] 1.2 把「错误内容」段的 `<pre class="bug-detail__body">{{ … }}</pre>` 改为 `<div class="bug-detail__body">` + `v-for` 的 `<p class="bug-detail__line">`；有 `label` 时行首渲染 `<strong class="bug-detail__line-key">{{ line.label }}</strong>` 再接 `line.text`。验证：容器类名仍是 `bug-detail__body`（底色/描边/硬影/`max-height` 不变）。
- [ ] 1.3 文本为空时保留「—」占位（`errorLines.length === 0` 分支）。验证：挂载一个 `detail` 为空的单据，页面上出现「—」且没有空的 `.bug-detail__line`。

## 2. 用例

- [ ] 2.1 新建 `frontend/tests/bug-manager/p0/bug-detail-error-lines.spec.ts`，覆盖：① 两行文本 → `.bug-detail__line` 数为 2 且 `.bug-detail__line-key` 文本为「来源任务：」；② 无冒号的行整行当正文、`label` 为空；③ 缩进行保留前导空白（断言文本以空格开头）。验证：`npx vitest run tests/bug-manager/p0/bug-detail-error-lines.spec.ts` 全绿。
- [ ] 2.2 跑既有 `tests/bug-manager/p0/bug-detail-steps.spec.ts`，确认 `toContain("来源任务：#18")` 仍成立（逐行渲染后 `text()` 会拼接）。验证：该文件全绿；若失败，说明拼接假设不成立，需改用结构断言并记录原因。
- [ ] 2.3 保留 `tests/bug-manager/p0/errorDetail.spec.ts`（helper 的 PA 级用例）不动。验证：该文件全绿，`git diff` 不含它。

## 3. 门禁与关单

- [ ] 3.1 `npm run typecheck`、`npm run build`、`npm run lint:styles`、`npm run test` 四条 exit 0。验证：记录退出码。
- [ ] 3.2 视觉口径核对：在浏览器打开任意 BUG 单详情（无失败快照者），确认「错误内容」块底色、描边、4px 硬影与改前一致，标签加粗但行高不变。验证：截图对照或目视确认，写入关单汇报。
- [ ] 3.3 关单汇报写明：本单只让「无失败快照 → 退回原文」这一支的标签加粗生效；有快照时仍显示四问（该分支不渲染 error detail）。随后归档（`skip_specs: true`）。
