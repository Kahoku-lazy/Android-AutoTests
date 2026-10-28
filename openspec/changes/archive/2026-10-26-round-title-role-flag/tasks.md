## 1. 纯函数：序号与标记

- [x] 1.1 `frontend/src/modules/task-list/helpers/task-detail.ts`：新增 `executorRoundNumbers(rounds)`——只给 `role_kind === "executor"` 发号，按 `step_seq` 首次出现顺序（同一 `step_seq` 复用），`step_seq` 缺失时退化为按轮次发号；返回 `Map<round_id, number>`。验证：`npx vitest run tests/task-list` 全绿。**验证结果**：14 个文件 110 passed；发号四条用例（只给执行轮 / 重试共号 / 缺 step_seq 退化 / 无执行轮空表）全过。
- [x] 1.2 同文件改写 `roundTitleLead(round, execNo)` 为「序号 + 重试 + 标记」三段拼装，新增 `roundFlag` 与 `roundOutcomeText`；删掉 `ROUND_KIND_LABELS` 与中文类别。验证：全绿。**验证结果**：`roundTitleLead` 输出形如 `"2. ➡️ "` / `"✅ "` / `"第 2 次 ✅ "`；类别文字在 helpers 与组件内均已无引用。
- [x] 1.3 `frontend/tests/task-list/p0/task-detail.spec.ts`：补四组断言（序号去重、标记三态、无判决无标记、标题不含类别/步骤/模型名）。验证：全绿。**验证结果**：该文件用例 15 → 22。

## 2. 组件与样式

- [x] 2.1 `TaskDetailPage.vue`：新增 `execNoById` 计算属性（逐用例调 `executorRoundNumbers`），模板删掉类别文字、序号改取 `execNoById`、判决徽章移到角色徽章之后、角色徽章挂 `roundKindClass`。验证：`npm run typecheck` 通过。**验证结果**：`vue-tsc --noEmit` 退出码 0；`roundOffset()` 随之删除（不再需要按分页位置编号）。
- [x] 2.2 `TaskDetailPage.style.css`：`.badge-role` 分色（执行 `--c-ai` 紫、验收 `--c-workflow` 蓝），相邻判决徽章补左间距；验收轮 `--round-accent` 由 `--c-report` 改为 `--c-workflow`。验证：`npm run lint:styles` 不新增告警。**验证结果**：门禁仍为 40 条存量告警（task-list 借用 `--ai-*`），与改动前一致；本次用的都是全局语义令牌。
- [x] 2.3 `frontend/tests/task-list/p0/task-detail-round-title.spec.ts`：按新格式改写断言（执行轮「1. ➡️」、验收轮无序号且以 ✅/❌ 开头、判决徽章在角色徽章之后、无判决无标记、两角色徽章类不同、重试同号、空角色不出徽章）。验证：全绿。**验证结果**：7 个用例全过。

## 3. 静态复核与门禁

- [x] 3.1 `temps/round-title-preview.html` 按新格式重画（执行/验收 PASS/执行/验收 FAIL/重试/无判决/窄屏），`node temps/render-round-title.mjs` 出图。验证：`temps/round-title-preview.png` 目视通过。**验证结果**：紫/蓝两色徽章与 emoji 标记清晰可辨，窄屏折行自然。
- [x] 3.2 门禁：`npm run typecheck` + `npx vitest run tests/task-list` + `npm run build` + `python run.py check`。验证：除既有 `openapi-schema` 外全绿。**验证结果**：typecheck 0、vitest 110 passed、build 16.1s 通过；`python run.py check` 阻塞项 21/22，唯一失败 `openapi-schema` 由工作区里先于本次的未提交后端改动引起（`backend/apps/*`、`openspec/openapi.yaml`）。首次跑 check 时 `vite-build` 报过一次失败，同目录再跑即通过，判断是与我并行的一次 `npm run build` 抢占 `dist/` 所致，与本改动无关。
- [ ] 3.3 页面验收（用户侧）：刷新任务详情，确认执行轮带「1. ➡️」、验收轮以 ✅/❌ 开头且无序号、两角色徽章不同色、标题里不再有「执行模型/验收模型」。验证：用户目视确认。

## 4. 归档

- [x] 4.1 `openspec validate round-title-role-flag --strict` 通过后 `openspec archive round-title-role-flag --yes`，主规格同步。验证：`openspec show agent-task-flow-report` 的标题要求为新口径。**验证结果**：`validate --strict` 通过（MODIFIED 块保留了既有 4 个场景名，另加「验收轮不占序号并以结果标记开头」「验收轮失败标记」「尚无判决的验收轮」）；归档后主规格该条需求已改为「不出现类别文字 / 序号只给执行轮 / 角色徽章分色带固定标记 / 验收轮以结果标记开头」。
