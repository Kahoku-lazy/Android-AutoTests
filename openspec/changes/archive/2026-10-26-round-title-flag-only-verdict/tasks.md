## 1. 去掉判决徽章

- [x] 1.1 `frontend/src/modules/task-list/helpers/task-detail.ts`：删除 `roundOutcomeText()`。验证：`grep roundOutcomeText frontend/src` 无命中。**验证结果**：全仓无命中；`ReportRoundTitleInput.verdict` 仍被 `roundFlag()` 使用。
- [x] 1.2 `TaskDetailPage.vue`：模板删掉判决徽章一段，`roundOutcomeText` 从 import 移除。验证：`npm run typecheck` 通过。**验证结果**：`vue-tsc --noEmit` 退出码 0；模板只剩「序号 + 标记 + 角色徽章 + ：动作」。
- [x] 1.3 `TaskDetailPage.style.css`：删除 `.badge-role + .badge`（判决徽章已不存在，选择器不再命中）。验证：`npm run lint:styles` 不新增告警。**验证结果**：仍为 40 条存量告警（task-list 借用 `--ai-*`），与改动前一致；`.badge-pass` / `.badge-fail` 因用例标题与页头摘要仍在用而保留。
- [x] 1.4 两个 tests 文件同步：断言验收轮标题不含 PASS / FAIL、徽章只剩角色徽章；helper 用例删掉 `roundOutcomeText` 一组。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：14 个文件 109 passed（上一轮 110，删掉 1 条判决徽章文字用例）。

## 2. 复核与门禁

- [x] 2.1 `temps/round-title-preview.html` 去掉 PASS / FAIL 徽章并重出图。验证：`temps/round-title-preview.png` 通过。**验证结果**：`✅ / ❌ + 角色徽章 + ：动作` 三段清晰，窄屏折行正常。（中途用 PowerShell `-replace` 批量删徽章把文件编码搞坏过一次，改用 write 重写后正常。）
- [x] 2.2 门禁：`npm run typecheck` + `npx vitest run tests/task-list` + `npm run build` + `python run.py check`。验证：除既有 `openapi-schema` 外全绿。**验证结果**：typecheck 0、vitest 109 passed、build 16.7s；`python run.py check` 阻塞项 21/22，唯一失败仍是 `openapi-schema`（工作区先于本次的未提交后端改动）。
- [ ] 2.3 页面验收（用户侧）：刷新任务详情，确认验收轮只有 ✅ / ❌、没有 PASS / FAIL 徽章，执行轮的 ➡️ 仍在。验证：用户目视确认。

## 3. 归档

- [x] 3.1 `openspec validate round-title-flag-only-verdict --strict` 通过后归档，主规格同步。验证：`openspec show agent-task-flow-report` 的该条需求要求「判决只由 ✅ / ❌ 表示、不得另挂 PASS / FAIL 徽章」。**验证结果**：`validate --strict` 通过（MODIFIED 块保留全部 7 个既有场景名，改写「验收轮不占序号并以结果标记开头」「验收轮失败标记」两条的 THEN）；归档后主规格该条需求已改为「判决 MUST 只由该标记表示：MUST NOT 另渲染 PASS / FAIL 徽章，也 MUST NOT 另写判决文字」。
