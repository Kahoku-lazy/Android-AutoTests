## ADDED Requirements

### Requirement: Workbench page surfaces do not occlude doodles

带侧栏的工作台页面，其 L2 页面根与 L3 `.doc-body` MUST NOT 绘制不透明纸面填充（含与 L0 同色的 `--paper` / 暖白实色）。暖白纸面 SHALL 只来自视口壳层；主区稀疏涂鸦 SHALL 能从内容块之间的空隙透出。本条 MUST NOT 要求拆掉内容卡片、表格、树、筛选栏或截图画布的自身底色。登录页（无侧栏、无涂鸦层）MAY 继续使用纸面底色。

#### Scenario: Inspector workbench shows doodles in gaps

- **WHEN** 用户打开 `/inspector` 且主区未铺满不透明卡片
- **THEN** 主内容区可见稀疏涂鸦，且 `.doc-page` / `.doc-body` 的计算背景不为不透明纸面填充

#### Scenario: Locator and case workspaces show doodles in gaps

- **WHEN** 用户打开 `/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 或 `/cases/projects/:id`
- **THEN** 主内容区可见稀疏涂鸦，且这些页的 `.doc-body` 计算背景不为不透明纸面填充

#### Scenario: Dashboard page root does not paint paper

- **WHEN** 用户打开 `/dashboard`
- **THEN** 页面根计算背景不为不透明纸面填充，章节钉板等内容块仍可保留自身底色

#### Scenario: Login page keeps solid paper

- **WHEN** 用户打开 `/login`
- **THEN** 视口仍为暖白实色纸面，且不要求出现主区涂鸦
