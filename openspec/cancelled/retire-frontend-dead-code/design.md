## Context

动机见 proposal.md - Why。审计已用 dependency-cruiser + 全文检索双重确认零引用，关键事实：

- `refreshAccessToken`（保留）只依赖 `inFlight` 锁 / `getRefreshToken` / `transport` / `setToken`，**不依赖** exp 解码链；`resetTokenRefreshLock` 清的是同一把被动刷新锁，是测试缝。
- `TaskReport*` 前端类型无消费方；其对应后端端点 `GET /api/tasks/{id}/report/` 仍被 agent-task-flow-report / platform-load-budget / task-list-module 三份**后端**规格描述为存活——前端详情页退役只让前端类型变死，后端端点是独立清理面。
- `AppTabs` 被 3 份主规格引用（l0 对比基准 / l2 主题列举 / serial-log 失效尾句）；现役共享分段控件是 `FilterTabs`。
- `knowledge-assistant-voice` 整份规格描述已下线语音面，退役门禁已禁止复活，后端 WS 路由为空。
- 进行中变更 `platform-config-for-knowledge` 正在改 `ops-console/model-configs.vue`。
- depcruise 曾漏报 `useExpandCollapse`（orphan=false 但 dependents=[]），单一工具不可尽信。

## Goals / Non-Goals

**Goals:**

- 删尽审计确认的孤儿 / 死导出 / 死类型 / 死图标 / 死依赖 / 死配置，恢复规格与实现一致。
- 把"HTTP 唯一出口 + 无孤儿"红线变成 CI 阻塞门禁。
- 续期口径收敛为被动单飞并写实进主规格。

**Non-Goals:**

- 不动后端 `GET /api/tasks/{id}/report/` 端点及其三份规格（独立后端清理面）。
- 不动 `@deprecated goal/verification` 旧协议字段（仍被旧数据归一化消费）。
- 不改 `AppTable.vue` 的 10 处 `any`（较大类型债，另立）；不做 echarts/element-plus 按需引入（包体重构，另立）。
- 不改 ops-console 文件名（延后到 `platform-config-for-knowledge` 合并后）；不补 knowledge-search 测试（WIP 进行中）。
- 不动 pinia（声明技术栈，保留）。

## Decisions

1. **token-refresh 只删主动续期链，保留被动单飞与测试缝。**
   删 `ensureFreshToken`/`isTokenExpired`/`tokenExpiresAt`/`decodePayload`/`TOKEN_REFRESH_SKEW_SECONDS`，并从 import 去掉只被 `ensureFreshToken` 用的 `getToken`；保留 `configureTokenRefresh`/`refreshAccessToken`/`RefreshRequest`/`resetTokenRefreshLock`。
   理由：已验证 `refreshAccessToken` 不依赖 exp 链；`resetTokenRefreshLock` 服务保留的被动刷新，非死代码。
   备选：接线启用主动续期——被否（需求方选定收敛为被动，且与现行主规格一致）。
2. **删除按"先消费者后提供者"分批，每批 typecheck + build + depcruise 验证。**
   顺序：孤儿文件 → 死导出/死类型/死图标 → 依赖 → token-refresh → 死配置/文档 → 改名 → 门禁 → 白名单 → ESLint。
   理由：零引用已确认，分批验证可在误删时立即定位；depcruise 漏报过孤儿，故每批辅以全文检索与 typecheck。
3. **图标保留 `makeIcon` 机制 + 14 个在用图标，删 31 个未用（30 零引用 + `IconLayers`）。**
   `IconLayers` 先删 `DashboardView.logic.ts` 的未用 import 再删导出。
   备选：整库保留当"素材库"——被否（AGENTS 规定新图标按需经 makeIcon，未用导出即死重）。
4. **AppTabs 删除 + 3 份规格引用同步：l0/l2 换 `FilterTabs`，serial-log 删失效尾句。**
   理由：FilterTabs 是现役共享分段控件；serial-log「其它页仍在使用」已假。MODIFIED 逐字复制完整需求块，仅改 AppTabs 处。
5. **改名用 `git mv` 保历史：`chat.vue→ChatView.vue`（+ `chat.style.css→ChatView.style.css`）、`evals.vue→EvalsView.vue`。**
   同步 `routes.ts` 两处 import、`assistant-chat.spec.ts` import、`ThreadLogPanel.vue` 注释、`<style src>` 引用。ops-console 延后（撞车）。
   理由：ChatView.vue 是白名单里既有的目标名；PascalCase 满足硬性规范 3。
6. **depcruise 门禁：`.dependency-cruiser.cjs` 增 `no-orphans`（error，排除 main.ts / *.d.ts 入口），`check_gates.py` 增 `cmd_gate("depcruise", …, [NPM,"run","depcruise"], blocking=True, cwd=FRONTEND)`，CI frontend gate 列表追加 `depcruise`。**
   理由：补"HTTP 唯一出口"红线无门禁缺口，并防孤儿再积压。
   备选：warn-only——被否（无牙门禁）。
7. **`.npmrc`：在 temps 副本验证去掉 `legacy-peer-deps` 后 `npm ci` 是否仍成功；成功则删开关 + blockly 过时注释，失败则保留开关并改写注释为真实原因。**
   理由：blockly 已不在 lock，注释失真；开关去留须实测而非臆断。
8. **白名单清理：删指向不存在文件的条目；现存文件若已 ≤500 行也删其条目；`gen_arch_stats.py --check-frontend` 验证。**

## 模块防火墙自检

- 纯前端 + 工具链改动，无跨 App 后端 import，无新增 HTTP 调用；`api-client` 的 `configureTokenRefresh` 注入不变。
- 无数据库 / 仪表盘写操作。
- `frontend/AGENTS.md` 仅改技术栈描述行（去 Mermaid），**非红线 / 禁止事项 / 准入清单 / 依赖边界条款**，不触发"改规则先请示"。
- depcruise 门禁是**收紧**而非放宽依赖边界（强化 HTTP 唯一出口），不属需请示的"放宽依赖方向"。
- 规格 delta 均为退役清理 / 口径收敛，不改后端端点行为。

## Risks / Trade-offs

- [no-orphans 门禁在变更 1 未先落地时把 `errorDetail.ts` 判为孤儿] → **先 apply 变更 1**（接线 errorDetail）再 apply 本变更；tasks 标注顺序依赖。
- [depcruise 漏报孤儿导致门禁假绿] → 每批辅以全文检索 + typecheck + build；门禁是必要非充分。
- [误删仍被引用的图标/类型] → 删前逐个 grep 复核零引用，删后 typecheck + build 兜底。
- [改名漏改 import 致路由/测试断] → 全量 grep `chat.vue`/`evals.vue`/`chat.style.css` 引用，跑 `tests/ai-assistant` + typecheck。
- [npm uninstall / 去 legacy-peer-deps 破坏解析] → `npm ci` + build + 全量 vitest 验证；开关去留先在 temps 副本实测。
- [白名单误删致新超标文件漏拦] → `--check-frontend` 验证。
- [MODIFIED 丢细节] → 逐字复制完整需求块，仅改 AppTabs 处，validate --strict 校验。

## Migration Plan

1. **先 apply `fix-bug-error-label-wiring`**（接线 errorDetail，使其可达），再 apply 本变更。
2. 本变更按 Decisions 2 的顺序分批，每批 typecheck + lint + 相关 vitest；末尾 `python run.py check` 阻塞项全绿。
3. 逐文件暂存、Conventional Commits（`refactor(frontend): …` / `chore(frontend): …` / `ci: …` 分事提交，禁 `git add -A`）。
4. 推 feature 分支 → `gh pr create --base Kahoku` → python / frontend 两个 CI job 全绿后合并（按现行 AGENTS PR 流程）。
5. 回滚：revert 对应提交；规格 delta 随归档可逆。

## Open Questions

（无——范围与方向均由需求方拍板。后端报告端点规格清理、AppTable 类型债、echarts 按需引入、ops-console 改名均已明确列为 Non-Goals / 后续独立变更，不阻塞本变更。）
