## 1. 共享件：删掉进入按钮

- [x] 1.1 `frontend/src/shared/components/KpiCard.vue`：删除 `enterLabel` 属性与默认值、`<button class="kpi-card__enter">` 片段、`.kpi-card__enter` 三段样式（基础 / hover / reduced-motion 内那条）；`isClickable` 改为 `props.clickable ?? (isEntry ? false : true)`。验证：`rg "enterLabel|kpi-card__enter" frontend/src` 无匹配，`npx vue-tsc --noEmit` 退出码 0。
- [x] 1.2 `frontend/src/modules/dashboard/components/StatsCard.vue`：删除 `showEnter` 属性、接口声明与默认值，以及传给 `KpiCard` 的 `:enter-label`。验证：`rg "showEnter|show-enter" frontend/src` 无匹配。

## 2. 仪表盘调用方

- [x] 2.1 `frontend/src/modules/dashboard/index.vue`：删除 6 处 `:show-enter="false"`（AI 五张 + 任务数量）。验证：`rg "show-enter" frontend/src` 无匹配；页面根 DOM 无 `show-enter` 属性。
- [x] 2.2 `index.vue`：删除「AI 用量」五张 KPI 卡的 `path="/ai-assistant"`。验证：Playwright 实测五张卡 `role=null`、`tabindex=null`、`cursor=auto`，点击后 URL 仍为 `/dashboard`。

## 3. 单测

- [x] 3.1 `frontend/tests/shared/p0/KpiCard.spec.ts`：改成「entry 无进入按钮，clickable=true 时点整卡触发 click」「默认不可点」「clickable=false 不可点」。验证：`npx vitest run tests/shared/p0/KpiCard.spec.ts` 6 passed。
- [x] 3.2 `frontend/tests/dashboard/p0/StatsCard.spec.ts`：改成「有 path 时无进入按钮、点整卡跳转」与「无 path 不可点」。验证：`npx vitest run tests/dashboard/p0/StatsCard.spec.ts` 12 passed。

## 4. 门禁与验收

- [x] 4.1 前端门禁：`npx vue-tsc --noEmit` 退出码 0。`npm run lint:styles` 与 `npm run build` 当前失败，但失败项**全部**位于并行变更的 `frontend/src/modules/task-list/**`（跨模块借用 `--ai-*` 令牌 51 处；`TaskDetailPage.vue` 引用不存在的 `./TaskReport.style.css`），与本变更文件无关——已用 `lint:styles` 输出与 `build` 报错逐条核对，`KpiCard / StatsCard / dashboard/*` 零告警。
- [x] 4.2 页面验收（Playwright）：`.kpi-card__enter` 计数 0；平台运营五张卡 `role=button`、`cursor=pointer`，点击首卡跳 `/devices`；AI 用量五张卡不可点、点击不跳转。截图见 `temps/visual-check/ops.png`、`temps/visual-check/ops-ai.png`。

> 备注：验收时后端因并行变更（`apps/ai_assistant/models.py` 移除 `AITask`、`admin.py` 仍 import）无法启动，页面数值为 0；交互与布局判定不受影响。
