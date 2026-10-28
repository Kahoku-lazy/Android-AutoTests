# 点击前先用红点核对坐标

## Why

执行模型靠视觉估算归一化坐标，点偏了才发现，往往要重试多轮，甚至点到错误控件；错误点击还会把页面带离目标，后续步骤跟着失效。现在缺一个「点之前先看红点落在哪」的固定步骤。

## What Changes

- 新增只读工具 `mark_dot(serial, x, y, normalized=True)`：截取当前屏幕并在坐标处画红点，返回标记后的图片（base64 + media_type），不落盘。
- 把 `mark_dot` 放进执行角色常驻组，与截图、返回键一样始终可见；验收角色不装配。
- 执行提示词新增硬约束：为点击得到的坐标——自己看图估算的归一化坐标与 `xpath_action` 返回的像素坐标——MUST 先 `mark_dot` 打点核对（像素坐标传 `normalized=False`）；红点未落在目标元素上 MUST 重新确定坐标并再次标记；确认红点位置前 MUST NOT 调用点击工具。xpath 坐标核对失败时 MUST 重新取 xpath 或换定位方式，MUST NOT 按截图重估坐标。
- 工具入参是设备 serial 与坐标，而不是图片 base64：执行模型收到的是图片块、拿不到 base64 原文，只有让工具自己截图，才能形成「打点 → 看图 → 确认 → 点击」闭环。
- 保留 `mark_dot_b64` 纯函数（base64 进 base64 出）供平台代码直接调用。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `executor-tool-groups`：常驻组在 `screenshot_page` / `press_key` 之外加入 `mark_dot`。
- `ai-screen-vision`：新增坐标核对工具的需求（只读取、返回标记图片、仅执行角色可见）。
- `role-prompt-guardrails`：执行提示词新增「点击前必须先用红点核对坐标」的硬约束。

## Impact

- 引擎工具层：`engines/agents/tools/tool_img_b64.py`、`engines/agents/tools_config.py`（常驻组）。
- 提示词：`engines/agents/prompts/executor_prompt.py`。
- 测试：`tests/engines/agents/test_tool_img_b64.py`、`tests/graybox/unit/test_role_prompt_guardrails.py`。
- 不影响后端、前端、数据库。
- 成本：每次点击前多一次截屏（约 0.5~1s，视设备而定）与一次图片输入，模型费用相应增加；换来的是少一次错点与重试。
