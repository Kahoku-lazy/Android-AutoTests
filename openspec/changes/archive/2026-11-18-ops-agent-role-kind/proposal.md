# Proposal: ops-agent-role-kind

## Why

运营后台「Agent配置」列表只有名称、模型配置、系统提示词三列，运营看不出某份配置是拿来当执行者还是验收者，只能靠名称猜；而 `ai-role-registry` 的既有需求又明文禁止把「任务类型」写进角色记录本身，所以类型既不能加在 `ai_roles` 上，也不能靠改名约定。需要在不碰运行链路的前提下，给配置补一个可读、可校验的类型标签。

## What Changes

- 新增关联表 `ai_role_kinds`（一行 = 一条配置的一个类型标签），字段只有 `id`、`role`（外键指向 `ai_roles`，级联删除）、`kind`、`created_at`；`kind` 取值 `executor` / `verifier` / `planner`（执行者 / 验收者 / 规划者）。
- **一份配置只能有一个类型**（`UNIQUE(role)`），需求方已确认「同一份配置不能既是执行者又是验收者」；同时保留 `UNIQUE(role, kind)`，将来放开多类型只需删一条约束，不改表、不迁数据。
- `GET /api/ai/roles/` 响应每条记录增加 `kinds` 字段（长度 0 或 1 的数组）；`POST` / `PATCH` 入参可带 `kinds`，**整组替换**（同一事务先清后插）。路径、信封、snake_case 全部不变。
- 新建配置时 `kinds` **必填且只允许 1 项**；存量配置允许为空（显示「未分类」），由运营在页面上补齐。**BREAKING**：新建接口在不传 `kinds` 时返回 400。
- 运营后台「Agent配置」表格在「名称」后新增「类型」列（chip 呈现，空显示「未分类」），编辑抽屉增加类型选择（单选，三个选项）。
- 数据迁移按名称后缀保守回填：只回填名称明确以 `_VERIFIER` / `_EXECUTOR` 结尾的存量（当前 3 条），`CASE_WRITER_PROMPT` 等语义不明的留「未分类」，不猜。
- 运行时零改动：SOP 只读 `AIRole.system_prompt` 与 `AIRole.model_config`，`resolve_workflow()`、`AIAssistant`、`AISopWorkflow`、`engines/**` 均不动；**不**做「按类型过滤 SOP 选人」（需求方已确认不做）。

## 关联文档

无对应 PRD 编号：本变更是需求方 2026-11-18 直接提出的列表可读性需求，四条口径（1:1、新建必填、三个选项、不做选人过滤）已当面拍板。`PRD-平台总需求` 未对 Agent 配置分类编号，不虚构编号；设计细节见同变更的 `design.md`。

## Capabilities

### New Capabilities

（无——类型标签是既有角色注册能力的需求级扩展，不新开能力）

### Modified Capabilities

- `ai-role-registry`: 新增「配置的类型标签存放在独立关联表」需求（角色记录本表 MUST NOT 增加类型字段，与既有条款一致）；新增「类型取值与唯一性」「类型随配置级联删除」两条约束。
- `ops-agent-config`: 「Agent 配置列表」需求扩展为五列（名称 / 类型 / 模型配置 / 系统提示词 / 操作），新增「新建必填类型、存量允许未分类」的验收口径。

## Impact

- **后端**：`backend/apps/ai_assistant/`（`models.py` 新增 `AIRoleKind`、`migrations/0071_airolekind.py` 建表 + 回填、`services/agent_configs.py` 的 `replace_kinds` 与 `prefetch_related`、`serializers.py` 的 `kinds` 进出参、`api.py` 的 `create_role` / `update_role` 透传、`views_drf.py` 的 `RoleViewSet` 分发）。
- **前端**：`frontend/src/modules/ops-console/`（`types.ts`、`constants.ts` 列定义与选项、`agents.vue` 表格单元与抽屉表单、新增 `components/OpsAgentKindTags.vue` 展示件）；`api.ts` 不用改（透传 payload）。
- **契约**：`/api/ai/roles/` 只做加法，唯一破坏点是新建接口对 `kinds` 的强制校验；助手名片选配置（`frontend/src/modules/ai-assistant/api/assistants.ts`）读响应、不传参，无需改动。
- **运行时**：`engines/**` 零改动；SOP、任务、报告、计费均不读类型。
- **测试**：`tests/backend/apps/ai_assistant/` 增加 kinds 的创建 / 替换 / 清空 / 校验 / 级联用例；`frontend/tests/ops-console/p0/` 增加类型列与表单 payload 用例。
- **不受影响**：`AIAssistant` / `AISopWorkflow` 绑定、`resolve_workflow()` 参数、分页口径（前端每页 10 条切片）。
