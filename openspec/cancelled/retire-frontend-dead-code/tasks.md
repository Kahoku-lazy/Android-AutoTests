## 1. 前置确认

- [ ] 1.1 确认 `fix-bug-error-label-wiring` 已 apply 并合并（`errorDetail.ts` 已接线可达）。验证：`BugDetailDrawer.vue` 已 import `splitErrorDetail`，`npm run depcruise` 不再把 `errorDetail` 报为孤儿。若未合并，先落地变更 1 再做本变更（no-orphans 门禁依赖此前置）。

## 2. 孤儿文件删除

- [ ] 2.1 删除 `task-list/components/CaseImportCard.vue`、`shared/components/AppTabs.vue`、`shared/composables/useExpandCollapse.ts`、`shared/ocrMatch.ts` 与 `tests/shared/p0/ocrMatch.spec.ts`；清 `tests/serial-log/p0/SerialLogPage.spec.ts` 的 AppTabs 残留 stub。验证：全文 grep `CaseImportCard|AppTabs|useExpandCollapse|matchOcrToElements|ocrMatch` 在 src 零命中；`npm run typecheck` 与 `npm run lint` 通过；`npx vitest run tests/serial-log tests/shared` 全绿。

## 3. 死导出 / 死类型 / 死图标

- [ ] 3.1 删 `shared/types/ai.ts` 的 `TaskReport*` 簇（约 335-527 行）与 `AgentRoute`/`TaskSubmitPayload`/`AgentOpResponse`，修头部失真注释；保留 `@deprecated goal/verification`。验证：grep `TaskReport|AgentRoute|TaskSubmitPayload|AgentOpResponse` 在 src+tests 零命中；`npm run typecheck` 通过。
- [ ] 3.2 删 `shared/animations.ts` 的 `selectPop`/`iconBounce`/`loadingDots`。验证：grep 三符号零命中；`npm run typecheck` 通过。
- [ ] 3.3 先删 `dashboard/DashboardView.logic.ts` 未用的 `IconLayers` import，再删 `shared/icons/index.ts` 31 个未用图标导出（保留 `makeIcon` 与 14 个在用图标）。验证：逐个 grep 被删图标名零引用；`npm run typecheck` 与 `npm run lint` 通过。

## 4. 依赖瘦身

- [ ] 4.1 `npm uninstall mermaid marked dompurify mitt playwright`（保留 pinia），同步 `package-lock.json`。验证：`npm ci` 成功；`npm run build`、`npm run typecheck`、`npm test` 全绿。

## 5. token-refresh 收敛为被动单飞

- [ ] 5.1 删 `shared/auth/token-refresh.ts` 主动续期链（`ensureFreshToken`/`isTokenExpired`/`tokenExpiresAt`/`decodePayload`/`TOKEN_REFRESH_SKEW_SECONDS`），import 去掉 `getToken`，docstring 改为被动单飞口径（去 WS 4401）；保留 `configureTokenRefresh`/`refreshAccessToken`/`RefreshRequest`/`resetTokenRefreshLock`。验证：`npm run typecheck` 通过；grep 被删符号在 src 零生产引用。
- [ ] 5.2 重写 `tests/login/p0/tokenRefresh.spec.ts` 只测被动单飞（并发单飞 / 无续期凭证不请求 / 失败不写回 / 通道未初始化报错），修文件头规格引用为现行 auth-session 要求。验证：`npx vitest run tests/login` 全绿。

## 6. 死配置 / 死资产 / 过时文档

- [ ] 6.1 删 `vite.config.js` 的 `/ws` 代理段；删 `public/agent-avatar.svg`。验证：grep `agent-avatar` 在 src 零命中；`npm run build` 通过。
- [ ] 6.2 修 `shared/composables/useFilterTabs.ts` 引用死 AppTabs 的注释（改 FilterTabs 或去除）；`frontend/AGENTS.md` 技术栈行去 Mermaid；`.agents/skills/vue/SKILL.md` 去失真的 mitt 锚点。验证：对应三文件不再残留 AppTabs / Mermaid / mitt 失真表述。
- [ ] 6.3 `.npmrc`：在 temps 副本实测去掉 `legacy-peer-deps` 后 `npm ci` 是否成功；成功则删开关 + blockly 过时注释，失败则保留开关并改写注释为真实原因。验证：主工作区 `npm ci` 成功。

## 7. PascalCase 改名（仅 ai-assistant）

- [ ] 7.1 `git mv` `chat.vue→ChatView.vue`、`chat.style.css→ChatView.style.css`、`evals.vue→EvalsView.vue`；同步 `routes.ts` 两处 import、`ChatView.vue` 的 `<style src>`、`tests/ai-assistant/p0/assistant-chat.spec.ts` import、`ThreadLogPanel.vue` 注释。验证：grep `chat\.vue|evals\.vue|chat\.style\.css` 零命中；`npm run typecheck` 通过；`npx vitest run tests/ai-assistant` 全绿。（ops-console 改名延后，不在本任务。）

## 8. depcruise 门禁

- [ ] 8.1 `.dependency-cruiser.cjs` 增 `no-orphans` 规则（severity error，`from.pathNot` 排除 `main.ts` / `*.d.ts` 入口）。验证：`npm run depcruise` 报 0 孤儿 0 error。
- [ ] 8.2 `utils/check_gates.py` 增 `cmd_gate("depcruise", "前端依赖边界（HTTP 唯一出口 / 无孤儿）", [NPM,"run","depcruise"], blocking=True, cwd=FRONTEND)`；`.github/workflows/ci-phase1.yml` frontend job gate 列表追加 `depcruise`。验证：`python utils/check_gates.py --only depcruise` 通过。

## 9. 白名单 + ESLint

- [ ] 9.1 清 `utils/frontend-whitelist.json` 失效条目（指向不存在文件、或现存但已 ≤500 行的条目）。验证：`python utils/gen_arch_stats.py --check-frontend` 通过。
- [ ] 9.2 零化 7 处 ESLint warning（`sop-form.ts` 未用参数、`DashboardView.logic.ts`/`DevicePoolView.logic.ts` 未用 import、`useDashboardStats.ts` 空函数、`useECharts.ts`/`useFilterTabs.ts` 的 any）。验证：`npm run lint` 0 problems。

## 10. 门禁与交付

- [ ] 10.1 `python run.py check` 阻塞项全绿；`openspec validate retire-frontend-dead-code --strict` 通过。若无关 WIP（`platform-config-for-knowledge`）致失败，先协调其收口再重跑，不带无关改动入本变更提交。
- [ ] 10.2 逐文件暂存、按事分提交（`refactor(frontend): 退役孤儿与死代码` / `chore(frontend): 依赖瘦身与死配置清理` / `ci: depcruise 接入门禁` 等，禁 `git add -A`）；推 feature 分支 → `gh pr create --base Kahoku` → python / frontend 两个 CI job 全绿后合并。
- [ ] 10.3 合并后走 `/openspec-archive-change` 归档，把 5 份 delta 同步进主规格（auth-session 增被动单飞、l0/l2/serial-log 改 AppTabs 引用、knowledge-assistant-voice 移除）。
