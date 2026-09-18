# frontend-doodle-content-card Specification

## Purpose
定义前端共享内容卡（胶带 note 卡与便利贴 sticky 卡）以及涂鸦操作按钮的可见行为，使小助手卡、任务卡及其它模块列表条目能共用同一套 Hand-Drawn Doodle 语言。

## Requirements

### Requirement: Shared note card matches deco-card DNA

系统 MUST 提供共享内容卡的 `note` 变体，其默认外观 SHALL 对齐模版 deco-card：虚线描边、近直角、纸色底、硬偏移色阴影、可选顶中半透明胶带与微倾；SHALL NOT 以实线细边 + 大圆角 + 模糊 elevation 作为该变体默认样式。

#### Scenario: Assistant route card uses note variant

- **WHEN** 小助手看板渲染线路卡
- **THEN** 卡片呈现虚线边、纸色底、彩色硬阴影与顶中胶带（若启用装饰）
- **AND** 仍展示功能标题、助手身份与连通状态

### Requirement: Shared sticky card matches Do-note DNA

系统 MUST 提供共享内容卡的 `sticky` 变体，其默认外观 SHALL 对齐模版 sticky.do：虚线描边、青绿浅底、硬偏移阴影、可选胶带与更大微倾。失败态 SHALL 可切换为 Dont 语言（浅红底 + 红阴影），仍为同一组件。

#### Scenario: Successful task card uses sticky do language

- **WHEN** 任务列表渲染成功态任务卡
- **THEN** 卡片为青绿浅底 + 虚线边 + 青绿硬阴影
- **AND** 仍展示标题、状态、目标摘要、设备/时间与操作区

#### Scenario: Failed task card uses sticky dont language

- **WHEN** 任务列表渲染失败态任务卡
- **THEN** 卡片为浅红底 + 红硬阴影
- **AND** 标题与删除/详情操作仍可读、可点

### Requirement: Shared doodle buttons use marker tones

系统 MUST 提供共享涂鸦按钮，外观 SHALL 对齐模版 `#comp-buttons`：墨色描边、近直角、硬偏移阴影。色调 MUST 为：危险操作用红底（删除）、校验与详情用青绿底、配置用黄底。MUST NOT 用冷蓝作为「蓝色」语义——本条禁令 SHALL 仅约束上述**操作按钮的语义色调**；切换/分段类控件的「未选中 / 选中」二态不属于语义色调，由 `frontend-doodle-button` 规定。

#### Scenario: Action color mapping on cards

- **WHEN** 用户在小助手卡或任务卡上看到操作按钮
- **THEN** 「删除」为红底，「校验」与「详情」为青绿底，「配置」为黄底
- **AND** 按钮 hover 呈现上移并加深硬阴影，disabled 时不可点且阴影变灰

#### Scenario: Cold blue ban is scoped to semantic tones

- **WHEN** 检索平台内以冷蓝 `var(--c-workflow)` 为底色的按键
- **THEN** 命中项均为切换/分段类控件的「未选中」默认态，不出现于内容卡操作按钮的语义色调中

### Requirement: Decorations do not block actions

内容卡上的胶带等装饰 MUST 使用 `pointer-events: none`（或等价），MUST NOT 遮挡标题、正文或按钮的可点区域。

#### Scenario: Tape does not steal clicks

- **WHEN** 卡片启用顶中胶带且用户点击「配置」或「详情」
- **THEN** 对应动作被触发

### Requirement: Reduced motion and keyboard

可点击按钮 MUST 支持键盘激活。在 `prefers-reduced-motion: reduce` 下，卡片与按钮 MUST NOT 依赖旋转或位移动效传达可交互性，静态虚线边与硬阴影 MUST 保留。

#### Scenario: Reduced motion disables tilt

- **WHEN** 用户环境为减少动效
- **THEN** 卡片悬停不播放倾角回正或位移
- **AND** 按钮仍可用键盘或指针激活

### Requirement: AI assistant consumes shared components

小助手线路卡与任务列表条目 MUST 使用上述共享内容卡与共享按钮（直接使用或薄包装），SHALL NOT 再维护一套与模版冲突的私有实线大圆角默认样式。

#### Scenario: Agent and task boards share the doodle language

- **WHEN** 用户打开 AI 助手看板
- **THEN** 线路卡为 note 变体、任务卡为 sticky 变体
- **AND** 卡内操作按钮使用共享涂鸦色调
