# 设计：用例编写报告展示模型事件流

## Context

用例编写任务的运行事件已由 `TaskEventSink` 写入 `task_events`，`task_reports._load_events` / `_item` 已能把事件收成含时间、角色、模型与详情的行。报告此前只对设备任务使用这些事件，用例编写分支返回空 `rounds`/`cases`，只给文档与判决。

## Goals / Non-Goals

**Goals**

- 在用例编写报告里按时间回放模型过程：思考、文本、工具调用、模型调用、SOP 步骤、验收判决。
- 复用现有事件读取与详情格式化，不新增表、不重复存储。
- 报告体积可控：单条详情节流，完整文档只出现一次。

**Non-Goals**

- 不做实时流式回放（任务运行中仍按现有轮询/报告缓存机制）。
- 不把事件流做成可编辑/可重跑的控制台。
- 不改变设备执行任务的报告结构。

## Decisions

### D1 复用 `_load_events` + `_item`，新增 `_case_events`

`_case_events` 对每条事件调用 `_item`，把 `role_kind` 用 `_role_kind` 重新映射（`case_writer_role`→`case_writer`，`case_verifier_role`→`verifier`），移除 `handover` 字段，结构化交付的工具调用详情替换成「完整文档见生成的测试用例」提示；思考/文本详情保留全文。前端对超过 600 字的详情提供「展开全文 / 收起」。理由：事件格式化逻辑已经覆盖思考/文本/工具/模型调用，无需重新实现。

### D2 事件流放 `events` 字段，不塞进 `rounds`

设备任务的 `rounds` 以 YAML 用例步骤为单位，用例编写任务没有 YAML 步骤；直接返回扁平 `events` 更符合"看过程"的诉求，也避免前端误用设备轮次渲染。`rounds`/`cases` 继续为空。

### D3 前端用独立事件流区块

在「生成的测试用例」之后渲染「模型事件流」，每条显示时间、角色徽章、事件标签、模型、状态、次数与 `<pre>` 详情。`<pre>` 设 `max-height: 320px; overflow: auto; white-space: pre-wrap`，避免长思考文本撑破页面。

## Risks / Trade-offs

- [报告 payload 变大] → 结构化交付正文去重；思考/文本全文保留但默认折叠在 320px 框内，用户按需展开；后续如仍觉过大，可改成单事件按需拉取。
- [思考文本包含 system-reminder] → 如实展示，便于判断模型是否被提醒干扰；不隐藏。
- [事件很多时页面很长] → 每条详情框内滚动，事件本身按时间排列，后续可加折叠/筛选。

## Migration Plan

纯增量：部署后新报告带 `events`，旧报告/设备任务无该字段，前端按空数组处理。回滚只需移除 `events` 字段与 UI 区块。

## Open Questions

无。
