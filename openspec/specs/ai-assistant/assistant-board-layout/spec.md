# ai-assistant/assistant-board-layout Specification

## Purpose
约定平台小助手页的看板不套章节白底外框：线路卡直接置于页面背景，页面层级只由页头与卡片自身表达，并以固定的可读宽度展示。

## Requirements

### Requirement: Assistant card sits directly on the page

平台小助手页 SHALL 把助手线路卡直接放在页面背景上，MUST NOT 使用 `.doc-section` 的白色底、描边、阴影外框，MUST NOT 再渲染「平台小助手 / Assistant / N 个助手」区块标题行。页面页头「平台小助手」MUST 保留。

#### Scenario: Page shows the card without a section frame

- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 线路卡直接显示在页面背景上，卡片外不存在白色区块外框
- **AND** 页面不出现重复的「平台小助手」区块标题行或「N 个助手」计数

### Requirement: Assistant card uses a readable fixed width

线路卡在桌面视口 MUST 使用约 300–320px 的固定宽度，MUST NOT 被拉伸到整行。卡片 MUST 采用「左侧头像 + 右侧三行」布局：头像 MUST 为约 120px 的正方形；右侧列 MUST 约 140–150px 宽、约 120px 高，自上而下 MUST 依次为名称、职责、配置按钮，三行 MUST 纵向均匀分布。名称/职责字号 MUST 收敛到能完整放进右列（约 18px / 15px），配置按钮 MUST 与名称/职责同列、不得再占用卡片底部整行。窄屏下右列与字号 MUST 降档到 120px / 15px / 13px，卡片 MUST 收缩到容器宽度，MUST NOT 横向溢出。

#### Scenario: Wide viewport keeps a compact card

- **WHEN** 用户在桌面宽度打开平台小助手页
- **THEN** 线路卡宽度落在 300–320px 之间，头像约 120px，右侧自上而下为名称、职责、配置三行

#### Scenario: Narrow viewport shrinks the card

- **WHEN** 视口宽度小于 720px
- **THEN** 线路卡收缩到容器宽度，右列保持约 120px，页面不出现横向滚动

### Requirement: 助手入口是编排卡片与对话框

平台小助手入口页 SHALL 分为左右两栏：左栏是单智能体编排卡片，右栏是对当前所选卡片的对话框。左栏 MUST NOT 再展示原来的角色线路卡，右栏 MUST NOT 再展示模型池。页面页头 MUST 保留。窄屏下两栏 MUST 改为上下堆叠，MUST NOT 横向溢出。

#### Scenario: 进入助手页看到卡片和对话框

- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 左栏至少有一张「Android UI 控制」卡片，右栏是对话框
- **AND** 本页不出现模型池，也不出现原角色线路卡

#### Scenario: 点卡片后右栏对应该编排

- **WHEN** 用户点选「Android UI 控制」
- **THEN** 右栏对话发往该编排，而不是裸模型对话

### Requirement: 对话前展示当前设备选择

Android UI 控制的对话框 MUST 在发送前展示当前设备选择。未选择设备时发送控件 MUST 不可用，并说明原因。设备列表 MUST 来自现有设备接口，MUST NOT 在助手页另建一套设备数据。

#### Scenario: 没选设备不能发送

- **WHEN** 用户选中 Android UI 控制但没有当前设备
- **THEN** 发送控件不可用，并提示先选择设备

### Requirement: 助手区与工作流区标题条同构

`/ai-assistant` 页面的助手区与工作流区 MUST 各有一条区块标题条，两条 MUST 处于同一种位置与几何：标题在左、计数紧随标题、弹性空白把动作按钮推到最右，标题字号与字重一致。

助手区标题 MUST 为「AI 助手」，计数 MUST 为「共 N 位助手」（N 为当前助手名片数）；工作流区标题 MUST 为「工作流」，计数 MUST 为「共 N 条」。

两个区块的标题条 MUST 由同一个共享件渲染，MUST NOT 各写一份样式。

页面 L2 页头主标题 MUST 为「平台助手」，路由 `meta.title` MUST 与之一致。

#### Scenario: 两个区块标题条对齐

- **WHEN** 用户打开 `/ai-assistant`
- **THEN** 助手区首行是「AI 助手 · 共 N 位助手 …… 新建助手」，工作流区是「工作流 · 共 N 条 …… 新建工作流」
- **AND** 两个标题的基线、字号与左侧起点一致，两个动作按钮右端对齐

#### Scenario: 计数随数量变化

- **WHEN** 助手名片从 3 位增加到 4 位
- **THEN** 助手区计数显示「共 4 位助手」，标题仍为「AI 助手」

#### Scenario: 页头与标签页文案一致

- **WHEN** 用户打开 `/ai-assistant`
- **THEN** 页面标题区显示「平台助手」
- **AND** 浏览器标签页标题包含「平台助手」
