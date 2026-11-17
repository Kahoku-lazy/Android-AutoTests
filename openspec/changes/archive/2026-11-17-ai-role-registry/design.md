## Context

见 `proposal.md`「Why」。当前约束：

- `backend/apps/ai_assistant/models.py` 只有一张 `AIAgent`（表 `ai_agents`，30+ 字段），被 `task_list`、`dashboard`、`bug_manager`、`permissions`、`task_reports` 与 `views_drf` 引用，不能随手改结构。
- 该 App 的 `AGENTS.md` 写死「模型不对外……用户不能在页面上选择或切换模型」；根 `engines/AGENTS.md` 写死「提示词正文只放 `ae_harness/agents/config/prompts/*.md` 并经 `agents/config.py` 读取」。
- 分层纪律（`backend/apps/AGENTS.md`）：View 只分发，写库走 `api.py`，serializer 只做校验与 DTO。
- 路由约定：`/api/ai/` 前缀（`backend/config/urls.py`），路径带尾斜杠，成功信封 `{status, data}`。

## Goals / Non-Goals

**Goals（设计层面）**

- 一张可独立删除的表 + 一族可独立删除的端点：删掉这次改动时，`ai_agents` 与其它模块一行都不用动。
- `role_id` 的「绝不重复」由数据库唯一约束保证，而不是靠代码「应该不会撞」。

**Non-Goals（设计层面，非重复 proposal 的范围）**

- 不做分页、搜索、排序参数（全量返回，按创建时间倒序）。
- 不做归属/共享语义：本期没有 `owner` 字段，任何登录用户看到同一份列表。
- 不做乐观锁与并发编辑冲突提示（`updated_at` 只做展示）。
- 不做审计日志、不做软删除。

## Decisions

### D1 新建独立表 `ai_roles`，不改 `ai_agents`

新建 Model `AIRole`（`db_table = "ai_roles"`）。为什么不扩 `ai_agents`：那张表承载的是「可运行的智能体实例配置」（线路、密钥、任务类型、头像），和「角色是什么」不是同一关注点；把它精简成角色表要迁存量并改 6 处引用，收益与风险不成比例。

**代价**：短时间内库里同时有 `ai_agents` 与 `ai_roles` 两张含义相近的表，需要在文档里写清谁归谁。**替代方案（已否决）**：扩 `ai_agents` 加 `role_id` 与 `system_prompt` —— 会让「模型不对外」「提示词只放 .md」两条约束同时被一张老表拖着走。

### D2 `role_id` 是独立唯一列，自增主键只做内部主键

字段 `role_id = CharField(max_length=11, unique=True)`。生成规则见 spec：`YYYYMMDD` + 3 位 `[0-9a-z]`。

- 随机源用 `secrets.choice`（不用 `random`）：`role_id` 会被写进日志与用户可见的 URL，用密码学随机源避免可预测。
- 唯一性**不靠概率**：数据库 `unique=True` 是最终保证，生成函数撞了就重新生成；写入时再捕获 `IntegrityError` 重试一次，覆盖「查过不存在、写时被别人抢先」的竞态。
- 重试上限：单次创建最多 8 次生成。超过则视为当日空间耗尽（理论上限 46656/天），抛可读错误而不是死循环。
- 生成日期取 `django.utils.timezone.localtime()` 的日期，保证与服务器时区一致，不在跨时区部署时出现「ID 是昨天」的困惑。

**替代方案（已否决）**：UUID4（不可读、日志里搜不到）；纯自增 ID 对外（会暴露记录总量，且用户明确要随机标识）；`role_` 前缀 + 短码（用户明确要求以当天日期作固定前缀）。

### D3 名称唯一：DB 约束 + 序列化层前置校验

`name = CharField(max_length=200, unique=True)`；创建/更新时 serializer 先查重并抛 409，让常见路径拿到可读中文错误；并发下由数据库唯一约束兜底，捕获 `IntegrityError` 同样转 409。更新时排除自身 `pk`，因此「只改模型名称、名称原样提交」不会自我冲突。

**为什么区分大小写**：MySQL 默认排序规则不区分大小写，这一点与 spec 的「区分大小写」冲突。做法是在迁移里显式声明该列的排序规则为区分大小写（`utf8mb4_bin`），使「页面执行」与「页面执行 」之外的大小写差异被视为不同名称，与 spec 一致；代价是列表排序也变成按字节序。

### D4 `model_name` 只存储、不校验

写入只做「非空 + 长度 ≤ 200」。为什么不动 `ai_assistant/AGENTS.md` 的「模型不对外」：本期**不提供任何模型清单/取值查询接口**，也不把该值交给运行时装配，因此不构成「让用户在页面上选择或切换模型」。这条边界写进 tasks 的验收项；将来若要让页面按 `models.yaml` 列出可选模型，必须先提变更申请改该 AGENTS.md。

**代价**：用户可以写一个引擎里不存在的模型名，保存成功、装配时才失败。可接受：本期不装配。**缓解**：装配接入时先按 `ae_harness.agents.config.load_models()` 的键做存在性校验（那是下一次变更的事）。

### D5 `system_prompt` 本期只存库，不碰 `engines/`

正文原样入库，不读写 `engines/ae_harness/agents/config/prompts/*.md`，不改 `create_agent` 的签名。这样根 `engines/AGENTS.md`「提示词正文只放 prompts/*.md」在本次改动范围内**没有被违反**——那份红线的适用对象仍是引擎内置角色的提示词；本次只是给「用户自建角色」预留了一个存储位置，且尚未接入任何执行路径。

**代价**：库里会出现一份「暂时没有任何人读」的提示词。**缓解**：design 与 tasks 都显式记录「接入运行时前必须先提变更申请，明确哪一边是真相源」，避免下次顺手双写。

### D6 分层：View 只分发 → `api.py` 写库 → ORM

`views_drf.py` 新增 `RoleViewSet`，不直接 `AIRole.objects.create()`；所有写操作走 `api.py` 新增的 `create_role / update_role / delete_role / list_roles / get_role`。理由：`backend/apps/AGENTS.md` 要求 Tool 与 View 复用同一 api，后续角色被任务或对话引用时不用搬家。

### D7 用 DRF `ModelViewSet` + `lookup_field = "role_id"`

`router.register("roles", RoleViewSet, basename="ai_role")` 直接给出 `/api/ai/roles/` 与 `/api/ai/roles/{role_id}/` 两条带尾斜杠的路由，与现有 `agents` 注册方式一致。需要覆写三处：

1. `create` → 201 + `{status, data}`（DRF 默认 201 但无信封）。
2. `destroy` → 200 + `{status: true, data: {role_id}}`（DRF 默认 204 空体，前端无法按信封判成功）。
3. `list` / `retrieve` / `update` → 统一包 `{status, data}`。

**替代方案（已否决）**：照抄 `AgentViewSet` 的 `POST /{id}/update`、`POST /{id}/delete` 风格 —— 那是历史契约的遗留，新端点直接用 HTTP 方法语义更干净。

### D8 鉴权沿用，不做归属

DRF 全局 `IsAuthenticated` + JWT 中间件已兜底；不新增 `permissions.py` 分支。列表对任何登录用户返回全部角色（本期没有归属概念）。这也意味着任何人都能改任何角色——本期是单团队内部工具，先接受；写进 Risks。

### D9 时间字段由 ORM 维护，序列化 ISO 8601

`created_at = auto_now_add`、`updated_at = auto_now`，serializer 用 `DateTimeField` 默认 ISO 输出。

### D10 迁移只建表

新增 `0066_airole.py`，`CreateModel("AIRole")`，不改任何既有表。`ai_agents` 的迁移链一行不动。

## Risks / Trade-offs

- [`role_id` 同日空间耗尽] → 生成函数最多重试 8 次，超过抛可读错误（`503` 体面的说法或 409，见 tasks 落地）；46656/天的上限对当前规模足够。
- [`model_name` 不校验 → 装配期才炸] → 本期不装配；接入前补存在性校验（D4 缓解）。
- [提示词入库 → 与仓库 `.md` 形成双真相源] → 本期不读写 `.md`；接入前必须提变更申请（D5）。
- [无归属 + 无审计：任何登录用户可改任何角色] → 内部工具先接受；若要做隔离，加 `owner` 字段是兼容的加法迁移。
- [名称列改 `utf8mb4_bin` 会影响中文排序] → 列表排序只用 `created_at`，不受影响。
- [删除是物理删除] → 本期没有引用方，真删安全；一旦任务/会话引用角色，必须改软删除并单独迁移。

## Migration Plan

1. `python manage.py makemigrations --check` 应为空 → 手工新增 `0066_airole.py`（或由 `makemigrations` 生成后核对）。
2. `python manage.py migrate ai_assistant` 建表 `ai_roles`。
3. 回滚：`python manage.py migrate ai_assistant 0065` 删表；代码侧删掉 `roles` 路由注册即可，既有端点不受影响。
4. 不需要数据迁移，不需要停机；表建好前新端点会 500，因此上线顺序为「先迁移，再发代码」。

## Open Questions

- 是否需要归属（`owner`）与按用户过滤：本期不做，加字段是兼容迁移，可后置。
- 是否需要分页：当前全量返回；角色数量上千后再评估。
