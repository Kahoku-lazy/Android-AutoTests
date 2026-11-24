## Why

前端审计（2026-11-19）确认一批退役残留：5 个孤儿文件、`ai.ts` 约 193 行死类型簇、45 个自绘图标中 31 个零使用、5 个零使用依赖、死静态资源与死代理配置，以及 `token-refresh` 的"主动续期 + WS 4401"半套未接线功能。这些残留让门禁信号失真、包体虚胖，且 `token-refresh` 的主动续期与现行主规格（只要求 401 被动续期）漂移——归档变更 `2026-11-17-fix-auth-refresh` 曾新增「过期前主动续期」要求但从未同步进主规格。本变更批量退役残留并把续期口径收敛为被动单飞，恢复规格与实现一致。

## What Changes

- **删除孤儿文件**：`task-list/components/CaseImportCard.vue`、`shared/components/AppTabs.vue`、`shared/ocrMatch.ts`（+ 陪葬测试 `tests/shared/p0/ocrMatch.spec.ts`）、`shared/composables/useExpandCollapse.ts`；清 `SerialLogPage.spec.ts` 的 AppTabs 残留 stub。`bug-manager/helpers/errorDetail.ts` **不在本变更**（归 `fix-bug-error-label-wiring` 接线复用）。
- **删除死类型 / 死导出**：`ai.ts` 的 `TaskReport*` 簇（约 193 行，服务于前端已退役的详情报告渲染）与 `AgentRoute`/`TaskSubmitPayload`/`AgentOpResponse`；`animations.ts` 的 `selectPop`/`iconBounce`/`loadingDots`；`shared/icons/index.ts` 31 个未用图标（保留 `makeIcon` 机制与 14 个在用图标）。保留 `@deprecated goal/verification` 旧协议字段（仍被旧数据归一化消费）。
- **依赖瘦身**：移除 `mermaid`/`marked`/`dompurify`/`mitt`/`playwright`（src+tests 零引用）；**保留 pinia**（声明技术栈，模块模板仍列 stores/ 按需）。
- **token-refresh 收敛为被动单飞**：删主动续期链 `ensureFreshToken`/`isTokenExpired`/`tokenExpiresAt`/`decodePayload`/`TOKEN_REFRESH_SKEW_SECONDS`；保留 `configureTokenRefresh`/`refreshAccessToken`/`RefreshRequest`/`resetTokenRefreshLock`（后者是被动刷新的测试缝）；重写 `tokenRefresh.spec.ts` 只测被动单飞；docstring 去掉 WS 4401 / 主动续期口径。
- **死配置 / 死资产 / 过时文档**：删 `vite.config.js` 的 `/ws` 代理（前后端均无 WS 生产点）、`public/agent-avatar.svg`（头像改上传流后零引用）；修 `.npmrc` 的 blockly 过时注释、`useFilterTabs.ts` 引用死 AppTabs 的注释、`ai.ts` 头部失真注释；`frontend/AGENTS.md` 技术栈去掉 Mermaid；vue 技能锚点去掉失真的 mitt 描述。
- **PascalCase 改名（仅 ai-assistant）**：`chat.vue→ChatView.vue`（+ `chat.style.css→ChatView.style.css`）、`evals.vue→EvalsView.vue`，同步 routes / 测试 import / 注释。**ops-console 的 `agents.vue`/`model-configs.vue` 延后**——进行中变更 `platform-config-for-knowledge` 正在改 `model-configs.vue`，现在改名会撞车。
- **depcruise 接入网关**：`.dependency-cruiser.cjs` 增 `no-orphans` 规则；`utils/check_gates.py` 与 `ci-phase1.yml` frontend job 增 `depcruise` 门禁，补上"HTTP 唯一出口"红线无门禁的缺口。
- **清理 `utils/frontend-whitelist.json` 失效条目**（指向已不存在或已低于 500 行的文件）；零化本次涉及文件的 ESLint warning（未用 import/参数、空函数、2 处 any）。

## 关联文档

无关联需求编号。本变更是退役清理 + 工具链门禁补全 + 规格口径收敛，由前端废弃代码与技术债审计驱动，无新增产品需求。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `auth-session`: 新增「令牌续期为被动单飞」要求——续期仅由受保护端点 401 触发、并发单飞、无续期凭证不请求，并明确 MUST NOT 基于 JWT exp 主动预续期。收敛归档未同步的主动续期漂移，防止将来按归档"恢复"主动续期。
- `frontend-l0-design-tokens`: 「Element Plus 原子被覆盖到主题内且交互文本可读」的分段控件对比基准由已删除的 `AppTabs` 改为现役共享件 `FilterTabs`。
- `frontend-l2-page-region`: 「Every L2 page root provides the workbench theme scope」的主题共享件列举由 `AppCard/AppTable/AppTabs` 改为 `AppCard/AppTable/FilterTabs`。
- `serial-log-page`: 「串口日志 Tab 使用模块私有手稿 chip」删除失效尾句「共享件 AppTabs SHALL NOT 为本页修改（其它页仍在使用）」——AppTabs 已退役、无页面使用，该约束已无意义。
- `knowledge-assistant-voice`: **REMOVED**——整份规格描述已下线的知识助手语音面（`/ws/knowledge-assistant/`），退役门禁已禁止该产品面复活，规格属孤儿文档，随 `/ws` 代理退役一并移除。

## Impact

- 前端：`shared/`（icons / animations / ocrMatch / composables / components / auth / types）、`modules/ai-assistant`（改名）、`modules/task-list`（删 CaseImportCard）、`views` 无关；`vite.config.js`、`.npmrc`、`package.json`/`package-lock.json`。
- 测试：删 `ocrMatch.spec.ts`、重写 `tokenRefresh.spec.ts`、清 `SerialLogPage.spec.ts` stub、改 `assistant-chat.spec.ts` import；`tests/bug-manager` 不动。
- 工具链：`utils/check_gates.py`、`utils/frontend-whitelist.json`、`.github/workflows/ci-phase1.yml`、`.dependency-cruiser.cjs`。
- 文档：`frontend/AGENTS.md`（技术栈行，非红线条款）、`.agents/skills/vue/SKILL.md`（mitt 锚点）。
- 规格：`auth-session` / `frontend-l0-design-tokens` / `frontend-l2-page-region` / `serial-log-page` / `knowledge-assistant-voice` 五份 delta。
- **无后端 / 引擎代码改动**：`TaskReport*` 前端类型删除不动后端 `GET /api/tasks/{id}/report/` 端点及其规格（agent-task-flow-report / platform-load-budget / task-list-module 描述的是仍存活的后端端点，属独立后端清理面，不在本变更）。
- 冲突规避：与 `platform-config-for-knowledge` 无文件交集（ops-console 改名已延后）；`errorDetail.ts` 归变更 1。
