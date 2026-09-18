## ADDED Requirements

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