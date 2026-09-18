## 1. 过渡实现对齐令牌（motion.css）

- [x] 1.1 修改 `frontend/src/shared/styles/motion.css` 的 `.fade-slide-*`：时长改用 `var(--app-duration-slow)`、缓动改用 `var(--app-ease)`、位移改用 `var(--app-space-md)`（enter）与 `calc(var(--app-space-sm) * -1)`（leave），删除 `0.28s`、`ease`、`16px`、`10px` 字面量；验证：该段不再出现时长/缓动/位移裸字面量
- [x] 1.2 在 `motion.css` 增加 `@media (prefers-reduced-motion: reduce)` 降级块，使 `.fade-slide-enter-active` / `.fade-slide-leave-active` 的 `transition: none`；验证：在浏览器 DevTools 模拟 `prefers-reduced-motion: reduce` 后，路由切换无淡入与位移

## 2. 主区接线路由过渡（App.vue）

- [x] 2.1 在 `frontend/src/App.vue` 用 `<transition name="fade-slide" mode="out-in">` 包住 `<keep-alive :max="5">`，`:key="route.path"` 保持不变；验证：`cd frontend && npm run typecheck` 通过，且路由切换出现过渡而非硬切
- [x] 2.2 核对滚动与缓存契约未被破坏：页面根仍是 `.main-content__body` 的直接子元素，开发环境无新增 `[scroll-guard]` 告警，固定视口工作台页无整页双滚动条；验证：打开 dashboard 与一个 `.doc-page--fixed` 工作台页并缩放窗口检查

## 3. JS 编排动效 reduced-motion 降级（animations.ts）

- [x] 3.1 在 `frontend/src/shared/animations.ts` 增加模块私有 `prefersReducedMotion()`（含 `typeof window` 保护），并在各导出函数入口短路：返回 `void` 的函数直接写终值并 `return`，返回 animejs 句柄的函数以 `duration: 0` 完成；验证：公开签名与返回类型未变，`npm run typecheck` 通过
- [x] 3.2 逐消费方核对降级效果（`StatsCard.vue`、`ActivityTimeline.vue`、`ai-assistant/index.logic.ts`、`AppSidebar.vue`、`WbLoader.vue`）：启用「减少动效」后不播放动画过程、直接呈现终态；验证：DevTools 模拟 reduced-motion，目视仪表盘统计与侧栏入场

## 4. 门禁与验收

- [x] 4.1 运行前端构建与类型检查（`cd frontend && npm run typecheck`，若 `build:check` 可用一并执行），确认无本变更引入的新错误；验证：记录退出码与报错，既有无关报错需注明
- [x] 4.2 用 `vue-frontend-check` 技能过一遍前端门禁（布局裁剪 / 字号 / 硬编码色 / 契约），确认本变更涉及的三个文件合规；验证：门禁逐项记录，无新增违规
- [x] 4.3 完整目视回归登录页、仪表盘与至少一个固定视口工作台页的路由切换；验证：过渡正常，无空白、卡死、双滚动条，涂鸦与纸面观感不变
- [x] 4.4 同步技能口径：若 `.agents/skills/doodle-craft/references/tokens.md` §1.9 需要写明 reduced-motion 降级，则补充该条；验证：文档与实现一致
