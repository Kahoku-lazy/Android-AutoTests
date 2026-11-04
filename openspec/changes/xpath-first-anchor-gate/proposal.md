## Why

TASK-184/186 的真实记录里，`xpath_action` 只被调了 9 次，命中 5 次（56%）：一次是 App 把文案写成「睡 眠」，模型按「睡眠」查不到；一次是「定时」同时命中 2 个节点，模型还得自己猜点哪一个。于是它退回视觉估坐标，`mark_dot` 从 33 涨到 49 次，其中 11–22 次是「打点没打准又重打」。

同时 `mark_dot` 只是"看一眼"，并**没有强制**：模型不核对也能直接点，点错就进了别的页面，只能靠后面几趟截图才发现。

要的是：**能定位就用 xpath 精确定位；命中多个就把每个点都标在图上让模型挑；没确认过锚点的操作一律不许执行。**

## What Changes

- **xpath 结果可标记**：`xpath_action` 增加 `confirm`（默认开）。命中 1 个时返回带红点的图、像素坐标与帧 token；命中多个时**把全部命中画在同一张图上**，每个点带序号（从 1 起，按 y 再按 x 升序），返回 `items[]`（序号、文本、像素坐标）与 token。
- **文本归一化匹配**：精确匹配未命中时，去掉空白、全角转半角、忽略大小写再匹配一次（治「睡 眠」这类写法），并允许一次给最多 3 个候选表达式，一次 dump 全部试完。
- **点击必须带锚点确认**：`click_ratio` / `tap_screen` MUST 携带有效 `token`；没有 token、token 过期或不属于该设备时 MUST 返回可读 error 且 **MUST NOT 产生任何手势**。`tap_screen` 增加 `index`，用于点第 N 个已标记的命中点；只有一个点时 `index` 可省略。
- **多点帧缓存**：一帧保存多个标记点（序号 → 像素坐标），点击时按 `index` 取用；仍是进程内缓存、90 秒有效、每设备最多 2 帧。
- **执行提示词改优先级**：先按目标文案走 xpath（含归一化匹配），命中后看编号图挑 `index`，带 token 点击；xpath 全部未命中或无文案控件（开关、滑块）才用视觉估算 + `mark_dot`；**没有 token 的操作视为未确认锚点，禁止执行**。

## 关联文档

无 PRD 需求编号。触发于 2026-11-04 对 TASK-184/186 的耗时与调用链分析（`dev_docs/DEV_TEST/分析-结构化任务184耗时构成-20261104.md`）。约束来源为根 `AGENTS.md`「一次提交只做一件事」与 `engines/agents/AGENTS.md`「工具经 `tools_config.py` 分配」。

## Capabilities

### New Capabilities

（无：本次不新增能力，只改 xpath 与点击类工具的契约。）

### Modified Capabilities

- `ai-device-action`: 新增「xpath 命中点可标记、可按序号点击」，并把点击类动作的 `token` 从可选改为必填（硬门槛）。
- `role-prompt-guardrails`: 执行提示词改为 xpath 优先、多命中看编号图挑选、未确认锚点禁止操作。

## Impact

- 修改：`engines/agents/tools/tool_device.py`（`xpath_action` 的 confirm/多候选/归一化匹配、`tap_screen` 的 index 与 token 门槛）、`engines/agents/tools/tool_frame_cache.py`（一帧多点）、`engines/agents/tools/tool_img_b64.py`（多点标记 + 编号绘制）、`engines/agents/config/data/prompts/UI_EXECUTOR_PROMPT.md`。
- 新增：无新工具、无新模块（标记绘制复用现有图片工具）。
- 不改：`tools_config.py` 的工具名与分组、报告与前端、数据库表结构、日志检查工具、坐标核对工具（`mark_dot` 仍是视觉路径的单点核对，契约不变）。
- 测试：`tests/engines/agents/test_tool_device.py`、`test_tool_img_b64.py`、`test_frame_cache.py`、`tests/graybox/unit/test_role_prompt_guardrails.py`。
- 行为：**BREAKING**（仅对执行角色）：不带 token 的 `click_ratio` / `tap_screen` 由"可用"变为"报错且不点击"，这是本次的核心硬规则。
