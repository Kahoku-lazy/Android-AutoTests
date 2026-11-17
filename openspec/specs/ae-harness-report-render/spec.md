# ae-harness-report-render Specification

## Purpose
规定引擎侧 HTML 执行报告的呈现契约：一次任务的长内容必须能按分区收起来看，让读者先看到结构、再逐层看细节，而不是一次平铺几十屏截图。

## Requirements

### Requirement: 报告区三层分区可折叠且默认收起

报告区的结构 SHALL 分三层：子目标分组（一次 SOP 步骤或一个阶段）、角色块（执行者 / 验收者）、工具卡（单次工具调用）。

三层 MUST 各自可独立折叠：折叠一个分区 MUST NOT 改变同层其它分区的展开状态，也 MUST NOT 改变上下层分区的展开状态。

首次打开报告时三层 MUST 全部处于收起状态；页面 MUST NOT 默认平铺工具卡的正文。

收起后，每层的标题行 MUST 仍然可见并保留辨识信息：

- 子目标分组 MUST 显示分组名与调用次数。
- 角色块 MUST 显示角色名（`执行者` / `验收者`）。
- 工具卡 MUST 显示序号、工具名与该次调用的耗时（形如 `1 adb_screenshot 840.3 ms`）。

#### Scenario: 首次打开长报告

- **WHEN** 读者打开一份含 66 次工具调用的报告，且未做过任何点击
- **THEN** 报告区只显示子目标分组的标题行与调用次数，分组内的角色块、工具卡与截图均不显示
- **AND** 页面高度不随分组内工具卡数量线性增长

#### Scenario: 逐层展开到单张工具卡

- **WHEN** 读者依次点击子目标标题、角色块标题、工具卡标题
- **THEN** 每点一次只展开该层的正文，其余分区保持原状态
- **AND** 工具卡展开后显示该次调用的意图、入参、结果与截图

#### Scenario: 收起后标题行仍带辨识信息

- **WHEN** 读者把已展开的工具卡重新收起
- **THEN** 该卡片只保留序号、工具名与耗时组成的标题行
- **AND** 该卡片的截图与正文不再显示

### Requirement: 报告区子目标带手绘序号

报告区的每个子目标分组 MUST 在标题前显示一个两位数序号：按出现顺序从 `01` 递增，上限 `99`。第 100 个及以后的子目标 MUST 继续显示 `99`，MUST NOT 出现三位数。

序号 MUST 由内联 SVG 的描边笔画绘制，MUST NOT 依赖字体字形，也 MUST NOT 使用位图。笔画 MUST 呈现手绘蜡笔质感：边缘不规则；同一个序号里左侧数字用红、右侧数字用蓝，两种颜色各自的浓度（不透明度）MUST 沿笔画方向由 `45%` 渐降到 `30%`。

同一份报告里的所有序号 MUST 复用同一份渐变与滤镜定义（红、蓝各一套渐变），MUST NOT 为每个序号各嵌一份。

序号 MUST 与子目标标题同处一个可折叠标题行：点击序号 MUST 与点击标题等效地展开 / 收起该分组。

序号 MUST 带可读标签（形如「第 N 个子目标」），读屏器 MUST NOT 把两位数读成「零一」。

#### Scenario: 五个子目标依次编号

- **WHEN** 报告里有 5 个子目标分组
- **THEN** 分组标题前依次显示 `01`、`02`、`03`、`04`、`05`
- **AND** 每个序号的标签分别是「第 1 个子目标」到「第 5 个子目标」

#### Scenario: 子目标超过 99 个

- **WHEN** 报告里有 100 个子目标分组
- **THEN** 第 99 个与第 100 个都显示 `99`
- **AND** 页面里不出现 `100` 这样三位数的序号

#### Scenario: 点序号等同于点标题

- **WHEN** 读者点击子目标标题前的序号
- **THEN** 该分组展开或收起，与点击标题的效果相同
- **AND** 该标题行的 `aria-expanded` 同步翻转

### Requirement: 折叠状态可被辅助技术识别且可键盘操作

每个可折叠分区的标题行 MUST 暴露 `aria-expanded`，其值 MUST 与当前展开状态一致；状态翻转时该属性 MUST 同步更新。

标题行 MUST 能只用键盘操作：聚焦后按 Enter 或 Space MUST 切换该分区，MUST NOT 触发页面滚动或其它动作。

#### Scenario: 键盘展开子目标分组

- **WHEN** 键盘用户把焦点移到子目标标题行并按 Enter
- **THEN** 该分组展开，且 `aria-expanded` 由 `false` 变为 `true`

#### Scenario: 状态与视觉一致

- **WHEN** 某个分区当前已收起
- **THEN** 它的标题行 `aria-expanded` 为 `false`
- **AND** 报告页的提示文案所描述的交互与实际行为一致

### Requirement: 轨迹页调用行可展开收起

轨迹页的调用列表 SHALL 支持点标题行展开该次调用的详情，再点收起。

展开后 MUST 显示该次调用的详情内容；模型调用行没有详情时 MUST 只切换状态，MUST NOT 报错、MUST NOT 显示空白塌陷。

#### Scenario: 展开工具调用详情

- **WHEN** 读者在轨迹页点击一个工具调用行
- **THEN** 该行下方展开详情区，显示概述、参数、结果与 Schema 页签

#### Scenario: 再次点击收起

- **WHEN** 读者在已展开的调用行上再点一次
- **THEN** 详情区收起，`aria-expanded` 回到 `false`

### Requirement: 两处标题栏用平台品牌字体渲染且不依赖外部文件

报告的侧栏品牌标题与页头标题 SHALL 使用平台品牌手写体（`Ziku FeiYang`），字体数据 MUST 随 HTML 内联（`@font-face` 的 `src` 为 data URI），使报告在 `blob:`、`file://` 与 HTTP 三种打开方式下呈现同一支字体。

字体文件不可读时 MAY 回落相对路径，但 MUST NOT 因此中断渲染。

#### Scenario: 前端以 blob: 打开报告

- **WHEN** 用户在前端「执行报告」页点击打开，正文以 `URL.createObjectURL(new Blob([content]))` 的 `blob:` 文档呈现
- **THEN** 侧栏 `AGENT可视化报告` 与页头 `AGENT 执行报告` MUST 呈现品牌手写体
- **AND** 页面 MUST NOT 向磁盘或网络请求任何 `.ttf`

#### Scenario: 直接双击本地报告文件

- **WHEN** 用户用浏览器直接打开落盘的 `*.html`
- **THEN** 两处标题栏 MUST 呈现同一支品牌手写体，不回落为系统黑体

### Requirement: 报告字号只有三档

报告文本 MUST 只取三档字号：**12px** 用于时间、日期、调用次数、耗时、标签与 Badge；**14px** 用于正文（任务正文、验收事项、提示语、侧栏列表、结果与入参 JSON、事件流字段）；**16px** 用于标题与小标题（子目标标题、工具卡标题、图表卡标题、表头）。

两处页面标题栏 MUST 维持平台档位（侧栏品牌 20px、页头 24px），MUST NOT 压到 16px。字号 MUST 取自令牌（`--app-size-*`），MUST NOT 写字面量。

#### Scenario: 正文不再出现 12px

- **WHEN** 阅读一份含任务正文、验收事项与工具卡结果 JSON 的报告
- **THEN** 上述正文 MUST 呈现 14px
- **AND** 单条工具调用的耗时（形如 `147.5 ms`）MUST 仍是 12px

#### Scenario: 页面标题不被压平

- **WHEN** 报告在 1600px 以上窗口打开
- **THEN** 页头标题 MUST 为 24px、侧栏品牌标题 MUST 为 20px
- **AND** 子目标标题 MUST 为 16px，与页头形成层次

### Requirement: 左侧栏默认占三成且可拖可键盘调整

报告左侧栏宽度 MUST 默认等于容器宽度的 30%，并 MUST 在 `[220px, min(760px, 容器宽 - 480px)]` 区间内呈现 —— 下限保证侧栏可读，上限保证右侧正文不被压没。

侧栏与主区之间 MUST 渲染一个分栏手柄，支持鼠标拖拽实时改宽、拖拽期间光标为 `col-resize` 且正文不可选；手柄 MUST 可键盘聚焦，并用 `role="separator"`、`aria-orientation="vertical"` 与 `aria-valuenow` / `aria-valuemin` / `aria-valuemax` 暴露当前宽度。

手柄 MUST 支持：← / → 每次 16px（按住 Shift 48px）、Home / End 直达下限 / 上限、双击回到默认三成。松手后宽度 MUST 被记住，同一浏览器再打开报告时恢复；存储不可用时 MUST 退回默认三成而不报错。

当视口宽度不足以并排两栏（≤900px）时，页面 MUST 退化为单栏且 MUST NOT 渲染分栏手柄。

#### Scenario: 鼠标拖宽侧栏

- **WHEN** 用户在分栏手柄上按住左键向右拖 200px 后松手
- **THEN** 侧栏宽度 MUST 比拖拽前增加约 200px（未触上限时）
- **AND** 拖拽期间 `body` 的计算 `cursor` MUST 为 `col-resize`

#### Scenario: 拖到边界不挤没正文

- **WHEN** 用户把手柄向最右拖过容器可容纳的范围
- **THEN** 侧栏宽度 MUST 停在 `min(760px, 容器宽 - 480px)`
- **AND** 右侧正文 MUST 仍有可见宽度

#### Scenario: 键盘调整与复位

- **WHEN** 键盘用户聚焦手柄后按两次 →，再双击手柄
- **THEN** 侧栏先增加 32px，`aria-valuenow` 同步更新
- **AND** 双击后回到容器宽度的 30%

#### Scenario: 窄屏不渲染手柄

- **WHEN** 视口宽度 ≤900px，两栏退化为单栏
- **THEN** 页面 MUST NOT 渲染分栏手柄
- **AND** 侧栏 MUST 占满可用宽度
