## ADDED Requirements

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

## MODIFIED Requirements

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
