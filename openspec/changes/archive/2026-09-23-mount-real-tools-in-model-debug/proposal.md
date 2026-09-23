## Why

模型调试页的对话跑的是「空工具集 + 不碰真机 + 5 分钟上限」的最小面：它调不调工具、调哪个工具、参数对不对、真机能不能跑通，全都看不到——而这几件事恰恰是「测试单个模型的效果」的全部内容。更关键的是**调试口径比生产更严**：平台生产链路里设备写工具本来就自动放行（`apps/ai_assistant/tools.py:433` 的 `AUTO_ALLOW_TOOLS` 明确写「设备管理/控制类工具自动放行（不走 HITL）」），设备串也是在生产同口径下经提示词下发（`engines/ai/agentscope/model.py:590/661` 的 `当前设备 serial：{serial}`）。于是「调试通过」与「生产可用」之间没有可比性。

## What Changes

- **挂载该角色真实工具子集**：调试角色不再以空工具集运行，工具名与 `RoleSpec.tool_names` 同源（规划 = 页面流工具、执行 = 视觉/设备工具 14 个、验收 = 截图工具）。
- **展示工具调用轨迹**：助手消息新增「工具调用」区块，逐条给出工具名 / 入参 / 结果状态 + 只读·写徽标（数据来自引擎已有的 `RoleResult.tool_usage`）。
- **先选定设备**：工具子集里存在声明 `serial` 参数的工具时，页内必须选一台设备；候选 = 对请求者可见 + 状态在线 + 未被占用（与平台工具调试页同口径）；后端再次校验，不合法返回 4xx 且**不触发模型调用**。规划模型不需设备。
- **发送前一次性授权**：确认框列出目标设备与将挂载的写工具数量；取消则不发请求。
- **serial 以生产同口径进入模型输入**：`当前设备 serial：{serial}` 前缀，不新增强制覆盖模型传参的包装器。
- **去掉单次 5 分钟上限**：前端不再对调试对话设等待上限；页面文案改为如实描述当前行为（挂载真实工具 / 会真实操作所选设备）。
- **不**改变 Skill 与知识库的挂载行为（仍不挂）；**不**做逐次工具调用的 HITL；**不**改变设备池占用状态；**不**动接口信封、权限（仍仅超管）与非设备相关工具。

## 关联文档

- PRD-需求总纲（AI 助手条目）
- 前置变更：add-model-debug-console、relayout-model-debug-page、distinguish-model-reply-and-thinking
- 用户口径（本轮确认）：挂全部真实工具 + 先选定设备；不设前端上限；仍只跑被选中的单个模型

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- ai-model-debug: 新增三条要求——「调试对话按该角色真实装配运行」（含工具调用轨迹）「需要设备的角色须先选定设备并获得一次性授权」「调试对话不设前端等待上限且如实描述行为」。既有行为需求（配置读取 / 仅超管 / 单角色 / 不落库 / 页面三层层级 / 回复与思考分块）不变，其中「不挂工具、不碰真机、单次最长 5 分钟」三条被本变更取代。

## Impact

- 后端：apps/ai_assistant/tools.py（候选设备口径上移）、model_debug.py（真实工具装配 + serial 校验与注入 + 透出 tool_usage）、views_model_debug_drf.py（请求体 serial）、views_tool_debug_drf.py（改为复用上移后的候选函数）。无迁移。
- 前端：frontend/src/modules/ai-assistant 下 ModelDebugPage.vue / .style.css（设备下拉 + 授权确认 + 工具调用轨迹 + 文案）、api/toolbox.ts（chat 请求带 serial、返回 tool_usage、去掉固定超时）、composables/useModelDebug.ts、constants.ts。
- 测试：后端 tests/graybox/unit 新增调试装配 / serial 校验用例；前端 frontend/tests/ai-assistant/p0/useModelDebug.spec.ts 增设备选择、授权确认、轨迹展示、无固定超时断言。
- 依赖 / 路由 / 迁移：无。
