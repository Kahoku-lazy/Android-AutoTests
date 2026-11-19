## Context

动机与范围见 `proposal.md`。方案要落地的现状约束（读码所得，行号为当前主干）：

- 角色表 `AIRole`（`backend/apps/ai_assistant/models.py:51`）只有 `role_id` / `name` / `model_config` / `system_prompt` + 时间戳；既有需求 `ai-role-registry` 明文禁止把「任务类型」写进这张表。
- 写库只有两个出口：`services/agent_configs.py`（`prepare_role` / `update_role` / `list_roles`）与 `api.py`（`create_role` / `update_role` / `delete_role`）；`views_drf.py:114` 的 `RoleViewSet` 只做分发。
- 运行时消费点是 `services/sop_workflows.py:95` 的 `_resolve_side()`：只取 `role.system_prompt` 与 `role.model_config.*`，**不读类型**。
- 前端一处页面消费该接口（`ops-console/agents.vue`）、一处复用（`ai-assistant/api/assistants.ts:21` 的选配置下拉）。
- 历史包袱：`AIAgent`（曾带 `prompt_planner` / `prompt_executor` / `prompt_verifier` 三分段提示词）已在 `migrations/0070` 退役，本次**不**恢复分段提示词，只做单值标签。

## Goals / Non-Goals

**Goals:**

- 类型标签落在独立关联表，角色记录零新增字段。
- 接口只做加法：一次请求返回扁平记录（含 `kinds`），前端不需要第二次 join 请求。
- 一份配置 1:1 一个类型；表结构为将来的 1:N 留出唯一的最短放开路径。
- 存量数据保守回填：能确定的补上，不确定的留「未分类」。

**Non-Goals:**

- 不做「按类型过滤 SOP 选人」、不改 `AISopWorkflow` / `AIAssistant` 绑定（需求方已确认）。
- 不做类型与工具/预算/模型的联动，类型纯标签。
- 不恢复 `prompt_planner` / `prompt_executor` / `prompt_verifier` 三分段提示词。
- 不新增 `/api/ai/role-kinds/` 子资源接口。

## Decisions

### 决策 1：类型放独立表，而不是给 `ai_roles` 加列

**选择**：新建 `AIRoleKind`（表 `ai_role_kinds`），外键指向 `AIRole`。

**理由**：`ai-role-registry` 的既有需求是「角色记录 MUST NOT 保存任务类型」，加列会直接违约，必须改那条 Must 级约束才能实现；独立表在不触碰该约束的前提下落地。

**备选**：给 `ai_roles` 加 `kind` 列（实现最简单，1:1 时无 join）——被否：违约且把展示分类混进「角色只描述角色本身」的契约。

### 决策 2：外键方向「标签 → 配置」，且用真外键 + CASCADE

**选择**：`role = ForeignKey(AIRole, on_delete=CASCADE, related_name="kinds")`。

**理由**：标签没有独立生命，配置删了就该跟着删。与 `AIAssistant.role_id`（故意不建外键，因为名片要比配置活得久）是两种不同语义，不能类比套用。

**备选**：存 `role_id` 字符串不建外键（与名片一致）——被否：会留下孤儿标签，需要额外的清理任务。

### 决策 3：约束先锁 1:1，结构保留 1:N

**选择**：同时声明 `UNIQUE(role)` 与 `UNIQUE(role, kind)`。

**理由**：需求方确认「同一份配置不能既是执行者又是验收者」，`UNIQUE(role)` 把这条规则交给数据库，不靠前端自律。将来若放开多类型，只需删 `uniq_ai_role_kind_role` 这一条约束，表结构与契约字段（`kinds` 数组）都不用动。

**备选**：只建 `UNIQUE(role, kind)`，靠校验层限制 1 项——被否：并发下仍可能写入两条，DB 约束更可靠。

### 决策 4：join 在后端，接口仍是「一次一条扁平记录」

**选择**：`list_roles()` 增加 `prefetch_related("kinds")`，`RoleOutputSerializer` 用 `SerializerMethodField` 输出 `kinds: string[]`；前端只发一次 `GET /api/ai/roles/`。

**理由**：前端两次请求再 join 会打破既有的「接口一次返回全部 + 本页前端切片 10 条」分页口径（`ops-agent-config` 已定），还要处理两份数据的时间差与错误态。`prefetch_related` 把 N+1 收敛为 2 条查询。

**备选**：新增 `/api/ai/role-kinds/` 让前端自己拼——被否：页面要为一次展示打两个请求，且写路径要维护两套 CRUD。

### 决策 5：`kinds` 用数组而不是单值字段

**选择**：入参/出参都是 `kinds: string[]`，当前长度 0 或 1。

**理由**：1:1 与 1:N 用同一套契约，放开多类型时不产生契约破坏性变更；前端 chip 渲染天然支持 0..N 个。

**代价**：单值场景多一层数组，校验必须显式写「新建恰好 1 项」。

### 决策 6：写入语义「整组替换」

**选择**：`replace_kinds(role, kinds)` 在同一事务里删除多余行、补插缺失行；调用于 `create_role` / `update_role` 之后，同属一个事务。

**理由**：前端一次提交完整状态，不需要「加一个 / 删一个」的细粒度接口；先清后插会导致 `created_at` 抖动，故用差集写法。

### 决策 7：回填只认名称里的独立类别词，不猜语义

**选择**：迁移里把名称按 `[-_]` 切词，命中整词 `EXECUTOR` / `VERIFIER` / `PLANNER` 才补类型；`CASE_WRITER_PROMPT` 等留未分类。

**理由**：实际命名既有连字符（`Android-UI-Executor`）也有下划线（`CASE_VERIFIER_PROMPT`），且 `role_id` 是日期+随机串，按前后缀匹配会一条都匹配不上（首次实现即踩到）。规划者/编写者在当前库里没有唯一答案（`AIAgent` 退役后没有 planner 链路），猜错比留空更糟——留空在页面上是可见的待办。

### 决策 8：前端类型列渲染为 chip，复用现成模块色

**选择**：新增 `components/OpsAgentKindTags.vue`，chip 用 `--app-size-xs` 字号、`var(--app-radius-sm)` 圆角、`1px solid color-mix(in srgb, var(--ink) 10%, transparent)` 实线描边，三类型描边分别借 `--c-device` / `--c-workflow` / `--c-element`，未分类用 `--app-text-secondary` 文字。

**理由**：按 `doodle-craft` 默认口径落地——不新增颜色原子、不用虚线（本列不在虚线白名单）、不改表格皮肤。抽屉里用 `el-radio-group` 三选一，与「一列一值」的表述一致。

## 模块防火墙自检

- **跨 App import**：本次只在 `backend/apps/ai_assistant/` 内部改动，无新增跨 App import；`task_list` 等模块不读类型，零改动。
- **写库收敛到 `api.py`**：新增的 `AIRoleKind` 写操作落在 `services/agent_configs.py`，经 `api.py` 的 `create_role` / `update_role` 暴露；`views_drf.py` 只把 `kinds` 从 `validated_data` 取出后透传，不直接碰 ORM。
- **前端不直连数据库**：前端只经 `/api/ai/roles/`。
- **engines 边界**：`engines/**` 零改动，不触发「platform 角色一律经 backend_bridge 装配」等红线。
- **AGENTS 红线**：未修改任何 `AGENTS.md` 条款，未新增自定义异常类，未改依赖方向，未动钱与配额口径。

## Risks / Trade-offs

- [新建接口开始强制 `kinds`，旧前端/脚本调用会 400] → 只影响运营后台内部页面，同一次变更里前端同步改；`PATCH` 保持可选，存量脚本的更新不受影响。
- [`UNIQUE(role)` 将来放开多类型要改约束] → 迁移只需 `RemoveConstraint` + `AddConstraint`，数据与契约不动。
- [类型成为没人维护的装饰字段] → 新建强制必选，存量在列表用灰色「未分类」暴露待办；编辑存量时 UI 要求补齐。
- [列表 N+1] → `list_roles()` 必须与既有 `select_related("model_config")` 并列加 `prefetch_related("kinds")`，由测试断言查询数。
- [回填误判] → 只认后缀，其余留空；迁移可逆（反向删除全部标签行，不回滚成角色字段）。

## Migration Plan

1. 迁移 `0071_airolekind`：建表（含两条唯一约束）→ 回填（后缀匹配）→ 反向为清空标签表。
2. 部署顺序：先上后端（加字段是纯加法，旧前端读多字段无感；新建接口的强制校验对新前端同时生效）→ 再上前端。
3. 回滚：回滚前端只是一个可见性回退；回滚后端需 `migrate ai_assistant 0070`，标签表删除，角色记录不受影响。
4. 运营动作：列表里把显示「未分类」的配置逐条补类型（当前 1 条：`CASE_WRITER_PROMPT`）。
