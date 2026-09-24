## Why

任务详情页「送给规划模型的输入」区块当前把接口原样返回的四键 JSON **一字不改地塞进 `<pre>`**。该文本由 `json.dumps(..., ensure_ascii=False)` 生成，是**紧凑单行**的一整行：四个键挤在一行，附件正文里的换行被转义成 `\n` 字面量。用户实际看到的是「一屏横向长条 + 满屏 `\n`」，既读不出结构，也读不出附件段落，等于看不了。

## What Changes

- 任务详情页「送给规划模型的输入」区块改为 **JSON 代码块**呈现：2 空格缩进、一键一行、键顺序不变。
- **字符串值内部的换行按真实换行呈现**（`\n`、`\r\n` 转成真换行，并按该值所在层级缩进对齐），使「任务目标」「附件文本内容」多行文本可读。
- 仅改**展示层**：接口返回的 `planner_input` 字段与内容一律不动，仍然是引擎装配同源的那条原文，保证「展示的入模内容 == 实际入模内容」这一既有事实不被破坏。
- 解析失败时（历史脏数据 / 非 JSON 文本）**回退原文整段展示**，不隐藏、不报错、不出现空白区块。
- 非目标：不改四键契约、不改后端序列化、不改附件区块（Markdown 正文本就带真换行）；不新增依赖（不引 `highlight.js` / `vue-json-pretty`）；不加语法高亮、不加复制按钮。

## 关联文档

- PRD-08（AI 助手 · 任务发布与设备操控）
- 前置变更：`openspec/changes/archive/2026-09-23-add-task-input-observability`（本单只改其展示层格式）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-task-publishing`: 任务详情页「送给规划模型的输入」区块必须以缩进 JSON 代码块呈现，且字符串值内的换行必须按真实换行展示；接口字段与入模原文不得改变。

## Impact

- 前端：`frontend/src/modules/ai-assistant/helpers/task-detail.ts`（新增纯函数格式化）、`frontend/src/modules/ai-assistant/components/TaskInputPanel.vue`（改为渲染格式化结果）。
- 后端：无改动（`serialize_agent_task_detail` / `build_planner_user_input` 原样保留）。
- 契约：`GET /api/ai/agent-tasks/{id}/` 的 `planner_input` 字段语义、内容、编码均不变。
- 测试：前端单测覆盖格式化纯函数（缩进 / 字符串内换行 / 非 JSON 回退 / 空值）；既有任务发布类后端单测不受影响。
