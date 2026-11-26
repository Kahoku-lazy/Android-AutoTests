# Tasks: redesign-report-views

## 0. 前置核对

- [x] 0.1 核对正文当前字体：`_CSS` 的 `--app-font` 首族是 `Cascadia Mono`，其次 `Noto Sans SC`，Windows 实际落微软雅黑；与平台 `--font-body`（`HarmonyOS Sans SC`）不一致
- [x] 0.2 核对两条打开路径：助手 / 任务报告走 `threadLogUrl`（`http(s):`），报告台账 SOP 报告走 `createObjectURL`（`blob:`）；两者都不能用相对路径取字体
- [x] 0.3 实测 blob 文档的字体解析：`new URL('/fonts/x.ttf', 'blob:http://host/uuid')` 抛 `TypeError: Invalid URL`；按 `origin` 拼绝对地址后请求命中
- [x] 0.4 核对字体许可：三档原始 TTF 共 24.1MB，许可第②条禁止改写；不内嵌、不切片，走同源加载

## 1. 渲染件（`engines/ae_harness/event/render_blocks.py`）

- [x] 1.1 事实表：`facts()` / `fact()` 输出 `.facts` / `.fact`，标签 12px/700 + 冒号，值按类型分派
- [x] 1.2 JSON：`json_block()` / `json_value()` 缩进 + 键/字符串/数字/字面量四类着色，JSON 字符串自动解析，超长折叠
- [x] 1.3 Markdown：`markdown()` 用 markdown-it-py（commonmark + table + strikethrough，`html=False`）
- [x] 1.4 文本：`pre_text()` / `clock()`（ISO 时刻取 `HH:MM:SS.mmm`）
- [x] 1.5 `requirements.txt` 显式登记 `markdown-it-py`；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过，`python -c "from engines.ae_harness.event.render_blocks import markdown"` 可导入

## 2. 字体

- [x] 2.1 `_CSS` 的 `--app-font` 改为 `HarmonyOS Sans SC → PingFang SC → Noto Sans SC → Microsoft YaHei → system-ui`，`--app-font-mono` 对齐平台 `Consolas → Cascadia Mono → ui-monospace`
- [x] 2.2 `_SCRIPT` 增加同源字体注入：`blob:` / `http(s):` 且 origin 为 http 时注入 `@import url("<origin>/fonts/harmonyos-sans/harmonyos-sans.css")`；`file:` / `null` 跳过且不报错
- [x] 2.3 标题品牌字体内联口径不变；验证：Chromium 实测 `http://` 与 `blob:` 两种文档都只请求同源 `/fonts/harmonyos-sans/`，`document.fonts.check('14px "HarmonyOS Sans SC"')` 为 true；`file://` 打开无报错并回落系统字体

## 3. 概览页

- [x] 3.1 运行环境：`run` 全字段 + `schema` + 事件数，按事实表逐行
- [x] 3.2 输入条件：提示词字数 / 工具数 / 角色卡 / 用户消息（Markdown）/ system prompt 全文（折叠）
- [x] 3.3 用量：token 事实表 + 缓存命中率条 + 末轮图片数；逐次调用改宽表（轮次 / 模型 / 输入 / 输出 / 缓存 / 开始 / 结束）
- [x] 3.4 结果：`final_text` Markdown 渲染；产物路径事实表；SOP 步骤结论卡保留
- [x] 3.5 视觉：卡片网格、宽卡跨列、卡头标签/计数、字号三档；验证：合成单角色 + SOP 记录渲染截图，无字段粘连、无 `None`

## 4. 阶段页

- [x] 4.1 单角色：准备（01）→ 每轮（02…）→ 收尾，阶段头带手绘序号、上下文/工具/耗时/token
- [x] 4.2 SOP：每步一个阶段（01…），阶段内角色卡，角色卡内轮次卡，步骤状态牌与期望/说明用事实表
- [x] 4.3 链路卡：类型徽章 + 事件名 + 开始/结束 chip + 时刻 + 字段事实表，长 JSON 折叠
- [x] 4.4 把 `_ORDINAL_DEFS` 提到页面级，阶段页不依赖报告区是否渲染过序号
- [x] 4.5 验证：合成记录切到阶段页逐层展开，键盘 Enter/Space 可折叠，窄屏不溢出

## 5. 事件流

- [x] 5.1 事件行：时刻 + 类型徽章 + 事实表；`type` / `created_at` 不重复
- [x] 5.2 增量事件默认折叠、行内短值截断；验证：合成含 delta 的记录打开正常，页面不出现横向滚动

## 6. 原始记录

- [x] 6.1 五段成卡，段内 JSON 高亮缩进；小段默认展开、大段折叠
- [x] 6.2 超过 20000 字的段注明「已截断」

## 7. 文档、测试与门禁

- [x] 7.1 更新 `.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md` 的五页签口径（字体、事实表、JSON、Markdown、阶段层）
- [x] 7.2 契约守护：新增 `tests/arch/unit/test_report_render_blocks.py`（字体族、同源字体注入、事实表/JSON/Markdown 类名、阶段序号、依赖登记）；`tests/arch/unit` 相关 29 项通过
- [x] 7.3 质量门禁：`engines-agents-style` 0 违规、docstring 检查 0 error；`utils/check_gates.py` 中 `ruff-engines-format / ruff-engines-lint / vite-build / style-gates` 均通过（`prettier` 与 `vue-file-size` 的失败来自工作区既有前端改动，本单未碰前端）
- [ ] 7.4 人工验收：本机无真实 `*.aligned.json`，已用合成记录（单角色 + SOP）逐页截图核对；待需求方用真实记录复跑后确认
