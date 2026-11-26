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

报告正文（`--app-font`）SHALL 首选 `HarmonyOS Sans SC`，与平台 `--font-body` 同一支。字体 MAY 在文档来源为 `blob:` 或 `http(s):` 时按同源地址加载平台既有的 `/fonts/harmonyos-sans/harmonyos-sans.css`；MUST NOT 把鸿蒙字体文件内嵌进报告，MUST NOT 引用第三方字体域名。字体不可用时 MUST 回退到 `PingFang SC → Noto Sans SC → Microsoft YaHei → system-ui`，MUST NOT 因字体加载失败中断渲染。

#### Scenario: 前端以 blob: 打开报告

- **WHEN** 用户在前端「执行报告」页点击打开，正文以 `URL.createObjectURL(new Blob([content]))` 的 `blob:` 文档呈现
- **THEN** 侧栏 `AGENT可视化报告` 与页头 `AGENT 执行报告` MUST 呈现品牌手写体
- **AND** 正文 MUST 以 `HarmonyOS Sans SC` 渲染，字体请求 MUST 只落在本报文来源的同源 `/fonts/harmonyos-sans/` 下

#### Scenario: 直接双击本地报告文件

- **WHEN** 用户用浏览器直接打开落盘的 `*.html`
- **THEN** 两处标题栏 MUST 呈现同一支品牌手写体，不回落为系统黑体
- **AND** 正文 MUST 回退到系统字体栈且页面不报错

#### Scenario: 同源字体不可用

- **WHEN** 平台字体文件 404 或被网络策略阻断
- **THEN** 报告正文回落系统字体，排版与功能不受影响
- **AND** 页面 MUST NOT 因字体加载失败抛错或白屏

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

### Requirement: 报告渲染的唯一数据源 SHALL 是回复的官方内容块

HTML 执行报告的内容 SHALL 由运行记录里每条回复的官方消息内容块渲染而来，MUST NOT 再从事件行或步骤列表里二次推导块内容。

若记录里没有任何可渲染的回复，报告 MUST 明确显示「无内容」状态，MUST NOT 生成结构完整但正文为空的报告来冒充成功。

#### Scenario: 长报告按内容块渲染

- **WHEN** 一次运行包含多次思考、文本与工具调用
- **THEN** 报告按内容块顺序呈现这些块
- **AND** 每一块都能追溯回它所属的那条回复

#### Scenario: 记录中没有回复

- **WHEN** 运行记录里没有可渲染的回复
- **THEN** 报告显示「无内容」状态
- **AND** 不出现空壳分区

### Requirement: 内容块到报告区块的映射 MUST 覆盖五类块且保留顺序

报告 SHALL 为 `thinking`、`text`、`tool_call`、`tool_result`、`hint` 五类内容块各自渲染成对应区块，并保持它们在消息中的先后顺序。

工具调用与工具结果 MUST 按调用标识配对成一张工具卡；同一次调用重复出现的结果 MUST 归入同一张卡。

未知块类型 MUST 降级为可读的通用区块，MUST NOT 丢弃、MUST NOT 让整份报告渲染失败。

#### Scenario: 工具调用与结果配成一张卡

- **WHEN** 一次调用产生工具调用块与工具结果块
- **THEN** 报告里是一张工具卡，卡内同时有入参与结果
- **AND** 后续块不会插到这张卡中间

#### Scenario: 未知块类型

- **WHEN** 记录里出现报告不认识的块类型
- **THEN** 该块以通用区块呈现
- **AND** 其余块照常渲染

### Requirement: 报告的用量与耗时 MUST 取自记录本身

报告的 token 用量 SHALL 取自消息对象的累计用量，耗时 SHALL 取自运行汇总；MUST NOT 在渲染时按步骤重新累加 token。

两边数字不一致时，报告 MUST 以记录内的值为准并在页面上标注该值来源，MUST NOT 静默改写其中一边。

#### Scenario: 报告用量与记录一致

- **WHEN** 记录的回复带累计用量、汇总带耗时
- **THEN** 页面展示的 token 与耗时与记录中的数字一致

### Requirement: 报告 MUST 提供完整执行链路视图

报告 SHALL 提供独立的链路视图，按发生顺序展示：整轮回复的开始与结束、每轮推理、**实际发给模型的 system prompt 全文**、**该轮实际发送的消息全量**（含文本、思考、工具调用、工具结果、运行时提示等块）、上下文压缩判定、工具执行、权限判定。

链路视图 MUST NOT 截断 system prompt 与消息正文；单条消息内的块 MUST 按原顺序展示，图片 MUST 可展开查看。

#### Scenario: 查看某一轮模型实际收到什么

- **WHEN** 读者打开链路视图并展开某轮「实际发给模型的消息」
- **THEN** 看到该轮的 system prompt 全文与该轮全部消息，每条消息带角色与其内容块
- **AND** 该轮的工具结果里若有截图，可直接查看

#### Scenario: 压缩与权限判定可追溯

- **WHEN** 运行中发生上下文压缩判定或权限判定
- **THEN** 链路视图里有对应条目，带压缩前后条数或判定结果

### Requirement: 报告 MUST 分页签呈现概览、阶段、事件流与原始记录

报告 SHALL 至少提供五个页签：结果（按内容块叙述）、概览（运行环境、输入条件、用量、产物路径）、阶段（按轮次分阶段）、事件流（原始事件，增量默认折叠并显示计数）、原始记录（`run` / `input` / `observations` / `summary` 原文）。

阶段视图 MUST 以轮次为粒度，并在首尾提供「准备」与「收尾」两个阶段；阶段的边界 MUST 取自观测里的回复/推理边界，MUST NOT 依赖文本中的阶段标记。

#### Scenario: 按轮次查看执行过程

- **WHEN** 一次运行经历 N 轮推理
- **THEN** 阶段页签出现准备卡、N 张轮次卡与收尾卡
- **AND** 每张轮次卡显示该轮上下文条数、工具次数与耗时

#### Scenario: 增量事件不淹没主事件

- **WHEN** 事件流里包含大量增量事件
- **THEN** 默认只列出非增量事件
- **AND** 末尾有一处折叠区显示增量事件条数，展开后可见

### Requirement: 可折叠标题 MUST 具备可辨识的展开指示

角色块等可折叠标题 MUST 呈现为卡片（边框、圆角与悬停反馈），折叠箭头 MUST 随展开状态旋转，使读者能一眼分辨可折叠与当前状态。

#### Scenario: 展开角色块

- **WHEN** 读者点击角色卡片标题
- **THEN** 箭头旋转 90°，内容展开
- **AND** 卡片保持边框与悬停反馈

### Requirement: 更换数据源 MUST NOT 改变既有视觉契约

本变更 MUST 保留 `ae-harness-report-render` 已定的视觉契约：三层分区可折叠且默认收起、子目标手绘序号、字号仅三档、左栏默认三成且可拖拽调整。

数据源切换 MUST NOT 引入默认展开的分区，MUST NOT 改变序号与标题行的规则。

#### Scenario: 数据源切换后仍默认收起

- **WHEN** 读者首次打开切换数据源后的报告
- **THEN** 三层分区仍全部收起
- **AND** 标题行仍带分组名、调用次数与工具名等信息

### Requirement: 语义字段按「标签：值」逐行渲染

报告里成组的语义字段（运行环境、输入条件、用量、阶段链路、事件字段、原始记录摘要）SHALL 以事实表呈现：一个字段一行，左列为字段名、右列为值，两列对齐。

左列字段名 MUST 使用 12px 字号与 700 字重的墨色，并以「：」与右列分隔；右列值 MUST 使用 14px 字号。字段值缺失（`None` 或空串）时 MUST 显示占位符或省略该行，MUST NOT 输出 `None` 字样。

字段名 MUST 保留记录里的原始键名（如 `role` / `agent` / `model` / `api_key_env` / `assistant_id` / `thread_id`），派生字段 MAY 用中文标签（如「耗时」「上下文条数」）。

#### Scenario: 概览运行环境逐行可读

- **WHEN** 打开一份 `run` 段含 `role`、`agent`、`model`、`api_key_env`、`assistant_id`、`thread_id` 的报告并切到「概览」
- **THEN** 每个字段独占一行，标签加粗，右侧是值
- **AND** 页面上 MUST NOT 出现 `role Android-UI-Executoragent Android-UI-Executor` 这样标签与值粘连的文本

#### Scenario: 缺失字段不显示 None

- **WHEN** 记录的某个字段值为 `None` 或空串
- **THEN** 该行不输出，或值列显示 `—`
- **AND** 页面不出现 `None`

### Requirement: JSON 值以高亮缩进结构渲染

报告中的 JSON 值（对象、数组，以及能解析成对象/数组的字符串）MUST 以缩进结构渲染，并 MUST 对键、字符串、数字、布尔/`null` 四类内容分别着色。

JSON 块 MUST 使用 14px 及以下的等宽字体与暖白纸面，MUST NOT 直接输出单行 `json.dumps` 原文。超长 JSON MUST 默认折叠在 `<details>` 内，summary MUST 标明行数或字数。

#### Scenario: 工具入参与事件载荷不再是单行

- **WHEN** 报告的入参、结果或事件字段是一个 JSON 对象
- **THEN** 该值按缩进多行展示，键与值颜色不同
- **AND** 能解析成 JSON 的字符串同样按结构展示，不出现 `{\"a\": 1}` 这种二次转义

#### Scenario: 超长 JSON 折叠

- **WHEN** 某个字段的 JSON 超过 20 行
- **THEN** 该块默认收起，summary 显示行数
- **AND** 展开后完整显示缩进高亮内容

### Requirement: Markdown 正文渲染为平台样式

报告里的模型文本（`summary.final_text`、报告区 `text` / `thinking` 块、概览用户消息）MUST 按 Markdown 渲染，MUST NOT 把 `**加粗**`、`## 标题`、列表、表格、代码围栏按原文显示。

Markdown 输出 MUST 使用平台令牌：正文 14px、标题 16px、行内代码 12px 等宽、代码块与表格用 1px 淡墨边、引用左侧 4px 强调色。渲染 MUST 转义原始 HTML，MUST NOT 执行模型输出里的脚本或内联事件。

#### Scenario: 最终文本里的加粗与标题生效

- **WHEN** 最终文本包含 `**操作记录**` 与 `## 结论`
- **THEN** 页面渲染为加粗文字与标题，MUST NOT 出现字面量 `**` 与 `##`
- **AND** 列表与表格按 Markdown 结构显示

#### Scenario: 原始 HTML 被转义

- **WHEN** 文本里含 `<script>alert(1)</script>`
- **THEN** 页面以文本形式显示该片段，不执行脚本、不生成 `<script>` 元素

### Requirement: 阶段页沿用报告页的阶段层设计

阶段页 SHALL 与报告页同构：准备、每个轮次（SOP 为每个步骤）、收尾各为一个可折叠阶段；阶段标题 MUST 带手绘序号（`01` 起递增，上限 `99`），MUST 复用报告页的序号 SVG 与折叠交互。

阶段标题行 MUST 保留辨识信息：单角色为「第 N 轮」与上下文条数、工具次数、耗时、token；SOP 为「第 N 步 · 步骤名」、尝试次数、工具次数与通过状态。

阶段体内的事件 MUST 以「类型徽章 + 事件名 + 时刻 + 事实表」的链路卡呈现，MUST NOT 把字段平铺成一行连续文本。

#### Scenario: 单角色阶段按轮编号

- **WHEN** 打开一份没有 `steps` 段的单角色记录并切到「阶段」
- **THEN** 首阶段是「准备」（序号 `01`），其后每个轮次一个阶段，收尾为最后一段
- **AND** 每个阶段默认收起，点标题或序号可展开该阶段

#### Scenario: 阶段内事件字段逐行

- **WHEN** 展开某个轮次阶段
- **THEN** 该轮的推理、请求、返回、压缩、权限、执行等事件各成一张链路卡
- **AND** 卡片内每个字段一行，长 JSON 折叠

### Requirement: 事件流与原始记录可读且不牺牲完整性

事件流每个事件 SHALL 显示时刻、类型与全部字段（`type` / `created_at` 已在行头，可不重复）；增量事件 MAY 保持紧凑并默认折叠。原始记录 SHALL 按 `run` / `input` / `steps` / `observations` / `summary` 分段成卡，段内 JSON 高亮缩进。

超长段 MAY 截断展示，但 MUST 显式注明已截断；小段 MUST 默认展开。

#### Scenario: 事件字段逐行且不被截断丢失

- **WHEN** 打开「事件流」页
- **THEN** 每个非增量事件显示时刻、类型徽章与字段事实表
- **AND** 长字段以可展开的 JSON 块呈现，不折叠字段本身

#### Scenario: 原始记录分段高亮

- **WHEN** 打开「原始记录」页
- **THEN** 五个段落各一张卡，段内 JSON 有缩进与着色
- **AND** 超过 20000 字的段明确标注「已截断」
