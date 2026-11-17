## Purpose

约定执行报告（`HtmlReportRenderer` 产出的自包含 HTML）的排版与分栏基线：标题栏必须用平台品牌字体渲染且不依赖外部文件，正文字号只有三档，左侧栏默认占三成且可拖可键盘调整。

## ADDED Requirements

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
