## Context

见 `proposal.md - Why`。与本设计相关的现状约束（代码事实）：

- 调试对话入口：`apps/ai_assistant/model_debug.py` 的 `run_role_chat()` —— 校验角色配置 → 需要设备的角色先 `require_available_device()` 选设备 → `build_debug_role()` 挂该角色真实工具 → `asyncio.run(role_obj.ask(prompt))` → 返回 `{role, label, model_name, reply, thinking, tool_usage, usage, cost}`；`tool_usage` 是引擎回溯出的 `call` / `result` 行（result 行带 `output`、截图行带 `screenshot_path`），**原样返回、后端不截断**（前端展示时按 160 字符截断）。
- 动作工具在真正调设备前打点并把 `action_time` 写进返回 JSON（`_with_action_time`），只读工具不打点。
- 日志证据：`DeviceLogEvidence.open_window / read_window`（`apps/ai_assistant/log_evidence.py` 装配，采集句柄在 `engines/device/logbus.py`）。`read_window` 需要**已开启的窗口**（未开窗抛 `LogWindowMissing`），以「动作发出时刻 + 阈值」构造取证窗并出等级；`wait_seconds` 用于等到「最后一次动作 + 阈值」。
- 上一份变更已把配对逻辑实现为 `engines/ai/agentscope/workflow.py` 的私有纯函数（`_extract_action_time` / `_build_executor_log_check`），前端展示组件 `StepLogCheck.vue` 与判空纯函数 `hasLogCheck()` 已在任务详情页用起来。

## Goals / Non-Goals

**Goals:**

- 调试台的每一次点击都能直接读到「点击前时间点 + 点击后截图路径 + 该时间点后 5 秒日志」，且与任务步骤证据同源同口径。
- 零额外模型调用 / 零额外 token；模型漏抄也照常有。
- 未产生点击的对话、以及其它角色（规划 / 验收）的对话表现不变。

**Non-Goals:**

- 不改任务步骤链路的既有行为与展示（两处并存，各自成立）。
- 不改验收模型输入、5 秒阈值、证据等级与合并排序口径。
- 不改无线端口面板的监听开关语义：平台 MUST NOT 为了调试去打开端口。
- 不为调试台新增「断言」概念（因此没有 `log_check` 标记：有点击就带日志）。

## Decisions

**决策 1：配对与切片逻辑提到共享模块 `engines/ai/agentscope/logcheck.py`，两处调用同一份实现。**

- 做法：把 `_extract_action_time` 与 `_build_executor_log_check` 从 `workflow.py` 迁到新模块并去掉下划线（`extract_action_time` / `build_executor_log_check`），`workflow.py` 改为 import 使用；调试台侧同样 import。
- 理由：规则是「点击之后第一张截图、不重复分配、切片只取本轮新增」——这套规则两处必须完全一致，否则调试台的证据与任务里看到的会对不上。放两处实现迟早漂移。
- 备选：调试台直接 import `workflow.py` 的私有函数——跨模块用下划线私有名，且会把整条工作流依赖拖进调试路径。不取。

**决策 2：开窗放在对话之前，读窗放在对话之后；只在「本轮确实有点击」时把日志并进响应。**

- 做法：`run_role_chat` 里，需要设备的角色在 `role_obj.ask()` **之前**调 `ensure_log_evidence()`（返回 `None` 表示无端口在监听）并 `open_window(device, label="model-debug")`；`ask()` 返回后，用共享纯函数从**全量** `tool_usage` 算出 `clicks`（调试台一次对话就是一轮，无「上一步遗留」问题，`skip_results=0`）；若 `clicks` 非空且 provider 存在，则 `read_window(device, window_id, action_times=[各点击时刻], wait_seconds=阈值)` 得到证据，放进 `log`。
- 理由：与生产链路同口径（动作前开窗 → 动作后读窗），且窗口能同时覆盖本轮多次点击；读窗等到「最后一次点击 + 阈值」避免慢日志漏采。
- 备选：① 用只读日志工具 `read_device_log(at=..., seconds=5)` 按时间点直接查——那条路返回的是「行 + 关键词命中」，没有动作前基线与等级标注，口径会与任务证据不一致。② 不读窗口、只把工具返回里的日志片段给用户——那是模型视角，不是平台证据。均不取。

**决策 3：响应新增键名 `log_check`，形状与任务过程记录同形。**

- 形状：`{"clicks": [{"action_time": str, "screenshot_path": str}], "log": <证据块> | None}`；`clicks` 为空时整个键不出现。
- 理由：与任务侧同名同形，前端复用同一组件与判空纯函数，不产生第二套 DTO 语义。
- 备选：改名 `evidence` / `debug_log`——同一概念两个名字，读代码的人要额外对一次。不取。

**决策 4：无端口在监听时如实不给日志，点击证据照旧。**

- 做法：`ensure_log_evidence()` 返回 `None` → `log` 为 `None`，`clicks` 照常产出（时间点与截图路径来自工具结果，不依赖日志总线）。
- 理由：时间点与截图是工具事实，任何情况下都有；日志取决于用户在「无线端口」里有没有开监听，平台不能替他开。如实呈现「无日志证据」比假装有更有用。
- 备选：无日志时干脆不产出该块——用户会以为「没有点击」，把两件事混成一件。不取。

**决策 5：前端复用 `StepLogCheck.vue`，在助手消息内渲染。**

- 做法：`ModelDebugReply` 与消息 DTO 增 `log_check`；`ModelDebugPage.vue` 在助手消息的「回复」区块之后按 `hasLogCheck()` 渲染该组件。
- 理由：同一份内容两处展示，复用组件才能保证文案与等级口径一致（该组件已把「该次点击后未截图」等文案集中在常量里）。
- 备选：调试台单独写一个精简列表——会立刻出现两套文案与两套等级标签。不取。

## 模块防火墙自检

- 跨 App import：无。改动在 `apps/ai_assistant`（自身）与 `engines/ai/agentscope`（引擎层）；调试台对日志总线仍只经 `log_evidence.py` 的装配对象，不直接操作采集句柄。
- 写库收敛：不新增任何写库路径（调试对话本就不落库，本变更 MUST NOT 改变这一点）。
- 引擎边界：引擎侧只新增一个纯函数模块，不 import `apps.*`、不 import `engines.device.*`；日志读取仍由 Django 侧的提供者注入。
- 通信通道：无新增端点、无新 WS 事件；沿用既有 `POST /api/ai/model-debug/{role}/chat`，仅响应多一个键。
- 前端：不新增 HTTP 出口，不直连数据库。

## Risks / Trade-offs

- [读窗等待使调试对话比现在晚约 5 秒返回] → 前端本就不设等待上限（既有要求），期间保持「模型运行中…」状态；如实知会用户。若某角色不需要设备（规划），不触发任何等待。
- [长对话里模型点了很多次，`clicks` 与日志块变长] → 与任务侧同一上限口径（工具轨迹与证据块本就只展示必要字段）；日志仍受既有窗口合并与条数控制。
- [`screenshot_page` 的结果在引擎侧被瘦身（只留摘要字段），点击↔截图配对依赖 `screenshot_path` 字段本身] → 瘦身白名单里保留了 `screenshot_path`，配对不受影响；用例覆盖「点击后无截图如实标注」。
- [调试台产生的证据窗口进入总线窗口注册表，可能影响后续任务读窗] → 任务侧按自己的 `window_id` 读窗（`open_window` 每次返回新 id），不使用 `latest` 回退；调试台也持有自己的 id，互不干扰。用例覆盖「按 window_id 读取」。
- [模型在调试台点击了设备但没有截任何图] → 如实标注「该次点击后未截图」，日志照常按时间点后 5 秒给出（时间点不依赖截图）。
