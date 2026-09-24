# element-locator-projects Specification

## Purpose
定义元素定位的系统内置单项目工作台：`android` 一个不可新建、改名、删除的项目，项目内的无限目录树与统一叶子类型（页面），以及迁移后叶子标识的保持。

## Requirements

### Requirement: System locator projects

The system SHALL provide exactly one locator project with code `android`. Users MUST NOT create, rename, or delete this project. The project list API SHALL seed the missing project on read.

#### Scenario: List locked projects

- **WHEN** a logged-in user requests `GET /api/elements/projects/`
- **THEN** the response envelope is `{status: true, data}` containing exactly one project with code `android`

#### Scenario: Mutating projects is rejected

- **WHEN** a client calls `POST`, `PATCH`, or `DELETE` on `/api/elements/projects/` or a project detail
- **THEN** the server responds with HTTP 405 and a Chinese message

### Requirement: Project workspace tree

The project SHALL expose an unlimited-depth directory tree. Tree nodes SHALL be directories or files. File `kind` SHALL be `page`. Dragging a directory into its own descendant MUST return HTTP 409.

#### Scenario: Create directory and file under project

- **WHEN** the user creates a directory then creates a `page` file under it
- **THEN** `GET /api/elements/projects/android/tree/` includes both nodes under the correct parent

#### Scenario: Illegal directory move

- **WHEN** the user moves a directory under one of its descendants
- **THEN** the move fails with HTTP 409 and Chinese message

### Requirement: Leaf identity preserved on migration

Data migration SHALL place existing Android pages into the corresponding system project directories derived from former folders, preserving leaf primary keys whenever possible.

#### Scenario: Existing page id still fetchable

- **WHEN** migration completes for an existing Android page id N
- **THEN** `GET /api/elements/pages/N` (or equivalent leaf read) still returns that page and its elements

### Requirement: 目录树拖拽移动

项目工作台的目录树 MUST 支持通过拖动把节点搬到别的目录或项目根。桌面指针输入 MUST 可直接起拖（无需等待）；触摸输入 MUST 先按住节点满 1 秒才进入可拖动状态，未满 1 秒即松开 MUST 按普通点击处理（打开页面或展开目录），MUST NOT 产生任何移动。可接受的落点只有**目录节点**与**项目根落点区**：落入目录即挂到该目录下，落入项目根即挂到根（无父目录）。目录 MUST 可以嵌套进另一个目录；页面（文件）MUST NOT 接受任何落点，因为文件不能包含文件；节点 MUST NOT 落入自身或自身的子孙。把目录拖入自身或其子孙 MUST 被拒并返回 HTTP 409，目录树 MUST 保持不变；把节点拖到页面上 MUST 被拒且 MUST NOT 发出移动请求。被接受的落点 MUST 立即执行移动并刷新目录树；被拒绝的落点 MUST 提示具体原因，且目录树 MUST 与拖动前完全一致。

#### Scenario: 桌面端直接拖入目录

- **WHEN** 用户用鼠标按住项目根下的一个页面并拖到「测试目录」节点上松开
- **THEN** 该页面的父目录变为「测试目录」，目录树刷新后该页面出现在「测试目录」下

#### Scenario: 触摸端长按满 1 秒才起拖

- **WHEN** 用户在触摸屏上按住一个页面节点满 1 秒后移动手指并落到某个目录上
- **THEN** 该页面被移动到该目录下

#### Scenario: 触摸端未满 1 秒按普通点击处理

- **WHEN** 用户在触摸屏上按住一个页面节点不足 1 秒随即松开
- **THEN** 按普通点击处理（页面进入详情），MUST NOT 触发拖动，MUST NOT 发出移动请求

#### Scenario: 目录可以嵌套目录

- **WHEN** 用户把一个目录拖到另一个目录节点上松开
- **THEN** 该目录成为目标目录的子目录，其原有子孙随之保留

#### Scenario: 文件不能包含文件

- **WHEN** 用户把任意节点拖到页面（文件）节点上
- **THEN** 提示只能放到目录或项目根
- **AND** MUST NOT 发出移动请求

#### Scenario: 拖回项目根

- **WHEN** 用户把一个位于子目录下的页面拖到项目根落点区松开
- **THEN** 该页面的父目录变为空，目录树刷新后它出现在项目根

#### Scenario: 目录拖入自身或子孙被拒

- **WHEN** 用户把一个目录拖到它自己或它的某个子孙目录上
- **THEN** 移动被拒并返回 HTTP 409
- **AND** 目录树保持拖动前的结构

#### Scenario: 落点失败时目录树不变

- **WHEN** 一次拖动因落点非法（页面落点、自身/子孙、目标目录不存在或同级重名）而失败
- **THEN** 界面提示失败原因
- **AND** 目录树 MUST 与拖动前一致，MUST NOT 出现半移动状态

### Requirement: 目录树批量勾选移动

目录树 MUST 提供批量选择模式，允许用户勾选多个节点，且勾选 MUST 逐节点生效：勾选一个目录 MUST NOT 自动勾选它的子孙。可勾选集合 MUST 同时包含目录与页面。用户 MUST 能把整个勾选集合一次性移动到指定目录——拖动勾选集合中任一节点到目录/项目根落点，或通过「移动到…」选择目标目录。当勾选集合同时包含某个目录及其后代时，该后代 MUST 被去重（移动该目录已一并带走后代），MUST NOT 对同一节点重复落库。批量移动 MUST 是全有或全无：只要有一个节点非法（移入自身/子孙、目标目录不存在、目标位置同级重名），MUST NOT 移动任何一个节点，并 MUST 返回对应错误（目标不存在 404、非法移动或重名 409、空集合或参数非法 400）。批量移动成功后 MUST 刷新目录树并清空当前勾选。

#### Scenario: 勾选多个文件移动到指定目录

- **WHEN** 用户在批量选择模式下勾选项目根下的 3 个页面，执行「移动到…」并选择「测试目录」
- **THEN** 这 3 个页面全部移动到「测试目录」下
- **AND** 目录树刷新后项目根不再出现这 3 个页面，勾选被清空

#### Scenario: 勾选目录不级联勾选子孙

- **WHEN** 用户勾选一个含子目录与页面的目录
- **THEN** 只有该目录处于勾选态，其子孙 MUST NOT 自动被勾选

#### Scenario: 目录与其后代同时勾选时去重

- **WHEN** 用户同时勾选目录 A 与 A 内的页面 B，并把勾选集合移动到目标目录
- **THEN** 只移动 A（B 随 A 一起到达目标位置），MUST NOT 对 B 再单独落库或报「已在目标位置」

#### Scenario: 勾选集合可含目录与页面

- **WHEN** 用户在批量选择模式下同时勾选一个目录与一个页面并执行移动
- **THEN** 两者都被移动到目标目录

#### Scenario: 任一项非法则整批不落库

- **WHEN** 勾选集合中有一个目录被移动到它自己的子孙目录下
- **THEN** 整批移动失败并返回 HTTP 409
- **AND** 集合中其余合法节点也 MUST NOT 被移动

#### Scenario: 目标目录同级重名被拒

- **WHEN** 勾选集合中某个节点移动到目标目录后会与目标目录下已有节点同名
- **THEN** 整批移动失败并返回 HTTP 409，且提示重名
- **AND** 目标目录下的既有节点 MUST NOT 被覆盖或改名

#### Scenario: 拖拽勾选集合整批移动

- **WHEN** 批量选择模式下已勾选多个节点，用户拖动其中任一已勾选节点并落到某目录
- **THEN** 整个勾选集合被移动到该目录，表现与「移动到…」一致

### Requirement: 批量移动接口契约

元素定位模块 MUST 提供批量移动操作：入参为节点集合（每项含类型 directory 或 page 与节点 id，两类可混合）与目标目录（缺省或空表示项目根），出参 MUST 采用 status/data 信封并给出实际移动的节点数。该操作 MUST 复用单件移动的校验口径：目标目录 MUST 属于当前项目且存在，目录 MUST NOT 移入自身或其子孙，同级同名 MUST 被拒。同一请求内的节点去重口径 MUST 与勾选去重一致（祖先已在集合中时不再单独处理其后代）。

#### Scenario: 批量移动返回信封与数量

- **WHEN** 客户端以 2 个合法节点调用批量移动
- **THEN** 响应信封为 status 为 true 且 data 中含移动数量 2
- **AND** 这两个节点在库中的父目录为目标目录

#### Scenario: 空集合或参数非法

- **WHEN** 客户端提交空的节点集合或缺少节点类型/id
- **THEN** 返回 HTTP 400 并带中文提示
- **AND** MUST NOT 修改任何数据

#### Scenario: 目标目录不存在

- **WHEN** 客户端指定一个不存在或不属于当前项目的目标目录
- **THEN** 返回 HTTP 404 并带中文提示
- **AND** MUST NOT 修改任何数据

### Requirement: 目录树批量勾选删除

目录树的批量选择模式 MUST 提供删除能力：用户 MUST 能把整个勾选集合（目录与页面可混合）一次性删除。删除 MUST 是**全有或全无**：只要有一个节点非法（不存在、类型非法），MUST NOT 删除任何一个节点，并 MUST 返回对应错误。当勾选集合同时包含某个目录及其后代时，该后代 MUST 被去重，MUST NOT 对其重复删除或重复计数。删除成功后 MUST 刷新目录树并清空当前勾选；删除前 MUST 有二次确认，且确认文案 MUST 说明目录会连同其下内容一并删除。

#### Scenario: 勾选多个页面整批删除

- **WHEN** 用户在批量选择模式下勾选 3 个页面并确认删除
- **THEN** 这 3 个页面与其下元素一并被删除，目录树刷新后不再出现它们
- **AND** 当前勾选被清空

#### Scenario: 勾选目录连同其下内容删除

- **WHEN** 用户勾选一个含子目录与页面的目录并确认删除
- **THEN** 该目录、其全部子目录、其下所有页面与元素一并被删除

#### Scenario: 目录与其后代同时勾选时去重

- **WHEN** 用户同时勾选目录 A 与 A 内的页面 B 并确认删除
- **THEN** A 与 B 只被删除一次，删除计数 MUST NOT 把 B 重复计入

#### Scenario: 任一项非法则整批不落库

- **WHEN** 勾选集合中包含一个已不存在的节点
- **THEN** 整批删除失败并返回 HTTP 404
- **AND** 集合中其余合法节点也 MUST NOT 被删除

### Requirement: 删除目录级联删除其下内容

删除一个目录 MUST 删除该目录、其**全部子目录**、以及这些目录下的**所有页面与其元素**。系统 MUST NOT 采用「只删目录、页面浮回项目根」的旧行为。单条删除（右键「删除目录」）与批量删除 MUST 使用同一口径。一次删除 MUST 在单个事务内完成：任一步失败 MUST 整体回滚，MUST NOT 留下「目录已删、页面悬空」的中间状态。

#### Scenario: 删目录不留下浮到项目根的页面

- **WHEN** 用户删除一个含 2 个页面与 1 个子目录的目录，且子目录下还有 1 个页面
- **THEN** 这 3 个页面与其元素全部被删除
- **AND** 项目根 MUST NOT 出现这 3 个页面

#### Scenario: 单条删除与批量删除口径一致

- **WHEN** 分别用右键单条删除与批量勾选删除同一个目录结构
- **THEN** 两者删除的节点集合（目录 / 页面 / 元素）完全一致

#### Scenario: 目录不存在

- **WHEN** 客户端删除一个不存在的目录
- **THEN** 返回 HTTP 404 并带中文提示
- **AND** MUST NOT 修改任何数据

### Requirement: 批量删除接口契约

元素定位模块 MUST 提供批量删除操作：入参为节点集合（每项含类型 directory 或 page 与节点 id，两类可混合），出参 MUST 采用 status/data 信封，并 MUST 分别给出删除的顶层节点数、实际删除的页面数与元素数（MUST NOT 用 ORM 级联对象总数冒充页面数）。空集合或非法 kind MUST 返回 HTTP 400；节点不存在 MUST 返回 HTTP 404。该操作 MUST 复用批量移动的祖先去重口径。删除 MUST NOT 触碰磁盘上的媒体文件（孤儿副本由媒体维护命令回收）。

#### Scenario: 批量删除返回信封与计数

- **WHEN** 客户端以 2 个合法页面（其一含 3 个元素）调用批量删除
- **THEN** 响应信封为 status 为 true 且 data 中含删除的顶层节点数 2、页面数 2 与元素数 3

#### Scenario: 空集合或非法 kind

- **WHEN** 客户端提交空的节点集合或未知 kind
- **THEN** 返回 HTTP 400 并带中文提示
- **AND** MUST NOT 修改任何数据

### Requirement: 项目工作台分栏版式

视口宽度不小于 1280px 时，元素定位项目工作台 MUST 以左右两栏呈现：左栏为固定宽度的目录树，右栏为当前选中页面的元素内容。用户在左栏点击一个页面时 MUST NOT 触发整页跳转，MUST 在同一工作台的右栏就地呈现该页面的元素内容。右栏尚未选中任何页面时 MUST 呈现选择引导（空态），MUST NOT 呈现空白区域。左栏 MUST NOT 承载元素表，右栏 MUST NOT 承载目录树。切换选中页面 MUST NOT 重建目录树：树的展开状态、滚动位置与批量勾选集合 MUST 保持不变。

#### Scenario: 宽屏点击页面在右栏就地呈现

- **WHEN** 视口为 1500px 的用户打开 `/elements/projects/android` 并点击目录树中的「详情页-音乐模式页面」
- **THEN** 浏览器地址 MUST NOT 离开 `/elements/projects/android`
- **AND** 右栏呈现该页面的元素内容，且页面标题与面包屑末项均显示「详情页-音乐模式页面」

#### Scenario: 未选中页面时给出引导空态

- **WHEN** 用户刚进入工作台、尚未点击任何页面
- **THEN** 右栏呈现「从左侧选择一个页面」一类的引导空态
- **AND** MUST NOT 呈现空白右栏

#### Scenario: 切换页面不重置目录树

- **WHEN** 用户先展开某目录、把树滚到中部并勾选两个节点，然后在宽屏下点击另一个页面
- **THEN** 目录树的展开状态与滚动位置保持不变
- **AND** 批量勾选集合 MUST NOT 被清空

### Requirement: 目录树紧凑呈现

目录树的每一行 MUST 默认不绘制完整描边，仅在指针悬停或该行被选中时给出底色与描边。层级关系 MUST 通过不小于 18px 的缩进加一条层级引导线表达，MUST NOT 仅依赖小于 18px 的缩进。目录行 MUST 尾随其直接子项数量；直接子项为 0 的目录 MUST 显示「空」而不是数字 0。页面行的进入指示 MUST 紧贴页面名称，MUST NOT 使用把该指示推到行尾的远端对齐。

#### Scenario: 行默认态不画描边

- **WHEN** 用户打开工作台、指针不在任何行上
- **THEN** 目录树每一行的计算 `border-style` 为 `none`（或描边宽度为 0）

#### Scenario: 悬停与选中态给底色与描边

- **WHEN** 指针悬停在某一行上，或某一行是当前选中页面
- **THEN** 该行出现底色，选中行另有 2px 实线墨色描边与硬阴影

#### Scenario: 目录显示子项数与空目录表达

- **WHEN** 目录「GoveeHome-APP页面元素」下有 13 个页面、目录「测试目录」下无任何子项
- **THEN** 前者尾随显示 13，后者尾随显示「空」，MUST NOT 显示 0

#### Scenario: 进入指示紧贴名称

- **WHEN** 测量任一页面行中「进入」指示左边缘与页面名称文本右边缘的距离
- **THEN** 该距离 MUST 小于 24px，MUST NOT 被推到行尾

### Requirement: 项目根落点按需出现

目录树的项目根落点区 MUST 只在拖拽进行中或批量选择模式下可见。既非拖拽中、也非批量选择模式时，该落点区 MUST NOT 占据目录树的任何一行。隐藏期间落点的判定口径 MUST NOT 变化：把节点拖到项目根时仍 MUST 移动到项目根（无父目录），且 MUST NOT 因落点区隐藏而产生额外的移动请求。

#### Scenario: 平时不显示落点区

- **WHEN** 用户打开工作台且未进入批量选择模式、未开始拖拽
- **THEN** 目录树顶部 MUST NOT 出现「项目根」落点区

#### Scenario: 拖拽起手后出现并可落

- **WHEN** 用户按住一个位于子目录下的页面开始拖动
- **THEN** 项目根落点区出现
- **AND** 把该页面落到该区域后，其父目录变为空且目录树刷新后出现在项目根

#### Scenario: 批量模式显示落点区

- **WHEN** 用户进入批量选择模式
- **THEN** 项目根落点区可见，可用于把勾选集合整体移出目录

### Requirement: 工作台窄屏退化

视口宽度小于 1280px 时，工作台 MUST NOT 并置两栏：MUST 仅呈现目录树。此时点击一个页面 MUST 跳转到该页面的文件详情路由（`/elements/projects/:code/files/:fileId`），沿用既有的整页详情、深链与面包屑口径。

#### Scenario: 窄屏点击页面整页进入详情

- **WHEN** 视口为 1024px 的用户点击目录树中的一个页面
- **THEN** 浏览器地址变为该页面的文件详情路由
- **AND** 详情页呈现其元素表

#### Scenario: 窄屏不渲染右栏元素表

- **WHEN** 视口为 1024px 的用户打开工作台
- **THEN** 页面 MUST NOT 呈现并置的右栏元素表区域
