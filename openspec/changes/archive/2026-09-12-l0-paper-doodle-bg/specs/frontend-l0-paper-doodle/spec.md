## Purpose

定义平台视口纸面底色与主内容区稀疏涂鸦装饰层的可见行为，使全站背景对齐 hand-drawn doodle 原型，同时保持侧栏干净与内容可交互。

## ADDED Requirements

### Requirement: L0 paper background is solid warm white
系统 SHALL 在文档根（`html`/`body`/`#app` 所在视口纸面）使用纯暖白纸面底色，MUST NOT 在该层使用点阵、横线本或网格纹理。

#### Scenario: Viewport shows solid paper
- **WHEN** 用户打开任意前端页面（含登录页）
- **THEN** 视口纸面呈现暖白实色背景，且无可感知的点阵重复纹理

### Requirement: Main content has non-interactive doodle layer
系统 SHALL 在主内容区背后呈现稀疏手绘风 SVG 涂鸦装饰（如星点、咖啡渍环、波浪线等）。该装饰层 MUST 不拦截指针事件，且 MUST NOT 绘制在侧栏区域内。

#### Scenario: Doodles visible behind content
- **WHEN** 用户进入带侧栏的工作台页面
- **THEN** 主内容区背景可见稀疏涂鸦，侧栏背景无同类涂鸦

#### Scenario: Doodles do not block interaction
- **WHEN** 用户点击主内容区按钮、表格行或表单控件
- **THEN** 交互正常命中目标控件，涂鸦层不挡住点击

### Requirement: No double paper texture in workbench pages
固定视口工作台页面（内容区滚动容器）MUST NOT 再叠加第二套点阵纸纹；与 L0 纸面策略保持一致。

#### Scenario: Workbench body has no dot grid
- **WHEN** 用户打开使用固定视口 + 内层滚动的工作台页面
- **THEN** 内容滚动容器背景不为点阵纸纹，且不与 L0 形成双层点阵

### Requirement: Scroll strategy unchanged
本变更 MUST NOT 改变 L0「视口固定 + 内层滚动」策略：`html`/`body` 仍保持高度链与溢出裁切口径；滚动仍发生在既有滚动容器内。

#### Scenario: Inner scroll still works
- **WHEN** 页面内容超出一屏
- **THEN** 用户仍可在既有主内容/内层滚动容器中滚动，且不会因本变更出现整页双滚动条
