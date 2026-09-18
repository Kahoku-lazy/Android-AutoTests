## Why

`frontend/tests/login/p1/LoginErrorOverlay.spec.ts` 的 6 条用例里**有 3 条长期失败**（`点「知道了」` / `按 ESC` / `点击遮罩`），且从 L5 覆盖层收敛那天起就没通过过。根因是那次迁移**只做了一半**：

- 断言迁到了 EP DOM（找 `.el-dialog` / `.el-overlay`）
- 但 spec 的 stub 仍只有 `{ teleport: true, transition: false }`，没给 `el-dialog` / `el-button` 任何 stub

于是 vitest 里 `el-dialog` 是未解析组件：控制台刷 `[Vue warn]: Failed to resolve component: el-dialog / el-button`，DOM 里既没有 `.el-dialog` / `.el-overlay`，**footer 具名插槽也不渲染**（未解析元素只渲染默认插槽），所以连 `data-testid="login-error-dismiss"` 都找不到。

项目约定并非「注册真实 EP」——`vite.config.js` 明确写着「单测用 stub 替换 el-*，避免 Element Plus 按需 CSS 拖垮 Vitest」，`LoginCard.spec.ts` / `AccountSwitchPrompt.spec.ts` 也都自带内联轻量 stub。所以这是**漏写 stub**，不是基建缺失。

危害：3 条红用例被当成长期噪声，掩盖了登录页 L5 覆盖层的真实回归面（例如刚修掉的「遮罩被 transform 困在卡片里」在单测层完全无感）。

## What Changes

- 按项目既有约定，为 `LoginErrorOverlay.spec.ts` 补 `el-dialog` / `el-button` 内联 stub，模型化组件真正依赖的 EP 契约：`.el-overlay`（遮罩）> `.el-dialog`、默认插槽 + `footer` 具名插槽、ESC 关闭、点遮罩关闭
- 6 条既有断言的语义**保持不变**（不改成「配合实现」的弱断言），仅让它们重新可达
- 新增 1 条断言锁定 `append-to-body`：这是 L5「Blocking overlays escape transformed ancestors」在单测层唯一可观察的契约（遮罩是否铺满视口只能在真实浏览器量，已由 `temps/login-layer-map/` 的实测覆盖）

**Non-goals**：
- 不在测试里注册真实 Element Plus 插件（违反 `vite.config.js` 既有口径，且拖慢单测）
- 不改 `LoginErrorOverlay.vue` 实现（刚在 `2026-09-17-fix-l5-overlay-transform-trap` 修完）
- 不改 `LoginCard.spec.ts` / `AccountSwitchPrompt.spec.ts` 等已通过的 spec
- 不修 `tests/dashboard/**` 的 30 例 typecheck 既有问题（他模块在飞工作中）

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md` —— 其 Scenario「Error notice overlay on login shell」正是本 spec 应覆盖的行为；本次不新增/修改需求，只让单测真正跑起来
- `frontend/tests/login/p0/LoginCard.spec.ts`、`frontend/tests/login/p1/AccountSwitchPrompt.spec.ts` —— 内联 stub 约定的既有两个范例
- `frontend/vite.config.js` test.projects —— 无 `setupFiles`，故 stub 必须由各 spec 自带
- `openspec/changes/archive/2026-09-17-fix-l5-overlay-transform-trap/` —— 上一个变更顺带定位了本问题根因

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯测试基建修复，无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。生产代码零改动，只让既有 spec 的断言恢复可达。

## Impact

- 测试：`frontend/tests/login/p1/LoginErrorOverlay.spec.ts`（唯一改动文件）
- 生产代码 / 后端 / API / 依赖：无
- 验证范围：`vitest --project login/p1` 该文件 6/6 通过；`vitest --project login/p0 --project login/p1` 全绿；`npm run typecheck`
