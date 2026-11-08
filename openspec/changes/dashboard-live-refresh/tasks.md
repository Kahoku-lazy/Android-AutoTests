## 1. 章节头瘦身

- [x] 1.1 `index.vue`：四个章节头删除 `.chapter-eyebrow`（Platform Ops / AI Usage / Test Assets / Trends & Activity）与 `.chapter-desc` 描述行，只留模块色方标与中文标题。验证：页面无 eyebrow 与描述行，章节标题仍为四段。**验证结果**：`grep chapter-eyebrow|chapter-desc` 在 index.vue 为 0。
- [x] 1.2 `DashboardView.style.css`：保留 `.chapter-title` 与方标样式（`.chapter-eyebrow/.chapter-desc` 规则保留但无消费点，后续可清）。验证：`npm run build` 通过。**验证结果**：build 通过。

## 2. 自动刷新

- [x] 2.1 `index.vue`：删除 `#actions` 里的「刷新」按钮与 `refreshing` 解构；启用 `useDashboardAutoRefresh(refreshSilently)`。验证：页头无按钮，页面挂载后 5 秒触发一次静默拉取。**验证结果**：`refreshing` 残留 0；轮询已在 setup 中调用。
- [x] 2.2 `useDashboardAutoRefresh.ts`：`DASHBOARD_REFRESH_MS` 30s → 5s（含注释）。验证：`tests/dashboard/p1/dashboardAutoRefresh.spec.ts` 断言 5_000 通过。**验证结果**：7 文件 59 用例通过。
- [x] 2.3 `useDashboardStats.ts`：`_fetchAndMap` 增加数据指纹（统计 + 四图 + 任务 + 活动，排除 `last_updated`）；静默轮询指纹一致时直接返回，不写任何 ref。验证：单测 + 手动观察「最近更新」不再每 5 秒跳。**验证结果**：`useDashboardStats.spec.ts` 14 条通过（含活动失败保留 error 的用例）。
- [x] 2.4 `tests/dashboard/p1/dashboardAutoRefresh.spec.ts`：间隔断言与用例名改 5 秒。验证：`npx vitest run tests/dashboard` 全绿。**验证结果**：59 passed。

## 3. 页脚固定

- [x] 3.1 `index.vue`：`<footer class="dashboard__footer">` 移出 `.doc-body`，成为 `.doc-page` 的直接子节点。验证：`.doc-body` 后代中不再包含页脚。**验证结果**：footer 位于 `</div>`（doc-body 结束）之后。
- [x] 3.2 `DashboardView.style.css`：`.dashboard__footer` 加 `flex: 0 0 auto` 与外边距；`.doc-body` 下内距从 `lg` 收到 `sm`。验证：滚动内容时页脚位置不变。**验证结果**：样式已改。

## 4. 门禁与验收

- [x] 4.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/dashboard`、`npm run lint:lines`。验证：命令全绿。**验证结果**：tsc 0；build 37.9s；59 passed；虚线门禁 0 处。
- [ ] 4.2 页面目视：章节头只剩标题、页头无刷新按钮、滚动时页脚不动。验证：用户确认。

## 5. AI 用量 Agent 卡横排

- [x] 5.1 DashboardView.style.css：.ch-ai__body 右列由 minmax(280px, 420px) 改为 minmax(0, 1fr)，让 Agent 卡拿到整段剩余宽度。验证：1684 视口下两卡各约 420px。**验证结果**：已改。
- [x] 5.2 index.vue：.agent-usage-list 由单列改 
epeat(2, minmax(0, 1fr))，lign-items: stretch；@media (max-width: 1400px) 回落单列，保留 1100px 的间距规则。验证：
pm run build:check 与 	ests/dashboard 通过。**验证结果**：build 35s、59 用例通过。

## 6. 章节标题放大与活动区留白

- [x] 6.1 DashboardView.style.css：.chapter-title 由 --app-size-md(16) 提到 --app-size-lg(20)；.chapter-mark 34 → 40px、内部 svg 16 → 20px，与字号匹配。验证：
pm run build:check 通过。**验证结果**：build 35.1s 通过。
- [x] 6.2 ActivityTimeline.vue：去掉 .timeline__list 与 .timeline__empty 的 min-height: 10 槽（以及只服务它的 --timeline-slot），条目少时不再留整片空白；空态改为 padding: var(--app-space-xl) 0。验证：
px vitest run tests/dashboard 通过。**验证结果**：59 passed。

- [x] 6.3 DashboardView.style.css：.doc-body 顶部内距 0 → ar(--app-space-sm)。章节板带 -0.25° 旋转，宽度约 1400px 时上角外扩约 3px，零内距下会被滚动容器裁掉顶边。验证：最小复现页左右对比顶边完整。**验证结果**：build 33.6s、	ests/dashboard 59 passed。

- [x] 6.4 DashboardView.style.css：章节图标与标题对齐——.chapter-mark 40 → 26px、边框 2.5 → 2px、内部 svg 20 → 15px；.chapter-head__left 由 lex-start 改 center，使图标上下与 20px 标题行盒（25px）齐平。验证：
pm run build:check、	ests/dashboard 通过。**验证结果**：build 41.9s、59 用例通过。

## 7. 页尾空白

- [x] 7.1 内容不满一屏时的页尾裸白：DashboardView.style.css 让最后一块章节板 .doc-body > section:last-child 以 lex: 1 撑满剩余高度，并把其中的 .activity-timeline 设为 lex: 1; min-height: 0，活动卡边框与硬阴影一直落到页脚。验证：数据超过一屏时无剩余空间，不受影响。**验证结果**：build 35.5s。
- [x] 7.2 ActivityTimeline.vue：.timeline__list 改 flex 列，.timeline__empty 用 lex: 1 在卡内垂直居中，空白不再裸露在卡外。验证：
px vitest run tests/dashboard 59 passed。**验证结果**：59 passed。
