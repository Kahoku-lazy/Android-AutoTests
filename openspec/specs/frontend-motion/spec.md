# frontend-motion Specification

## Purpose
定义平台前端动效的可见行为与降级契约：主内容区（L1 主区）的路由切换必须呈现过渡，且过渡时长与缓动取自统一设计令牌；当用户启用「减少动效」偏好时，CSS 过渡与 JS 编排动效都必须降级为无动画并直接呈现终态。

## Requirements

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

### Requirement: 组件级动效取自令牌并提供 reduced-motion 降级

组件级 CSS 动效（`transition` / `animation`）的时长 MUST 取自 `--app-duration-*`，缓动 MUST 取自 `--app-ease` / `--app-spring`；系统 SHALL NOT 在动效声明中出现时长或缓动的裸字面量。无限循环的装饰性动画（骨架 shimmer、状态脉冲）MAY 保留其固有周期，但 MUST 提供 `prefers-reduced-motion` 降级。凡 `transition` 声明中动画了 `transform` 的文件 MUST 提供 `@media (prefers-reduced-motion: reduce)` 块，使其不播放位移 / 旋转 / 缩放；仅动画颜色或边框色的文件不要求降级块。

#### Scenario: No hardcoded motion literals outside the registered decorative animations

- **WHEN** 静态检索 `frontend/src` 中 `transition` / `animation` 声明的时长与缓动
- **THEN** 不再出现 `0.12s` / `0.15s` / `0.1s` / `0.2s` 或裸 `ease`
- **AND** 仅剩骨架 shimmer 的 `1.4s` 与状态脉冲的 `1.5s` 两处已登记例外

#### Scenario: Files animating transform ship a reduce block

- **WHEN** 逐行检索含 `transition: … transform …` 声明的文件
- **THEN** 每个文件都含 `@media (prefers-reduced-motion: reduce)` 块
- **AND** 缺失数为 `0`

#### Scenario: Decorative infinite animations keep their period but degrade

- **WHEN** 启用「减少动效」并打开仪表盘任务面板或任何骨架加载中的页面
- **THEN** shimmer / 脉冲不再播放（对应文件已有降级块）
- **AND** 默认渲染下其固有周期不变

#### Scenario: Colour-only transitions are exempt

- **WHEN** 某文件的动效只涉及颜色或边框色
- **THEN** 不要求提供降级块，且其时长仍须取自 `--app-duration-*`
