# Proposal: redesign-report-views

## Why

需求方拿「AGENT 执行报告」的概览 / 阶段 / 事件流 / 原始记录四张截图提出五个问题，核心是**报告读起来像调试转储，不像给人看的报告**：

1. 正文用的是 `Cascadia Mono → Noto Sans SC`，不是平台统一的鸿蒙字体（`switch-ui-font-to-harmonyos-sans` 明确把引擎报告列为不在范围）；
2. 语义字段（`role` / `agent` / `model` / `api_key_env`…）以行内 `<span>` 平铺，没有换行、没有标签加粗，`role Android-UI-Executoragent Android-UI-Executor` 连成一串；
3. JSON 一律 `json.dumps` 后塞进 `<pre>`，没有缩进高亮，长字段与短字段同样处理；
4. 最终文本里的 `**操作记录**`、`## 标题`、列表、表格按原文显示，Markdown 未渲染；
5. 阶段页每轮是一张白底卡 + 一串行内字段，与「报告」页的子目标 / 角色卡 / 工具卡三层次设计语言不一致。

## What Changes

- **字体**：报告正文族从 `Cascadia Mono` 改为平台同一支 `HarmonyOS Sans SC`；字体文件不内嵌（三大档原始 TTF 共 24MB，且许可禁止改写），改为在 `blob:` / `http(s):` 文档里按同源 `@import` 平台既有 `/fonts/harmonyos-sans/harmonyos-sans.css`，`file://` 打开时静默回退系统字体栈。品牌手写体 `Ziku FeiYang` 的内联口径不变。
- **字段呈现**：新增「事实表」渲染件（`.facts` / `.fact`），一个字段一行，标签 12px/700（墨色）在左、值 14px 在右，形如 `role：Android-UI-Executor`；概览、阶段、事件流、原始记录统一使用。
- **JSON**：新增 JSON 高亮渲染件（键 / 字符串 / 数字 / 字面量四类着色，缩进结构），字符串里能解析成对象/数组的自动解析；超长值默认折叠，短值行内显示。
- **Markdown**：最终文本、报告页文本块与思考块、阶段收尾、用户消息统一走 Markdown 渲染（标题 / 加粗 / 列表 / 表格 / 引用 / 代码块 / 行内代码 / 链接），样式取平台暖白纸面与墨线令牌。
- **阶段页**：改成与「报告」页同构的分区——准备 / 每轮 / 收尾各为一个可折叠阶段，阶段标题带手绘序号（复用手绘序号 SVG），阶段头带上下文条数、工具次数、耗时与 token；阶段内事件按「事实表」渲染的链路卡。
- **事件流 / 原始记录**：事件行改为「时刻 + 类型 + 事实表」，增量事件保持紧凑并默认折叠；原始记录每段一张卡，高亮缩进 JSON，小段默认展开、大段折叠。
- **不改**：五页签结构与数据源、三层折叠语义、字号三档、左栏三成可拖、`HtmlReportRenderer` 旧入口的数据来源。

## 关联文档

无 PRD 编号：本变更是引擎侧报告呈现层的可读性修复，不新增产品能力、不改接口与落库字段。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ae-harness-report-render`：新增「正文用平台鸿蒙字体」「语义字段按标签逐行」「JSON 高亮渲染」「Markdown 渲染」「阶段页沿用报告层次」五条呈现要求；同时修改「两处标题栏字体不依赖外部文件」一条，允许正文按同源加载鸿蒙字体。

## Impact

- **代码**：`engines/ae_harness/event/render.py`（共享 CSS/脚本、字体令牌）、`engines/ae_harness/event/render_aligned.py`（四页签渲染）、新增 `engines/ae_harness/event/render_blocks.py`（事实表 / JSON / Markdown 渲染件）；`requirements.txt` 显式登记 `markdown-it-py`（原本经 deepeval → rich 间接存在）。
- **产物**：`*.aligned.json` 数据不变；新生成的 `*.html` 体积随事件流事实表增大，仍为单文件自包含（字体走平台同源，不写入文件）。
- **文档**：`.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md` 的五页签口径与字体口径同步。
- **回退**：`git revert` 本单提交即可；报告是每次运行重新生成的产物，无存量数据迁移。
