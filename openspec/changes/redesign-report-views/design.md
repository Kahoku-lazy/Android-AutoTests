# Design: redesign-report-views

## Context

报告由引擎侧生成单文件 HTML（`render.py` 持有共享 CSS/JS，`render_aligned.py` 产出五页签）。数据源是 `*.aligned.json`（`run` / `input` / `replies` / `observations` / `steps` / `summary` / `events`），报告不重新推导任何内容。

现状问题（需求方截图 + 代码核对）：

- `_CSS` 的 `--app-font` 首族是 `Cascadia Mono`，其次 `Noto Sans SC`（本机没有 `@font-face`，Windows 实际落微软雅黑），与平台 `--font-body`（`HarmonyOS Sans SC`）不一致；
- `_overview` / `_chain_parts` / `_log_row` 用行内 `<span class="kv"><i>key</i>value</span>` 拼字段，父容器不是 flex/grid 时标签与值直接连成串；
- `json.dumps(...)` 的结果只做 `html.escape` 后进 `<pre>`，没有结构着色；能解析成 JSON 的字符串也不解析；
- `final_text` 与报告区 `text` 块都是 `html.escape` 后进 `<pre>`，Markdown 原样显示；
- 阶段页是白底卡 + 行内字段，与报告页「子目标 → 角色卡 → 工具卡」的层次和手绘序号不一致。

约束：单文件自包含（除平台同源静态字体）、不写注释、字号只有 12 / 14 / 16 三档、折叠契约与左栏契约不变、Doodle Craft 令牌不新增。

## Goals / Non-Goals

**Goals**

- 四页签改成「标题（加粗标签）：数据（一行一条）」的可读结构；
- JSON 有缩进与语法着色，能解析就解析；
- Markdown 真正渲染，样式与平台暖白纸面一致；
- 阶段页复用报告页的阶段头 + 手绘序号 + 角色卡 + 折叠语言；
- 正文与平台同一支鸿蒙字体。

**Non-Goals**

- 不改 `aligned.json` 任何字段、不改 `AlignedRun` 的折叠与落盘；
- 不改五页签的划分与数据来源；
- 不改 `HtmlReportRenderer`（SOP 旧入口）的三页签与数据源，只共享字体令牌；
- 不做交互式筛选 / 搜索 / 虚拟滚动；
- 不内嵌鸿蒙字体（体积与许可原因，见 D1）。

## Decisions

### D1 正文字体：同源加载平台字体表，绝不内嵌 TTF

平台把鸿蒙字体拆成 `public/fonts/harmonyos-sans/harmonyos-sans.css` + 三个原始 TTF（24.1MB）由 `index.html` 挂载。报告有两种打开方式：

| 打开方式 | 文档来源 | 相对路径 | 绝对路径 |
| --- | --- | --- | --- |
| 助手 / 任务报告（`threadLogUrl`） | `http(s):` | 可用 | 可用 |
| 报告台账 SOP 报告（`createObjectURL`） | `blob:http://host/uuid` | 不可用 | 不可用（实测：blob 的不透明路径解析失败，连请求都不会发） |
| 下载后本地打开 | `file:` | 不可用 | 不可用 |

因此不能靠 CSS 里的相对 / 绝对路径，必须用脚本按 `location` 求 origin 再注入。实测（Chromium，blob 文档）：

```
new URL('/fonts/x.ttf', 'blob:http://127.0.0.1:8765/uuid')  → TypeError: Invalid URL
new URL(location.href).origin                                → http://127.0.0.1:8765
注入 @font-face src = origin + '/fonts/...'                    → 请求命中
```

方案：`_SCRIPT` 启动时若 `location.protocol ∈ {http:, https:, blob:}` 且 origin 以 `http` 开头，则往 `<head>` 追加一条
`@import url("<origin>/fonts/harmonyos-sans/harmonyos-sans.css")`；`file:` / `origin === "null"` 直接跳过。
不内嵌 TTF 的理由：三档 24.1MB，base64 后 32MB，报告本身已有截图；且华为许可第②条禁止改写，切片 / 转 woff2 有解释风险（与 `switch-ui-font-to-harmonyos-sans` 同口径）。

`--app-font` 改为与平台 `--font-body` 相同的回退链；`--app-font-mono` 对齐平台 `--font-mono`（`Consolas, Cascadia Mono, ui-monospace`）。

### D2 事实表：两列定义网格，一行一个字段

新增渲染件 `.facts`（容器）+ `.fact`（行）：

```
.fact   grid-template-columns: minmax(5.5em, max-content) minmax(0, 1fr)
.fact__k  12px / 700 / 墨色，::after 生成「：」
.fact__v  14px / 常规，可放行内文本、<pre class="json">、<pre class="text">、Markdown
```

- 标签用**原始字段名**（`role` / `agent` / `model` / `api_key_env`…）回答需求方「字段字体要突出」；只有语义化的派生字段用中文（耗时、上下文条数、轮次…）。
- 值分派：`dict/list` 或 JSON 字符串 → JSON 块；含换行或超 96 字 → 文本块；其余行内。
- 行与行之间用 1px 淡墨横线分隔，最后一行无线；不使用粗描边，避免和卡片外框抢层级。

### D3 JSON：缩进 + 四类着色，能解析就解析

`render_blocks.json_block()` 先 `json.dumps(..., indent=1)`，再用正则按 **字符串（区分键）→ 数字 → 字面量** 的顺序着色：

| 类 | 令牌 | 用途 |
| --- | --- | --- |
| `.j-key` | `--color-blue-27` + 700 | 键 |
| `.j-str` | `--color-teal-38` | 字符串值 |
| `.j-num` | `--color-red-46` | 数字 |
| `.j-lit` | `--c-report` | `true` / `false` / `null` |

字符串值若以 `{` / `[` 开头且能 `json.loads`，先解析再 dump，避免「JSON 里套了一层转义 JSON」。
超长块用 `<details class="jfold">` 折叠，summary 写明行数/字数；不在卡片内部做滚动容器。

### D4 Markdown：markdown-it-py（commonmark + table + strikethrough）

`markdown-it-py` 已随 `deepeval → rich` 存在于环境，本次在 `requirements.txt` 显式登记，避免依赖传递链断裂。配置 `html=False`（模型输出里的原始 HTML 按文本转义）、`linkify=False`（不引额外包）、启用 `table` 与 `strikethrough`。

样式 `.md` 只取平台令牌：正文 14px、标题 16px、行内代码 12px 等宽 + 浅底、代码块暖白纸面 + 1px 淡墨、表格 1px 淡墨、引用左侧 4px `--c-element`。

落点：`summary.final_text`（概览结果 / 阶段收尾）、报告页 `text` 与 `thinking` 块、概览 `input.user_message`。

### D5 阶段页：与报告页同构

- 单角色：`准备`（序号 01）→ 每轮一个阶段（02…）→ `收尾`（最后）；
- SOP：每步一个阶段（01…）→ 阶段内按角色卡 → 角色卡内按轮次卡 → 收尾；
- 阶段头 = `caret + 手绘序号 + 标题 + 右侧 meta`，完全复用报告页的 `.phase-h` / `_ordinal_svg` / `.fold-box` 语义与键盘契约；
- 阶段体 = 事实表（上下文条数、工具次数、耗时、in/out/cache token、reply_id）+ 链路卡；
- 链路卡 = 类型徽章 + 事件名 + 开始/结束 chip + 时刻 + 事实表（字段名取自观测键，中文标签映射），长 JSON 折叠；
- `_ORDINAL_DEFS` 从报告区提到页面级，避免阶段页单独用序号时缺 `<defs>`。

### D6 事件流与原始记录

- 事件行：时刻（12px 等宽）+ 类型徽章 + 事实表；`type` 与 `created_at` 不进事实表（已在头部），其余字段全保留；
- 增量事件（`*_DELTA`）：仍在末尾 `<details>` 里默认折叠，行内只保留短值（截断 120 字），避免 4000+ 行把 HTML 撑爆；
- 原始记录：每段一张卡，段落 JSON 高亮；超 20000 字的段落保留现有截断并显式注明「已截断」；小段（< 4000 字）默认展开。

### D7 不变式

- 数据源仍是 `parts["run"|"input"|"replies"|"observations"|"steps"|"summary"|"events"]`，不新增推导；
- `.fold-box/.fold-h/.fold-b`、`aria-expanded`、键盘 Enter/Space、左栏 30% 拖拽、窄屏单栏全部不动；
- 字号只用 `--app-size-xs/sm/md`；颜色只用已声明令牌；新增样式集中在 `_EXTRA_CSS`，字体令牌改在 `_CSS`。
