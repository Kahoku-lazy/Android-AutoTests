# `backend/apps/ai_assistant` 模块代码分析

> 分析时间：2026-10-22
> 范围：`backend/apps/ai_assistant/`（含 60 个迁移）+ 上下游（`task_list` / `dashboard` / `engines/agents` / `frontend/src/modules/ai-assistant`）
> 方法：静态通读全部源码 → 全仓引用检索 → `ruff check` / `ruff format --check` → 实跑相关单测 → 对照 `openspec/specs`

---

## 0. 结论

**这个 App 已从「AI 引擎宿主」退化为「平台小助手的配置存储 + 7 个管理端点」：625 行非迁移代码、1 张表、60 个迁移、0 个 HTTP 层测试。**

分层本身是干净的（View → api → ORM、跨 App 只读、密钥 Fernet 加密、写库单通道），`ruff` 与 `format` 全绿。**真正的风险不在代码风格，而在「产品是单智能体」与「代码/契约是多智能体」的错位**：

| # | 结论 | 严重度 |
|---|---|---|
| 1 | `create_agent` 只写 name/avatar，产出没有 `executor/verifier` 线路的智能体；全仓没有受支持的线路写入路径（UI/admin/命令/API 都没有），这样的 agent 提交任务必失败 | P1 |
| 2 | 任务**写**路径按 `agent_id`，任务**读/控**路径钉死 `get_platform_agent()`（超管名下 id 最小者）；有第二个 agent 时任务"提交成功但列表里消失" | P1 |
| 3 | App 无任何 HTTP 层测试；且「AI 助手」marker 下现存 **1 条红测**（指向已退役的 tool_gateway），本地门禁与 CI 都只做 `pytest --collect-only`，跑不出来 | P1 |
| 4 | 约 1/3 代码与 7 个 DB 字段是零引用死代码；`reveal-key` 与 `delete` 前端已无入口但没有下线 | P2 |
| 5 | `openspec/specs` 仍保留 7 份已退役能力（意图路由 / 多 Harness / 工具箱 / 连通校验…），与本 App 代码已不一致 | P2 |

**推荐收敛路线：承认「单平台小助手」这一产品事实**（路线 A，见 §6）——与现有 UI、`2026-10-19-slim-agent-config-basic-info` 的产品口径、任务链实现三者一致，成本约 1 次 OpenSpec 变更 + 1 个迁移。

---

## 1. 模块画像

### 1.1 文件清单（625 行，不含迁移）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `api.py` | 191 | **唯一写库通道**；Agent CRUD、密钥加解密/脱敏、可见性过滤、线路配置解密 |
| `views_drf.py` | 124 | `AgentViewSet`（list/retrieve + 4 个自定义 POST action） |
| `serializers.py` | 114 | 入参校验 + 两个输出 DTO |
| `permissions.py` | 51 | 对象级权限判定（owner / visible / 超管写） |
| `provider_registry.py` | 46 | provider → base_url 映射 + base_url 白名单校验 |
| `models.py` | 44 | 唯一模型 `AIAgent`（12 个业务字段） |
| `views_upload_drf.py` | 24 | base64 头像 → data URI |
| `urls.py` | 15 | 路由真相源 |
| `admin.py` | 7 | Django admin 注册（仅列表页配置） |
| `decorators.py` | 5 | `require_auth` 再导出（**全仓零引用**） |
| `apps.py` | 4 | AppConfig |
| `AGENTS.md` | **0 字节** | 空文件（其余 4 个 App 有 1.7–2.9 KB 的 App 级约束） |

迁移：`0001`–`0060`，单表却 60 个迁移，其中一半是「退役」类（`0053_retire_ai_chat_surface`、`0055_retire_ai_toolbox`、`0057_retire_agent_connectivity_check`、`0058`–`0060` 任务模型拆出到 `task_list`）。

### 1.2 端点（7 个）

| 方法 | 路径 | 视图 | 前端是否在用 |
|---|---|---|---|
| GET | `/api/ai/agents/` | `list` | ✅ 看板 + 任务发布下拉 |
| GET | `/api/ai/agents/{pk}/` | `retrieve` | ✅ 配置页 |
| POST | `/api/ai/agents/create/` | `create_agent` | ⚠️ 仅在 `/ai-assistant/agent/new`（无入口按钮） |
| POST | `/api/ai/agents/{pk}/update/` | `update_agent` | ✅ 配置页 |
| POST | `/api/ai/agents/{pk}/delete/` | `delete_agent` | ❌ 无调用方 |
| POST | `/api/ai/agents/{pk}/reveal-key/` | `reveal_key` | ❌ 无调用方 |
| POST | `/api/ai/upload-avatar/` | `UploadAvatarAPIView` | ✅ 配置页 |

### 1.3 依赖方向（正确）

```
frontend ──► /api/ai/agents ──► ai_assistant.views_drf ──► ai_assistant.api ──► AIAgent
                                                                 │
dashboard ────────────────────────────────────────────────────┘（只读 Model + 只读 api）
task_list ──► ai_assistant.api（读） + provider_registry（直接 import）
     └──► engines.agents.role.config.ModelConfig（注入模型连接）

engines/agents ──► 零处 import ai_assistant（已验证）
ai_assistant ──► 零处 import task_list（已验证）
```

---

## 2. 做对的部分

1. **写库单通道**：`views_drf` 不直接 `save()`，全部经 `api.py`；`tests/arch/test_view_write_convergence.py` 的 AST 守卫覆盖 `views*.py`，本 App 干净。
2. **权限与视图分离**：`permissions.py` 只回答「能不能」，视图只负责抛 403/404，行为与旧函数视图逐条对齐（含「不存在资源先 403」的旧契约）。
3. **密钥不落明文**：`route_configs.*.api_key` 以 `SECRET_KEY` 派生 Fernet 密钥加密（`api.py:162-171`），读取时脱敏（`mask_key`），`reveal-key` 一次性揭示（`key_revealed` 标记）。
4. **provider 白名单 + SSRF 防护**：仅 `deepseek` / `dashscope` 两个 provider、host 白名单、生产禁 http、禁本机地址（`provider_registry.py:39-61`）。这块质量高于模块其余部分。
5. **引擎与 Django 解耦**：`engines/agents` 不认识 `AIAgent`，模型配置由 `task_list.engine_adapter` 从 `route_configs` 读出后注入 `ModelConfig`，依赖方向单向。
6. **代码卫生**：`ruff check` / `ruff format --check` 全绿；模块 docstring、函数 docstring 覆盖率高。

---

## 3. P1 问题

### P1-1 「新建智能体」产出不可执行的 agent，且没有受支持的配置写入路径

证据链：

| 环节 | 位置 | 事实 |
|---|---|---|
| 创建 | `api.py:59-78` | 只写 `route_configs={"device_control": {name, avatar}}` |
| 执行装配 | `task_list/engine_adapter.py:26-48` | 要求 `device_control.{executor,verifier}` 各有 `provider + model_name + api_key(可解密)`，缺任一即 `ValueError` |
| 提交校验 | `task_list/views.py:29-35` | 装配失败 → 400「智能体不可用于 SOP」 |
| 前端入口 | `frontend/src/modules/ai-assistant/routes.ts:11-16` | `/ai-assistant/agent/:agentId` 支持 `new` |
| 看板 | `index.vue:20-27` | **只渲染 `agents[0]`**，且没有「新建」按钮 |

补充事实：

- `AgentInputSerializer`（`serializers.py:18-30`）只接受 name/avatar/tags/description，**任何 API 都无法写入线路模型配置**。
- `admin.py:6-10` 只配了 `list_display` / `search_fields` / `list_filter`；Django admin 能编 `route_configs` 的原始 JSON，但 `api_key` 要填 Fernet 密文，手填明文 → `decrypt_key` 失败返回 `""` → 仍报「api_key 为空」。
- `management/commands/` 目录为空（`model_test.py`、`planner_eval.py` 只剩 `.pyc`），无种子/运维命令。
- 无任何迁移 seed 过 agent 行（`route_configs` 字段只在 `0031` 定义过）。

**判定**：除了「用 `api.encrypt_key()` 现算密文再手工写库/填 admin」这条未文档化的运维暗路径，没有任何产品路径能产出一个可执行的智能体。今天线上还能跑，说明库里存在一条历史手工数据。

**触发面**：属于**潜在**问题（看板没有新建入口），但路由仍可达、API 仍开放给超管，一旦有人访问 `/ai-assistant/agent/new` 就会造出一条永远提交失败的脏数据。

### P1-2 多智能体是幻觉：写路径按 `agent_id`，读/控路径按 platform agent

| 动作 | 代码 | 取哪个 agent |
|---|---|---|
| 提交任务 | `task_list/views.py:29` → `api.get_agent(agent_id)` | **请求里指定的** |
| 任务列表 | `task_list/views.py:84` → `get_platform_agent()` | 超管名下 id 最小 |
| 取消 / 删除 / 重跑 / 清空 | `task_list/views.py:96,112,133,153,165` | 同上 |
| 前端下拉 | `useTaskPublish.ts:54-68` | 列出**全部可见** agent，可切换 |

`get_platform_agent()`（`api.py:128-140`）的语义是「超级管理员拥有的、`status=active` 的、id 最小的那个」。于是：

- 用户在下拉里选第 2 个 agent 提交 → 任务创建成功 → 任务列表按第 1 个 agent 过滤 → **任务看不见，也无法取消/删除**（404「任务不存在」）。
- `get_agent`（`api.py:143-148`）**不过滤 `status`**，而 `get_platform_agent` 过滤 `ACTIVE` → 被停用的 agent 仍可接任务。

**根因**：`ai_assistant` 暴露了 N 个 agent 的 CRUD，而 `task_list` 已按「平台唯一小助手」重写。两边的世界模型没对齐。

### P1-3 测试面几乎为零，且曾有一条红测（已清理）、门禁看不见

- `tests/api/` 下 **0 个** `/api/ai/agents` 用例；`tests/AGENTS.md` 的模块映射表自己写着「AI 助手 接口测试脚本待补充」。
- 与 App 相关的只有 `test_ai_api_public_exports.py`（断言 `__all__` 含 `filter_agents_for_user`）和 `test_task_model_ownership.py`（断言 App 不再拥有任务模型）——都不覆盖权限矩阵、reveal-key、上传、脱敏。
- **实测**：`test_ai_tool_gateway_auth.py::test_correct_token_allowed` **失败**（期望 200，实际 401）。该用例打的 `/api/ai/tools/devices/list_all/` 是本 App 早已退役的 `views/tool_gateway.py`，路由已不存在；该过时用例已于 2026-10-28 删除。
- 门禁为何没拦住：`utils/check_gates.py:337-341` 与 `.github/workflows/ci-phase1.yml:58-64` 都只跑 `pytest --collect-only`——**只收集、不执行**。因此「6 个 CI job 全绿」不代表任何用例通过。

---

## 4. P2 问题：死代码、死字段、契约漂移

### 4.1 零引用符号（可静态证明）

| 符号 | 位置 | 证据 |
|---|---|---|
| `_MODEL_LIST_PATHS` | `views_drf.py:37` | 全文件无第二次引用 |
| `_require_owner` | `views_drf.py:72-79` | 无调用方（retrieve 用 `_require_visible`，写操作走 `_require_admin`） |
| `check_agent_owner` | `permissions.py:41-48` | 只被上面的死方法调用 |
| `ModelDetectInputSerializer` | `serializers.py:33-59` | 模型探测页已下线，零引用 |
| `decorators.py` 全文 | `decorators.py:1-7` | 全仓零 import（`require_auth` 已下沉 `shared.auth`） |
| `filter_agents_for_user` 再导出 | `permissions.py:12` | `views_drf.py:29` 从 `permissions` 拿，而真相源在 `api.py`（应走 api，违反本文件自己的 docstring） |
| `get_provider_config(…, model_name)` | `api.py:233-239` | `model_name` 形参未使用；且 `engine_adapter.py:10` 绕过它直接 import `provider_registry`，同一事实两个入口 |
| `check_can_update_agent(…, agent_id)` | `permissions.py:68-70` | `agent_id` 形参未使用（视图另做存在性检查） |

### 4.2 零读取 DB 字段（7 个）

| 字段 | 位置 | 现状 |
|---|---|---|
| `agent_scope_id` | `models.py:38` | AgentScope 时代遗留，全仓零读写 |
| `vision_model_name` | `models.py:24` | 只出现在 `AgentDetailSerializer:108` 输出 |
| `strong_model_name` | `models.py:26` | 同上（`:109`） |
| `strong_enabled` | `models.py:28` | 同上（`:110`） |
| `max_loops` | `models.py:33` | 同上（`:114`），另被 2 个单测显式赋值 |
| `api_key` | `models.py:34` | 执行链不读（引擎读 `route_configs`）；只剩 `reveal-key` 与详情 DTO |
| `base_url` | `models.py:35` | 同上，只剩详情 DTO 输出 |

前端 `shared/types/ai.ts:14-15,243-244` 仍保留这些可选字段——契约比后端实际语义更宽。

### 4.3 契约与前端不一致

| 位置 | 问题 |
|---|---|
| `views_drf.py:105` vs `:112` | 列表返回 `{agents}`、详情返回 `{agent}`，两种形状（可用，但不统一） |
| `views_drf.py:123,133` vs `frontend/src/modules/ai-assistant/api/agents.ts:24-31` | 后端创建/更新只返回 `{"id"}`，前端却声明返回 `AgentDetailResponse` |
| `AgentDetail.vue:71` vs `agents.ts:18` | 前端传普通对象 `{image: dataUrl}`，函数签名声明 `FormData`（axios 会 JSON 序列化，能跑但类型说谎） |
| `views_upload_drf.py:28` | 不管原始格式，统一重贴 `data:image/png` 前缀 → JPEG 被标成 PNG |
| `views_drf.py` 全部 action | 无 `@extend_schema`，create/update 在 OpenAPI 里没有请求体 schema（只有 class docstring 兜住 description） |

### 4.4 文档 / 声明漂移

- `backend/apps/ai_assistant/AGENTS.md` **0 字节**，而同层 `task_list` / `serial_log` / `report_generator` / `accounts` 都有 App 级红线与关单项。
- `models.py:1` 仍写 "AgentScope-powered"；`api.py:236` 仍写 "避免直接导入 agent_scope.provider_registry"——AgentScope 早已退役（`2026-10-19-remove-engines-ai`）。
- `frontend/src/modules/ai-assistant/helpers/model-capability.ts:4` 指向 `engines/ai/agents/config.py`，该路径已不存在。
- `gateway/middleware.py:12-18` 的 `RETIRED_AUTH_PATHS` 仍保留 5 条 `/api/ai/auth/*`。

### 4.5 规格漂移（OpenSpec 作为"真相源"已失真）

`openspec/specs/` 里仍有 7 份描述已退役能力的规格，涉及本 App 的对外行为：

- `ai-multi-agent-orchestration`（多套 Harness / 意图路由 / 强模型短路）
- `ai-intent-routing`（意图分类 / 按意图裁剪工具集 / 视觉模型降级）
- `ai-agent-model-config`（配置页管理三类模型、强模型开关、多模态提醒）
- `ai-agent-routes`（多线路模型配置；含仍有效的"API Key 加密与脱敏"）
- `ai-shared-skill-upload`、`ai-platform-tool-debug`、`ai-route-connectivity`

代码侧 `0053`–`0057` 已把这些面删掉。归档变更普遍带 `skip_specs: true`，所以主规格从未回写——**读规格的人会以为这些能力还在**。

---

## 5. P3：安全与健壮性边角

1. **双次 JWT 校验**：`gateway/middleware.py:88-90` 校验一次（设 `request.user_id`，不设 `request.user`），DRF `shared/auth/drf_auth.py:51-62` 又校验一次并查一次 User 表。本模块每个请求都付这份代价。
2. **`delete_agent` 级联删历史**：`task_list/models.py:11` 是 `on_delete=CASCADE`，删 agent 会连带删任务/附件/事件/媒体。API 仍开着，前端已无入口——一把没有护栏的铲子。
3. **owner 为 NULL 的 agent**：`permissions.py:19-23` 视为"无主不可见"，但 `get_platform_agent()` 不做 owner 过滤，仍会选中它执行 → 一个"谁都看不见、却仍在跑"的 agent。
4. **`reveal_agent_key` 的失败态**：`api.py:110-125`，`decrypt_key` 失败返回 `""`，代码仍置 `key_revealed=True` 并回"请立即复制保存"——一次空白揭示把唯一机会消耗掉。
5. **`reveal-key` 本身已空转**：`api_key` 不被执行链读取，且没有"重置/重新配置密钥"的写入路径 → 老数据只能揭示一次，之后永久 `***`。
6. **列表无 `ordering`**：`views_drf.py:104` 的 queryset 无 `order_by`，看板卡片顺序依赖 DB 返回顺序（`get_platform_agent` 反而显式 `order_by("id")`，两处不一致）。

---

## 6. 两条收敛路线

### 路线 A：承认单例（推荐）

把 `/api/ai/agents` 从"集合资源"改成"平台小助手单例"：

- 保留 `GET /api/ai/agents/`（前端看板已按 `agents[0]` 渲染）与 `POST /{pk}/update/`；
- 删除 `create` / `delete` / `reveal-key` 三个 action 与 `/ai-assistant/agent/new` 前端分支；
- 6 个死字段 + `api_key` / `base_url` 一次性迁移删除（`0061`）；
- 删 `ModelDetectInputSerializer`、`_require_owner`、`_MODEL_LIST_PATHS`、`decorators.py`；
- `get_agent` 补 `status=active` 过滤，与 `get_platform_agent` 对齐；
- 补 3–4 条 API 测试：列表可见性、非超管改 403、更新镜像 name/avatar、上传头像；
- 写入 App 级 `AGENTS.md`（当前 0 字节）。

收益：代码量约减 25%，"多智能体幻觉"与"不可执行 agent"两个 P1 同时消失，与产品口径一致。
代价：低（无路由契约破坏，前端只用 list/retrieve/update/upload）。

### 路线 B：补全多智能体

- `create` 必须携带 `device_control.executor/verifier`（或创建后置"未配置"态并在看板明示"不可用"）；
- 提供受支持的线路写入路径：管理命令（`api.encrypt_key` + 校验）或超管专用配置 API；
- `task_list` 的列表/取消/删除/重跑改为按 `task.agent` 过滤，不再钉 `get_platform_agent()`；
- 看板改为渲染 N 个 agent，而不是 `agents[0]`。

收益：保留多智能体能力。代价：中高（跨 App 改动 + 前端改版 + 新 UI 配置面），且与 `2026-10-19` 的产品决策相反。

---

## 7. 需要决策的事项

| # | 决策 | 我的建议 |
|---|---|---|
| 1 | 走路线 A（单例收敛）还是路线 B（补全多智能体）？ | **A**：与现有 UI、任务链、`slim-agent-config-basic-info` 口径一致，改动最小 |
| 2 | 7 个死字段是否本轮清（`0061` 迁移 + 前端 DTO 同步）？ | 清；字段退役不牵动执行链，但 `api_key`/`base_url` 要连带决定 `reveal-key` 去留 |
| 3 | 是否把「补 HTTP 测试面」写进本次变更的关单条件？ | 是；并建议把 `run.py check` 从 `--collect-only` 升级为至少跑 `unit + arch`，否则红测永远无人发现 |
| 4 | `openspec/specs` 的 7 份退役规格是否单独开一次规格清理？ | 建议单独变更处理（与代码改动解耦），否则"真相源"继续误导后续 OpenSpec 流程 |
| 5 | 是否更名 `ai_assistant` → `agent_config`？ | **不建议**：60 个迁移 + `/api/ai/` 路由前缀 + 前端模块名，收益不抵成本；写进 `AGENTS.md` 说明职责即可 |

---

## 附录：复现命令

```bash
# 静态检查（已跑，全绿）
python -m ruff check backend/apps/ai_assistant
python -m ruff format --check backend/apps/ai_assistant

# 本 App 相关单测（原含一条指向已退役网关的红测，该用例已删除）
python -m pytest -c tests/pytest.ini \
  tests/graybox/unit/test_ai_api_public_exports.py \
  tests/graybox/unit/test_task_model_ownership.py -q
```
