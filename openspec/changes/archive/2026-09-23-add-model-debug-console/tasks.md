## 1. 后端：装配 service（命令与 HTTP 同源）

- [x] 1.1 新增 apps/ai_assistant/model_debug.py：ROLES = (planner, executor, verifier) 与 build_role_debug_configs(agent)——每角色回模型连接摘要（provider / model_name / vision / has_api_key，脱敏）、系统提示词、工具子集（RoleSpec.tool_names + 是否被平台停用）、以及技能清单与知识库来源。验证：3.1 断言三角色工具清单与 engines/ai/agentscope/config.py 常量一致。
- [x] 1.2 management/commands/model_test.py 的装配改为复用该 service（三角色 ModelConfig / tools / skill_dirs / system_prompts 全部取自同一处），命令行为不变。验证：单测断言命令与服务取自同一构造；python manage.py model_test --help 正常。
- [x] 1.3 run_role_chat(agent, role, text)：DebugRole(AgentRole) + tools=[] + asyncio.run 同步返回文本；模型未配置时抛可读错误。验证：3.1 的对话用例（mock 模型层）。

## 2. 后端：视图与路由

- [x] 2.1 新增 views_model_debug_drf.py：GET /api/ai/model-debug/<role>/ 返回该角色只读配置；POST /api/ai/model-debug/<role>/chat 返回单轮回复。两个端点均仅超管。验证：3.1 的 200 / 403 用例。
- [x] 2.2 urls.py 注册两条路由（model-debug/<str:role>/ 与 .../chat/）；role 不在白名单 → 400 且不触发模型调用；缺模型配置 → 400 可读错误。验证：3.1 的参数与错误用例。
- [x] 2.3 响应脱敏复核：响应体不含 api_key / base_url 明文。验证：3.1 的断言 + 真实请求抽样。

## 3. 测试

- [x] 3.1 新增 tests/graybox/unit/test_ai_model_debug.py：三角色工具子集正确（planner 页面流工具 / executor 视觉工具集 / verifier screenshot_page）；技能标注三模型共用；知识库来源来自 agent 启用清单；脱敏无 api_key；非超管 403；非法 role 400；缺配置 400；对话不落库（AIMessage/AIConversation 计数不变）；改系统提示词后回复随之变化（mock 模型层）。验证：pytest tests/graybox/unit/test_ai_model_debug.py 全绿。

## 4. 前端：来源入口与路由

- [x] 4.1 helpers/toolbox-assembly.ts 新增第四个来源（key debug，name 模型调试，gateKey 空）并扩展 AssemblySourceKey 类型。验证：4.3 spec 断言来源列表含该项且无总闸。
- [x] 4.2 components/ToolboxPanel.vue 在 activeSource === 'debug' 时渲染三张角色卡（角色名 / 模型名 / 工具数 / 视觉徽标），点卡跳 /ai-assistant/toolbox/models/:role。验证：4.3 spec + 浏览器复验。
- [x] 4.3 routes.ts 增 /ai-assistant/toolbox/models/:role（name ai-model-debug），constants.ts 增 modelDebugRoute(role) 与归属标注文案常量。验证：npm run typecheck + 对应 spec。

## 5. 前端：调试页

- [x] 5.1 api/toolbox.ts 增 fetchModelDebugConfig(role) 与 chatWithModelDebug(role, text)，后者单独设 300000ms 超时。验证：5.4 spec 断言路径与超时。
- [x] 5.2 composables/useModelDebug.ts：加载角色配置（loading/错误态）、发送消息（前端内存消息列表、发送中态、错误透出）。验证：5.4 spec。
- [x] 5.3 新增 ModelDebugPage.vue 与 ModelDebugPage.style.css：顶部回退到工具箱 + 角色名；四块只读（提示词 Markdown / 模型连接 / 工具清单含只读写与停用标记 / 技能与知识库含归属标注）+ 对话框。验证：5.4 组件 spec + npm run build + check-style-gates。
- [x] 5.4 新增 frontend/tests/ai-assistant/p0/useModelDebug.spec.ts 与 ModelDebugPage 组件用例：路径与超时、消息列表追加、错误透出、归属标注文本可见、工具清单渲染。验证：npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts 通过。

## 6. 文档

- [x] 6.1 AI 助手接口文档补两个端点：鉴权（仅超管）、role 白名单、单次超时 5 分钟、脱敏字段、缺配置 400 文案。验证：逐条与 views_model_debug_drf.py / model_debug.py 对照一致。

## 7. 门禁

- [x] 7.1 后端门禁：python manage.py check、makemigrations --check、ruff check、ruff format --check（改动路径）、pytest tests/graybox/unit。验证：全部通过、无新增告警。
- [x] 7.2 架构门禁：python tools/gen_arch_stats.py --check-boundaries。验证：零违规。
- [x] 7.3 前端门禁：npm run build + /vue-frontend-check 三块报告。验证：构建无错、门禁项全部有结论。
- [x] 7.4 端到端复验：真实浏览器进工具箱「模型调试」→ 打开某角色 → 改该角色提示词（加标记）→ 在对话框发问确认回复体现标记 → 核对不产生会话记录、无真机操作；并跑一次长请求确认 5 分钟超时不被中间层截断。验证：回复内容与库内提示词一致、AIMessage/AIConversation 计数不变。
