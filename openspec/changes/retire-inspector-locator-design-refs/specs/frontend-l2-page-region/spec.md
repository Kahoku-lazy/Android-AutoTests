## MODIFIED Requirements

### Requirement: L2 page roots reuse the shared page skeleton
前端每个 L2 页面根 SHALL 复用共享骨架类作为唯一页面根容器（`.doc-page`；固定视口页同时带 `.doc-page--fixed`），其主体内容容器 SHALL 复用 `.doc-body`；模块 MUST NOT 以私有类名自建等价于该骨架的根容器或主体容器，私有类只能作为作用域 modifier 与既有样式钩子保留。主体为自由布局画布 / 图形编辑器的页面 MAY 例外使用私有主体容器，但该例外 MUST 同时登记在 `frontend/AGENTS.md` 与本 spec，且 MUST NOT 扩散到非画布页面。

#### Scenario: Case and element pages use the shared skeleton
- **WHEN** 依次打开 `/cases`、`/cases/projects/:projectId`、`/cases/projects/:projectId/files/:fileId`、`/workflow` 与 `/serial-log`
- **THEN** 每个页面根元素的 class 同时包含 `doc-page` 与 `doc-page--fixed`，且其主体内容容器包含 `doc-body`

#### Scenario: Visual appearance does not regress
- **WHEN** 对比迁移前后上述页面
- **THEN** 分隔线、树面板宽度与表格横向滚动行为保持等价，无新增重叠或内容裁剪（纸面点阵已按 `frontend-l3-container` 收敛为暖白实色 + 主区涂鸦）

#### Scenario: Canvas page exception is registered and contained
- **WHEN** 检查 `/workflow/prototypes/:prototypeId` 的主体容器
- **THEN** 它是 `.wb-body` 且该例外在 `frontend/AGENTS.md` 与本 spec 中均有登记；其余模块页面主体仍为 `.doc-body`

### Requirement: Header and content share one horizontal inset
L2 页头与其下方内容的水平内边距 SHALL 取自同一设计令牌 `--app-space-lg`（24px）；页面 MUST NOT 出现页头内容与主体内容左边缘不一致的取值。

#### Scenario: Left edges align across pages
- **WHEN** 依次打开 `/dashboard`、`/devices`、`/reports`、`/ai-assistant/agents`、`/cases`、`/workflow` 与 `/serial-log`
- **THEN** 页头品牌区左边缘与主体内容左边缘对齐（浏览器实测差值不超过 1px）

### Requirement: Module page root class names are module-prefixed and globally unique

每个模块的页面根 modifier 类名 MUST 带该模块前缀（如 `case-` / `ai-`），且 MUST 在全仓唯一 —— 系统 SHALL NOT 出现两个模块使用同名页根类的情况。孪生组件（同角色的两份实现）的私有类名 MUST 采用同一规格来源（令牌或共享选择器），SHALL NOT 各自维护分叉的字面量规格。

#### Scenario: No page root class is shared across modules

- **WHEN** 静态检索全仓 `modules/**` 中出现的页根 modifier 类名
- **THEN** 每个类名只出现在一个模块内
- **AND** 不存在两个模块共用同一页根类名

#### Scenario: Twin components share one spec source

- **WHEN** 检查同一模块内同角色的两份组件实现（若存在）
- **THEN** 两者的圆角与底色**取自同一令牌**（如 `--app-radius-sm` / `--paper`），内边距取值一致
- **AND** 不存在一方用字面量、另一方用令牌的分叉（圆角与底色维度）

### Requirement: Subpage navigation lives at the top of doc-body

L2+ 的可见回退（返回芯片与波浪面包屑）MUST 渲染在该页 `.doc-body` 的顶部（加载、错误、空、有数据各态均可见，不得只挂在成功态内容里）；系统 SHALL NOT 把它放进 `.wb-header`。页头仍由唯一共享件 `WorkbenchHeader` 提供，且这些带面包屑的子页上页头 MUST 只显示品牌图标、主标题与副标题；`#actions` 操作按钮 MAY 继续留在页头。导航零件 MUST NOT 成为第二套页头。

#### Scenario: Report detail back control is inside doc-body

- **WHEN** 用户打开 `/reports/{runId}`
- **THEN** 回到列表的控件位于 `.doc-body` 顶部
- **AND** `.wb-header` 内没有「← 返回」或面包屑

#### Scenario: Case and element leaf navigation is inside doc-body

- **WHEN** 用户打开用例文件页
- **THEN** 祖先面包屑或返回芯片位于 `.doc-body` 顶部
- **AND** 页面根仍同时带 `doc-page` 与 `wb-shell`
- **AND** `.wb-header` 仍显示主标题与副标题

#### Scenario: Header remains the single shared header

- **WHEN** 在 `frontend/src` 检索页头共享件
- **THEN** 只有 `WorkbenchHeader` 被页面引用为页头
- **AND** 不存在第二套 `PageHeader` 或独立顶栏导航壳

#### Scenario: Locator project workbench matches the same placement

- **WHEN** 用户打开任一带目录树的项目工作台（如 `/cases/projects/:projectId`）
- **THEN** 返回芯片与面包屑在 `.doc-body` 内
- **AND** `.wb-header` 内没有 `.wb-crumbs`
