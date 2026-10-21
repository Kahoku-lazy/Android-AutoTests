## 1. 平台运营加卡

- [x] 1.1 把「任务数量」卡从 AI 用量移到平台运营，按「在线设备 / 活跃智能体 / 运行中任务 / 任务数量 / 工作流」顺序排列，保留 `color="gray"`、`path="/ai-assistant"`、`show-enter=false` 与「今日 N」副标题。验证：`frontend/src/modules/dashboard/index.vue` 的 `ch-ops` 章节含该卡，`ch-ai` 章节不再含「任务数量」。

## 2. AI 用量两行布局

- [x] 2.1 「AI 用量」章节改为 `ch-ai__body` 两列容器：左列 `ai-usage-kpis` 3 列网格，右列智能体卡列表。验证：DOM 中 KPI 卡与 `.agent-usage-list` 为兄弟节点，智能体卡不再位于 KPI 网格下方。
- [x] 2.2 第一行依次放「累计用量」「当天用量」「缓存命中率」，三张卡都 `hide-desc`；累计/当天取 `totalTokens.total/today`，M 单位 2 位小数，缓存命中率取 `cacheHitRate.total`。验证：标签、顺序、`hide-desc` 与取值均符合，`rg "累计 Token|当天 Token 用量"` 无匹配。
- [x] 2.3 第二行依次放「总费用」「当天费用」，分别取 `deepseekCost.total/today`，`significant-digits=3`、后缀「 元」、`desc="DeepSeek"`。验证：两张卡副标题均为「DeepSeek」，旧「DeepSeek 费用」卡不存在。
- [x] 2.4 补充布局样式与响应式：左列固定上限 536px、右列 280–420px，≤1100px 堆叠、≤640px 左列两列；无智能体时单列。验证：`DashboardView.style.css` 含 `.ch-ai__body`、`.ai-usage-kpis` 及对应媒体查询；浏览器缩窗确认不裁切、不重叠。

## 3. 验证与关单

- [x] 3.1 仪表盘相关单测通过：`npx vitest run tests/dashboard/p0/StatsCard.spec.ts tests/dashboard/p1/DashboardView.logic.spec.ts`。
- [x] 3.2 前端类型检查与构建通过：`npm run build:check`。
- [x] 3.3 运行前端门禁 `vue-frontend-check`，确认无硬编码字号/颜色与布局裁剪问题；缩窗验证 1100px / 640px 两档。
- [x] 3.4 归档前同步两个主 spec 的 Purpose（任务数量归平台运营、费用拆卡），并确认 `openspec validate "2026-10-21-dashboard-ai-usage-layout" --strict` 通过。
