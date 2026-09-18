## 1. 共享 KpiCard doodle 壳（kpi 变体）

- [x] 1.1 改造 `frontend/src/shared/components/KpiCard.vue` 默认外观为 doodle 壳（虚线边、近直角、硬偏移色阴影、模块 accent），保留 `label` / `value` / `color` / `shape` / click 兼容；验证：报告页与 AI 知识库目视换皮，既有 props 调用无报错，`cd frontend && npm run typecheck` 通过
- [x] 1.2 为 `prefers-reduced-motion: reduce` 关闭微倾/位移动效，静态壳（虚线边 + 硬阴影）仍保留；验证：DevTools 模拟 reduce 后悬停无旋转/位移动画
- [x] 1.3 更新或补齐 `KpiCard` 单测（类名/结构/click/键盘若适用）；验证：相关 vitest 通过

## 2. entry 变体 + 仪表盘薄包装

- [x] 2.1 在 `KpiCard` 增加 `variant="entry"`（图标槽、标题、数值、描述、进入动作、可选 live/deco），并保证装饰不挡住可点区域；验证：对照 `temps/prototype-doodle-kpi-stats-card.html` 目视一致，键盘 Enter/Space 可激活
- [x] 2.2 将 `frontend/src/modules/dashboard/components/StatsCard.vue` 改为薄包装共享 `entry`（保留 count-up / loading / path 路由逻辑，删除私有清新风默认样式）；验证：仪表盘统计行与 doodle entry 一致，进入导航仍正确，`StatsCard` 既有单测通过或按新结构更新后通过
- [x] 2.3 核对 `dashboard/index.vue` 无需重复样式覆盖；验证：页面无回归、无双套阴影/圆角冲突

## 3. 文档与规格同步

- [x] 3.1 更新 `.agents/skills/doodle-craft/references/components.md` §13：写明 dashed 边框、硬阴影、双变体与侧栏色板 DNA 对齐；验证：文档与实现一致
- [x] 3.2 更新 `frontend/AGENTS.md` 中 `KpiCard` 说明（变体、用途、StatsCard 薄包装关系）；验证：文档可被后续 AI/开发者按同一口径引用

## 4. 门禁与验收

- [x] 4.1 运行 `cd frontend && npm run typecheck`（若有 `build:check` 一并执行）；验证：无本变更引入的新错误（全仓仍有既有无关 TS 错误；本变更涉及文件无新增）
- [x] 4.2 用 `vue-frontend-check` 过本变更涉及文件；验证：布局裁剪 / 字号 / 硬编码色 / 契约无新增违规（fallback 色仅作 `var(--token, #…)` 兜底）
- [x] 4.3 目视回归：仪表盘统计行、报告 KPI 行、AI 知识库 KPI；验证：同壳语言，reduced-motion 下降级正确，功能点击/进入正常
