## 1. 渲染接线

- [ ] 1.1 `BugDetailDrawer.vue` 错误内容分支（`v-else`）：引入 `splitErrorDetail`，`<pre>` 改 `<div class="bug-detail__body">` + 逐行 `<p class="bug-detail__line">`，`line.label` 非空时前置 `<span class="bug-detail__line-key">`；拆行结果为空时渲染单行「—」。验证：`npm run typecheck` 与 `npm run lint` 通过，四问分支模板零改动（diff 只落在错误内容分支与脚本引入）。
- [ ] 1.2 样式核对：只复用既有 `.bug-detail__body` / `.bug-detail__line` / `.bug-detail__line-key`，不新增字面量。验证：`npm run lint:styles` 与 `npm run lint:lines` 通过。

## 2. 组件级测试

- [ ] 2.1 新增 `frontend/tests/bug-manager/p0/BugDetailDrawer.spec.ts`（挂载口径参照同目录 `bug-detail-steps.spec.ts`）：断言 ①「来源任务：」行出现 `.bug-detail__line-key` span 且文本含冒号原文；② 堆栈行 `  at run (runner.js:12)` 整行正文、无 span；③ `https://example.com/a:b` 行不拆标签；④ 空 detail 渲染「—」。验证：`npx vitest run tests/bug-manager` 全绿（含既有 `errorDetail.spec.ts` 不回归）。

## 3. 门禁与交付

- [ ] 3.1 本地门禁：`python run.py check` 阻塞项全绿。若工作区仍有 `platform-config-for-knowledge` 的未提交 WIP 导致无关失败，先协调该变更收口（提交或暂存）再重跑，不得把无关 WIP 带入本变更提交。
- [ ] 3.2 逐文件暂存提交 `fix(bug-manager): 错误内容行首标签加粗接线恢复规格合规`（禁 `git add -A`）；推 feature 分支并 `gh pr create --base Kahoku`，确认 `ci-phase1.yml` 的 python / frontend 两个 job 全绿后合并。
