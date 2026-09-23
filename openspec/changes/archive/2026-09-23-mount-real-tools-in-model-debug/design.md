## Context

现状（本变更前的调试装配）：

    # apps/ai_assistant/model_debug.py build_debug_role
    spec = RoleSpec(role=base.role, prompt="", tool_names=(), vision=base.vision, ...)
    return _DebugRole(config=model_cfg, tools=[], user_id=..., skill_dirs=[], system_prompt=...)

- `run_role_chat` 不接收 serial，直接 `role_obj.ask(content)`，返回 reply/thinking/usage/cost（未透出 `tool_usage`）。
- 前端 `MODEL_DEBUG_CHAT_TIMEOUT_MS = 300_000`，页面文案「只发这一个角色 · 不挂工具 · 不碰真机 · 不落库 · 单次最长 5 分钟」。

生产口径（本设计要对齐的真相源）：

- 设备写工具**自动放行、不走 HITL**：`apps/ai_assistant/tools.py:433 AUTO_ALLOW_TOOLS`（10 个写工具全在其中）。`PlatformFunctionTool.check_permissions` 只对「非只读且非 auto_allow」的工具返回 ASK，今天没有工具落在这个分支。
- 设备绑定靠**提示词注入**：`engines/ai/agentscope/model.py:590`（执行）、`:661`（验收）分别以 `当前设备 serial：{serial}` 开头拼用户输入；工具 handler 的 serial 由模型按提示词传入，生产链路同样不强制覆盖。
- 候选设备口径：`apps/ai_assistant/views_tool_debug_drf.py:44 _available_device_options`（`device_pool.api.list_devices` 过滤 status=ONLINE 且无 occupied_by）。
- 引擎在单次 reply 后已把工具调用/返回收进 `RoleResult.tool_usage`（`{type: call|result, name, input|output|state}`，见 `model.py:406-435`），无需新增采集。

约束：仅超管可用；不改接口信封；不引入新依赖；调试对话仍不落库（落库另开一单）。

## Goals / Non-Goals

**Goals:** 调试装配与生产工具子集同源；能看到工具调用轨迹；真机操作前必须有设备与一次性授权；不再有固定等待上限；页面文案与真实行为一致。

**Non-Goals:** 不挂 Skill 与知识库（用户列出的限制不含这两项；挂 Skill 会改变调试输入面与 token 预算，另行决定）；不做逐次工具调用的 HITL；不改设备池占用记账；不改 SSE/流式；不改 `AUTO_ALLOW_TOOLS`；不动落库（另一单）。

## Decisions

**D1 工具子集取自角色规格，不另抄一份。**
`build_debug_role` 把 `tool_names=()` 改回 `base.tool_names`、`tools=[]` 改为 `build_tool_specs()`，由 `AgentRole._select_tools` 按子集筛选。理由：与生产装配同一入口（`build_device_models` 用的也是 `build_tool_specs()`），不会漂移。备选「给调试页单独维护一份工具名清单」——必然漂移，否。

**D2 候选设备口径上移到 `tools.py`，两处共用一份实现。**
把 `_DEVICE_OPTIONS_SOURCE` / `_available_device_options` / `_resolve_param_options` 从 `views_tool_debug_drf.py` 迁到 `tools.py`（候选来源词表 `DEBUG_PARAM_OPTIONS` 本来就在那里），视图改为调用；`model_debug.py` 复用同一函数做后端校验。理由：调试对话与平台工具调试页必须同口径，两份实现必然分叉。

**D3 serial 是否必填，按「工具签名是否含 serial 参数」判定。**
`needs_serial = any("serial" in signature(TOOLS[name][0]).parameters for name in 子集)`。已核对：`list_page_flows(query)` / `get_page_flow(doc_id)` 无 serial（规划模型不需要设备），执行与验收子集均含 `screenshot_page(serial, ...)`。备选「按角色名硬编码」——新角色会漏；「用 `DEBUG_PARAM_OPTIONS` 判断」——该表只登记 9 个设备管理工具，**未登记 `screenshot_page`**，会误判验收模型不需要设备，故不采用。

**D4 serial 以生产同口径注入，不加强制覆盖的包装器。**
拼 `f"当前设备 serial：{serial}\n{content}"`。理由：与 `ExecutorRole.run` / `VerifierRole.run` 完全同形；生产也不强制覆盖模型传参，调试页若强制，反而看不出「模型会不会漏传/传错 serial」这个真实问题。

**D5 授权 = 发送前一次确认，不做逐次工具调用的 HITL。**
平台已在 `AUTO_ALLOW_TOOLS` 明确让设备写工具不走 HITL（生产里「建任务」本身就是那次授权）；调试页把「点发送前的确认」作为等价授权。逐次确认需要把调试对话从单次 POST 改成 SSE + `require_confirm`/`confirm_result` 回合（平台对话链路已有该机制），属独立的大变更，不在本单。

**D6 不 acquire 设备占用。**
与平台工具调试页同口径：只做「可见 + 在线 + 未占用」的候选过滤与服务端复校，不写设备池。理由：调试中断（关页/断网）会留下脏占用，代价高于并发竞争窗口；确认框如实写明「将真实操作该设备」。

**D7 前端去掉固定超时。**
删除 `MODEL_DEBUG_CHAT_TIMEOUT_MS`，请求不再传 `timeout`（axios 默认 0 = 不限）。本地经 Vite 代理直连 daphne，无反向代理超时；若将来置于有超时的网关之后需另行评估。

**D8 工具调用轨迹作为与「回复 / 思考过程」并列的第三个区块。**
默认展开（与思考过程一致：调试页的存在意义就是看过程），标题给「工具调用 N 次」，每条含工具名 + 只读/写徽标 + 结果状态；入参与返回做长度截断。数据直接取 `RoleResult.tool_usage`，前端不重新解析。

## 模块防火墙自检

- 跨 App：`model_debug.py` 校验设备时经 `apps.device_pool.api.list_devices`（跨 App 只读走 api，合规）；不新增跨 App 内部实现 import。
- 写库：本变更**无任何写库**（不落库、不 acquire），因此不涉及 ORM 写路径。
- 前端不直连数据库；HTTP 仍只经 `api/toolbox.ts` → `shared/api-client`。
- 引擎边界：只改 `apps/ai_assistant` 的装配调用方式，不改 `engines/`；引擎的 `ask` 已存在。

## Risks / Trade-offs

- [调试页能真机写] → 仅超管 + 发送前确认（列出设备与写工具数）+ 候选排除已占用设备 + 服务端复校；文案如实告知。
- [模型传错/漏传 serial] → 与生产同风险；本单不掩盖该风险（D4 的取舍），候选唯一化降低概率。
- [长跑占住连接] → 用户明确要求不设上限；本地无代理超时。
- [工具轨迹噪音与体积] → 标题给次数、入参与返回截断；`.md-msgs` 已有独立滚动。
- [与生产仍有差异：不挂 Skill] → 已在 Non-Goals 明示，需要时另开一单。

## Migration Plan

无数据迁移、无接口路径变更（仅 `chat` 请求体新增 `serial` 且为条件必填，属向后兼容的收紧：旧前端不传 serial 时执行/验收角色会得到 4xx）。回滚 = 还原 tools.py / model_debug.py / views_model_debug_drf.py / views_tool_debug_drf.py 与前端 4 个文件。

## Open Questions

（无）
