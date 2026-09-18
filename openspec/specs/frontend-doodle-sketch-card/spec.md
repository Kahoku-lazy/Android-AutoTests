# frontend-doodle-sketch-card Specification

## Purpose

定义前端共享撕纸入口卡（资源网格：项目 / 原型）在 Hand-Drawn Doodle 主题下的可见行为、cycle 配色与无障碍要求，保证用例、元素定位、页面流三处列表使用同一组件。

## Requirements

### Requirement: Shared sketch card uses torn-paper doodle shell

系统 MUST 通过共享 `SketchCard` 呈现可进入的资源网格项。默认外观 SHALL 采用撕纸卡壳：2.5px 虚线墨色描边、近直角、无模糊的色块硬偏移阴影、34px 墨线图标方块填充 accent；SHALL NOT 再使用顶部实色 accent 条 + 大圆角实线边作为这三处列表的默认卡片。

#### Scenario: Default sketch card renders doodle shell

- **WHEN** 页面渲染共享撕纸入口卡
- **THEN** 卡片可见虚线边框、近直角、硬偏移色阴影与色块图标
- **AND** 标题、描述（空则「暂无描述」）、右下角 meta 可见

### Requirement: Grid accent cycles module colors

同一网格内相邻卡片的 accent（图标底与硬阴影）MUST 按列表 index 循环 8 个模块色令牌 `--c-dashboard` / `--c-device` / `--c-element` / `--c-case` / `--c-runner` / `--c-report` / `--c-ai` / `--c-workflow`。SHALL NOT 把整页锁成单一模块色。

#### Scenario: Adjacent cards use different module accents

- **WHEN** 网格渲染不少于 2 张卡
- **THEN** index 0 与 index 1 的 accent 令牌不同
- **AND** index 8 与 index 0 使用同一令牌（模 8 循环）

### Requirement: Three resource lists consume SketchCard

用例项目列表、元素定位项目列表、页面流原型列表 MUST 使用共享 `SketchCard`。SHALL NOT 继续维护私有 `project-card__accent` / `proto-card__accent` 顶条实现。

#### Scenario: Case project list uses SketchCard

- **WHEN** 用户打开用例管理且存在至少一个项目
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入该项目工作台
- **AND** 删除控件不冒泡为进入

#### Scenario: Element project list uses SketchCard

- **WHEN** 用户打开元素定位且存在系统项目
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入对应 `code` 工作台
- **AND** 不提供删除控件

#### Scenario: Workflow prototype list uses SketchCard

- **WHEN** 用户打开页面流且存在至少一个原型
- **THEN** 每张卡为 `SketchCard` 撕纸壳
- **AND** 点击卡片进入该原型工作台
- **AND** 删除控件不冒泡为进入

### Requirement: Keyboard and reduced motion

可点击的撕纸入口卡 MUST 支持键盘 Enter / Space 激活进入。在 `prefers-reduced-motion: reduce` 下 MUST NOT 依赖倾斜或位移动效传达可交互性；静态虚线边与硬阴影仍保留。

#### Scenario: Keyboard activation

- **WHEN** 撕纸卡获得焦点且用户按下 Enter 或 Space
- **THEN** 系统执行与主键击相同的进入行为

#### Scenario: Reduced motion disables tilt

- **WHEN** 用户环境为 `prefers-reduced-motion: reduce`
- **THEN** 悬停 MUST NOT 播放旋转或位移动效
- **AND** 虚线边与硬阴影仍可见
