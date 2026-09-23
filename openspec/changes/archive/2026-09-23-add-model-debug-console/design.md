## Context

三角色的真相源（已核对代码）：

| 维度 | 位置 |
|---|---|
| 提示词 | AIAgent.prompt_planner / executor / verifier（迁移 0038 起 DB 为唯一真相源） |
| 模型连接 | route_configs.device_control.{role} → engine_adapter._model_spec() |
| 工具子集 | engines/ai/agentscope/model.py 的 RoleSpec.tool_names：planner=DEVICE_PLANNER_TOOLS（页面流工具）、executor=VISION_TOOLS（14 个设备/视觉工具）、verifier=VERIFIER_TOOLS（screenshot_page） |
| 角色差异 | executor：vision=True、max_image_num=5、max_iters=8；planner / verifier 无 vision |
| 技能 | engine.py 把同一份 req.skill_dirs 交给三个角色 → **三模型共用**，无 per-role 分配 |
| 知识库 | enable_knowledge_base / knowledge_sources 只出现在 api / models / serializers / views.tool_gateway → 执行链路**不读**，仅作为工具网关的 agent-config 下发 |

可复用的现成装配：management/commands/model_test.py 的 _build_device_models()（三角色 ModelConfig + build_tool_specs + list_enabled_skill_dirs + 三角色 system_prompts）。前端同构参照：ToolDebugPage.vue + 路由 /ai-assistant/toolbox/tools/:toolName。

## Goals / Non-Goals

**Goals:**

- 单个角色此刻生效的配置在一个页面里如实可见（提示词 / 模型 / 工具子集），并能用对话确认"改了提示词到底生效没有"。
- 不触碰真机、不消耗工具、不产生会话记录。

**Non-Goals:**

- 不做流式输出；不做真机执行或"允许调用工具"开关；不把 RAG 接进执行链路；不做 per-role 技能分配；不落库调试对话；不做费用统计与历史留痕。

## Decisions

**D1 新能力独立（ai-model-debug），不复用 ai-platform-tool-debug。**
理由：调试对象是"角色装配"（提示词 + 模型 + 工具子集），不是"平台工具的入参 schema"；两者页面骨架可复用，契约必须分开。

**D2 装配抽取为共用 service，命令与 HTTP 同源。**
新增 apps/ai_assistant/model_debug.py：build_role_debug_configs(agent) 产出三角色的只读配置（模型连接摘要、提示词、工具子集 + 平台停用标记、vision、技能清单、知识库来源）；run_role_chat(agent, role, text) 负责单角色对话。management/commands/model_test.py 改为复用同一 service。
理由：避免"命令行能跑、页面跑不通"这类装配漂移；单测可断言两者取自同一函数。

**D3 调试对话不挂任何工具。**
用通用 DebugRole(AgentRole)（只调 _execute(text)）承载该角色的 ModelConfig 与系统提示词，tools=[]；**不使用** ExecutorRole.run（它会拼真机 serial 指令）。备选：挂真工具并传假 serial——会把真机指令喂给模型，违背"不碰真机"，舍弃。

**D4 单次超时 5 分钟（300s）。**
DRF 同步视图不设短超时；前端只在这一个请求上把 axios timeout 覆盖为 300000（不动 api-client 全局 120s）。理由：思考模型 + 长提示词单轮可能远超 120s；流式留待后续单开。

**D5 对话不落库。**
不进 AIConversation / AIMessage；消息仅存前端内存，刷新即清。理由：调试台的定位是"看一眼就走"，落库会把它变成第二条对话线并带来清理与权限问题。

**D6 脱敏口径。**
模型连接只回 provider / model_name / vision / has_api_key（布尔）；api_key 与 base_url 明文一律不返回。

**D7 权限与错误。**
两个端点均仅超级管理员（复用现有 _is_superuser 校验）；非法 role → 400；模型连接不完整 → 400 且沿用 model_test 的中文文案（例如「规划模型(planner)」的 model_name 未配置…）。

**D8 前端接线。**
ASSEMBLY_SOURCES 增第四项 { key: 'debug', name: '模型调试', gateKey: '' }；ToolboxPanel 在 activeSource==='debug' 时渲染三张角色卡；新页 ModelDebugPage.vue 复用 ToolDebugPage 的版式与 T0 令牌；routes.ts 增 /ai-assistant/toolbox/models/:role；constants.ts 增 modelDebugRoute(role) 与"归属标注"文案常量。

**D9 "归属标注"是硬约束。**
技能区块显示「三模型共用」，知识库区块显示「执行链路当前未挂载 RAG」——文案集中在 constants.ts，并由 spec 场景守护，避免误导。

## 模块防火墙自检

- 后端只动 apps/ai_assistant（新 service + 新视图 + urls + 命令复用）；无跨 App import，无跨 App 写库，无新模型、无迁移。
- 前端只动本模块（helpers / components / composables / api / routes / constants）；HTTP 仍只经 shared/api-client。
- 复用既有引擎角色基类（engines/ai/agentscope/model.py）经 apps/ai_assistant 层调用，未新增引擎依赖方向。

## Risks / Trade-offs

- [命令与页面装配漂移] → D2 抽 service 单点；单测断言两处使用同一构造。
- [长提示词 + 视觉模型推高成本] → 仅超管、单轮、不落库；页面显式标注所用模型名。
- [300s 同步等待被中间层截断] → 端到端复验里专门跑一次长请求；若被截断则只调整代理超时，不改契约。
- [不挂工具 ⇒ 工具相关行为测不出] → 已列入非目标；页面明确展示工具清单（只读），需要真机验证时仍走任务。
- [知识库区块易被误解] → 强制标注 + spec 场景守护。

## Migration Plan

无数据库迁移、无依赖变更。发布：新增两个端点与一个页面；前端旧版本不受影响。回滚：删两条路由与页面文件即可，既有装配链路不受影响。

## Open Questions

（无）
