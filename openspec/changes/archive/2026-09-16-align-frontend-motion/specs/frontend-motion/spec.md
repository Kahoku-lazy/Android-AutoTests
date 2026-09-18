## Purpose

定义平台前端动效的可见行为与降级契约：主内容区（L1 主区）的路由切换必须呈现过渡，且过渡时长与缓动取自统一设计令牌；当用户启用「减少动效」偏好时，CSS 过渡与 JS 编排动效都必须降级为无动画并直接呈现终态。

## ADDED Requirements

### Requirement: Route transition is wired in the main content area
主内容区（L1 主区）的路由切换 SHALL 呈现过渡动效，MUST NOT 为瞬时硬切。

#### Scenario: Switching between module pages
- **WHEN** 用户在主区通过侧栏导航从任一模块页面切换到另一模块页面
- **THEN** 内容区呈现一次淡入与位移过渡，而非瞬时切换

#### Scenario: Login page stays reachable
- **WHEN** 用户从 `/login` 进入主区页面（或反向切换）
- **THEN** 切换正常完成，不出现空白、卡死或整页双滚动条

### Requirement: Transition timing and easing come from design tokens
路由过渡的时长与缓动 MUST 取自设计令牌 `--app-duration-slow` 与 `--app-ease`；过渡实现 MUST NOT 出现时长或缓动的硬编码字面量（如 `0.28s`、`ease`），位移量 MUST 由既有间距令牌派生。

#### Scenario: No hardcoded motion literals
- **WHEN** 检查 `frontend/src/shared/styles/motion.css` 中 `.fade-slide-*` 的 `transition` 与 `transform` 声明
- **THEN** 时长引用 `var(--app-duration-slow)`、缓动引用 `var(--app-ease)`、位移引用 `var(--app-space-*)`，不存在裸字面量

### Requirement: Transition preserves scroll and keep-alive contracts
接入过渡 MUST NOT 改变既有主区滚动与缓存契约：页面根仍必须是 `.main-content__body` 的直接子元素，`keep-alive` 的 `:max="5"` 与 `:key="route.path"` 保持不变。

#### Scenario: Scroll guard still resolves the page root
- **WHEN** 开发环境打开一个内容超过一屏的主区页面
- **THEN** `scroll-guard` 仍能取到页面根（`.main-content__body > *`）且不产生误告警

#### Scenario: Page cache behavior unchanged
- **WHEN** 用户在多个模块页面之间来回切换
- **THEN** `keep-alive` 仍按 `route.path` 缓存最多 5 个页面实例

### Requirement: Reduced motion disables route transition
当 `prefers-reduced-motion: reduce` 生效时，路由过渡 SHALL 关闭位移与淡入，直接呈现目标页面。

#### Scenario: Reduced motion user switches route
- **WHEN** 用户启用「减少动效」，并在主区切换路由
- **THEN** 目标页面立即呈现，无淡入与位移

### Requirement: Reduced motion disables scripted animations
当 `prefers-reduced-motion: reduce` 生效时，`frontend/src/shared/animations.ts` 导出的动画函数 SHALL 跳过动画过程并直接落到终态；其公开函数签名与返回类型 MUST 保持不变。

#### Scenario: Scripted animation lands on final state
- **WHEN** 启用「减少动效」，使用 `shared/animations.ts` 的组件（如仪表盘统计计数、侧栏入场）挂载
- **THEN** 元素直接呈现终态（计数为终值、位置为最终位置），不播放过渡过程

#### Scenario: Callers keep compiling
- **WHEN** 运行 `cd frontend && npm run typecheck`
- **THEN** 所有 `shared/animations.ts` 消费方编译通过，无因降级短路引入的新类型错误
