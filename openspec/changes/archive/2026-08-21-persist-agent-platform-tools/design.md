## Context

- 工具注入链路：`agent_factory._build_toolkit` → `_resolve_enabled_tools`（无 AITool(platform) 记录时按安全兜底只注入 `read_only=True` 的工具，有记录时按记录名注入）→ `build_platform_tools` 实例化。`save_case`/`save_api_test_case` 为写工具（`read_only=False`）。
- 前端编辑保存现状：`AgentDetail.vue` `save()` 编辑模式 `delete payload.tools`，注释称"编辑模式工具经独立 API 管理"——但 save 流程无任何同步调用，勾选结果只存在本地 `selectedPlatformTools` Set 中；创建模式正常（`payload.tools` → `create_agent` 建 AITool 记录）。
- 后端 `update_agent` 已有 `if "tools" in data: sync_agent_tools(...)`（全量 diff，波及 MCP/Skill 记录及其 config_json，含 skill 目录路径）。
- 仓库自带 `migrate_platform_tools` 管理命令：为 active 且缺平台工具记录的智能体补全全部 TOOL_SCHEMAS 记录（enabled=True），幂等（只补缺）。动机与问题背景见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- 编辑智能体保存时，平台工具勾选结果真实落库（补齐前端注释承诺的"独立 API"）。
- 修复后智能体 04 立即获得 `save_case` 等写工具（回填数据），且原有只读工具行为不变。
- 同步逻辑只触碰 `tool_type='platform'` 记录，MCP/Skill 副本零影响。

**Non-Goals:**

- 不改变"无记录 → 只读工具兜底"的安全语义（PRD-08 v6.5 口径）。
- 不做工具粒度（单个工具）的勾选 UI，维持现有"按模块勾选"粒度。
- 不新增路由/端点，复用既有 `POST /ai/agents/{id}/update`。
- 不动创建模式（isNew）既有保存路径。

## Decisions

**D1：新增独立契约字段 `platform_tools`，而非复用 `tools` 字段。**
编辑模式若复用 `tools` 会触发 `sync_agent_tools` 全量 diff：前端必须回传 MCP/Skill 副本的完整 `config_json`（含 skill `dir_path`），任何形状漂移都会改写或误删已导入工具；且 `tools` 语义历史上表示"清空全部工具"。独立字段只同步 platform 类型记录，语义单一、风险最小。备选（前端全量回传 `tools`）已排除。

**D2：同步实现为 platform 类型内的 diff，而非全删全建。**
删除不在勾选集合中的 platform 记录、创建缺失的（enabled=True）、已有但 disabled 的置回启用——保留主键，幂等，可安全重复调用。名字按 `TOOL_SCHEMAS` 过滤，防止垃圾记录入库（无效名字在注入侧本就无效果）。

**D3：数据回填复用 `migrate_platform_tools` 命令（dry-run 先行），不手写数据脚本。**
该命令即为"补齐缺记录智能体的全部平台工具"场景设计；智能体 04 无记录 → 回填后 26 个工具全部注入，保留其当前只读工具行为并新增写工具，与 PRD v6.5 兜底口径衔接。写工具执行仍受 HITL 确认与 user_id 校验保护。

**D4：端到端验证优先走真实对话（智能体 04 经 AgentScope 调用 `save_case` 创建 TC-NAV-004）；模型未调用工具时回退 handler 直建（`tool_registry` 同一代码路径）。**
真实对话能证明"模型可见并实际调用 save_case"这一用户可感知行为；handler 直建保证交付确定性（用户已确认保留 TC-NAV-004）。

## 模块防火墙自检

- 跨 App import：本 change 不新增跨 App import（`sync_platform_tools` 在 `apps/ai_assistant/api.py` 内，只操作本 App 的 `ai_tools` 表；save_case 执行路径沿用既有 `case_manager.api` 出口）。✅
- 禁止跨 App import service/runner/consumer/state_machine：未引入。✅
- INSERT/UPDATE/DELETE 收敛到 api.py：`sync_platform_tools` 即 api.py 函数，View 只传参调用；前端不直连数据库（经 `djangoClient` → `/ai/agents/{id}/update`）。✅
- 仪表盘不做写操作 / 通道收敛：无 WS/SSE 通道变更。✅

## Risks / Trade-offs

- [回填后智能体 04 获得全部 26 个平台工具（含 `run_test`/`acquire_device` 等写工具）] → 写工具有 HITL 确认兜底；用户可在修复后的编辑页按模块取消勾选。
- [AD001（biz=False）同样被建记录] → `_build_toolkit` 在 `enable_business_tools=False` 时不注入，无副作用。
- [编辑模式清空全部勾选 → `platform_tools=[]` 删除全部 platform 记录] → 语义正确：回到只读工具兜底，与"无记录"状态一致。
- [契约字段 `platform_tools` 为新增入参] → 非破坏性；前端旧版本不发该字段，后端 `update_agent` 跳过同步，行为与现状一致。
