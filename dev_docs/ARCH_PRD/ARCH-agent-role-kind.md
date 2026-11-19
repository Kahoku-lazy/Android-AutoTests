# ARCH — Agent 配置增加「类型」（执行者 / 验收者 / 规划者）

> 状态：待拍板 · 提出人：需求方 · 整理：lead · 日期：2026-11-18
> 相关 spec：`openspec/specs/ai-role-registry`、`openspec/specs/ops-agent-config`、`openspec/specs/agent-sop-workflow`

---

## 1. 结论

1. **独立表方案成立，而且比"在 `ai_roles` 上加一列"更合规**：已归档 spec `ai-role-registry` 明确写了角色记录 MUST NOT 保存"任务类型"，所以类型必须落在另一张表。
2. **一处必须纠正**：不要把"两张表拼起来"做成**浏览器里两次请求再 join**。join 放在后端 service 层，`/api/ai/roles/` 仍然一次返回一条扁平记录（多一个 `kinds` 字段）。前端看到的是一张表、一次请求、一套分页——这才是"前端一张表、后端两张表"的正确落法。
3. **表结构按可扩展的关联表设计**（`ai_role_kinds`，一行 = 一个「配置 × 类型」），但**先用 `UNIQUE(role)` 锁死 1:1**，前端单元格一个 chip。将来要放开"一份配置多类型"，只需删约束 + 前端换多选，不用改表、不用迁移数据。
4. **运行时零影响**：SOP 只读 `AIRole.system_prompt` + `AIRole.model_config`（`services/sop_workflows.py:95`），类型不参与装配，`resolve_workflow()` / `AIAssistant` / `AISopWorkflow` 一行都不用改。这正是你要的"不影响 Agent 创建的配置参数传递"。
5. 属于**新增字段 + 新表**，按根 `AGENTS.md` 走 OpenSpec 四步：`opsx:propose ops-agent-role-kind` → apply → archive。

---

## 2. 现状代码事实（方案的地基）

| 关注点 | 位置 | 事实 |
| --- | --- | --- |
| 角色表 | `backend/apps/ai_assistant/models.py:51` | `AIRole`：`role_id`(11 位唯一) / `name`(唯一) / `model_config` FK / `system_prompt` / 时间戳。只有三样业务字段 |
| 入参 | `backend/apps/ai_assistant/serializers.py:57` | `RoleInputSerializer`：`name` / `model_config_id` / `system_prompt` |
| 出参 | `backend/apps/ai_assistant/serializers.py:130` | `RoleOutputSerializer`：`role_id` + 名称 + 从 `model_config` 带出的 5 个模型字段 |
| 写库 | `backend/apps/ai_assistant/services/agent_configs.py` | `prepare_role`(25) / `update_role`(53) / `list_roles`(85) |
| 视图 | `backend/apps/ai_assistant/views_drf.py:114` | `RoleViewSet`，`lookup_field="role_id"`，list/retrieve/create/patch/destroy |
| 对外入口 | `backend/apps/ai_assistant/api.py:138` | `create_role()`；`__all__` 是跨 App 唯一入口 |
| 前端契约 | `frontend/src/modules/ops-console/types.ts:50` | `OpsAgent` / `OpsAgentInput` |
| 前端列定义 | `frontend/src/modules/ops-console/constants.ts:99` | `OPS_AGENT_COLUMNS`：名称 / 模型配置 / 系统提示词 / 操作 |
| 前端页面 | `frontend/src/modules/ops-console/agents.vue` | `AppTable` + `#cell-*` 插槽 + 右侧 `el-drawer` 表单 |
| 运行时消费 | `backend/apps/ai_assistant/services/sop_workflows.py:95` | 只取 `role.system_prompt` 与 `role.model_config.*`，**不读类型** |
| 另一个消费者 | `frontend/src/modules/ai-assistant/api/assistants.ts:21` | 助手名片表单复用 `/ai/roles/` 选配置；新增字段对它是加法，不改代码 |

**结论**：类型只影响「列表可读性」与「配置的检索/筛选」，不影响任何一条运行链路。

---

## 3. 数据模型

```python
class AIRoleKind(models.Model):
    """Agent 配置的类型标签 → ai_role_kinds（执行者 / 验收者 / 规划者）。

    一行 = 一条配置的一个类型。类型不写进 ai_roles，角色记录仍只描述角色本身。
    """

    KIND_CHOICES = [
        ("executor", "执行者"),
        ("verifier", "验收者"),
        ("planner", "规划者"),
    ]

    role = models.ForeignKey(AIRole, on_delete=models.CASCADE, related_name="kinds")
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_role_kinds"
        verbose_name = "Agent配置类型"
        verbose_name_plural = "Agent配置类型"
        constraints = [
            # 先锁 1:1：一份配置一个类型。放开多类型时改成 [role, kind]
            models.UniqueConstraint(fields=["role"], name="uniq_ai_role_kind_role"),
            models.UniqueConstraint(fields=["role", "kind"], name="uniq_ai_role_kind_pair"),
        ]
```

四个设计取舍，逐条说清：

| 取舍 | 选择 | 理由 |
| --- | --- | --- |
| 外键方向 | 标签表 → `AIRole`（`ForeignKey`，CASCADE） | 反向（`AIRole.kind_id`）等于把类型写进角色记录，违反 `ai-role-registry` 的 MUST NOT |
| 存 `id` 还是 `role_id` | Django 外键，落到整数 `id` | `AIAssistant.role_id` 之所以不建外键，是因为名片要比配置活得久；标签没有独立生命，配置删了标签就该跟着删 |
| `kind` 取值 | `executor` / `verifier` / `planner`（snake_case） | 与 `task_reports.py:577` 的 `executor/verifier` 口径一致；HTTP 全 snake_case |
| 1:1 还是 1:N | 约束锁 1:1，结构留 1:N | 你的表述是"名称后面多一个类型的列"= 一值；先锁死避免歧义，放开成本只是删一条约束 |

---

## 4. 接口契约（路径不变，只加字段）

`GET /api/ai/roles/` 响应（`{status, data}` 信封不变）：

```json
{
  "status": true,
  "data": [
    {
      "role_id": "20261118a7k",
      "name": "Android-UI-VERIFIER",
      "model_config_id": 3,
      "provider": "govee",
      "api_key_env": "GOVEE_API_KEY",
      "model_name": "deepseek-flash",
      "base_url": "https://api.govee.com/v1",
      "api_protocol": "openai",
      "system_prompt": "## 角色\n…",
      "kinds": ["verifier"],
      "created_at": "2026-11-18T10:00:00+08:00",
      "updated_at": "2026-11-18T10:00:00+08:00"
    }
  ]
}
```

- `POST /api/ai/roles/`、`PATCH /api/ai/roles/{role_id}/` 入参增加 `kinds: ["executor"] | []`。
- **向后兼容**：旧前端不传 `kinds` → 视为 `[]`；旧调用方读响应多的字段无感。
- **不新增** `/api/ai/role-kinds/` 这类子资源。标签是配置的从属字段，PATCH 整组替换（先清后插，同一事务），避免前端维护两套 CRUD。

---

## 5. 后端改动清单

| 文件 | 改动 |
| --- | --- |
| `models.py` | 新增 `AIRoleKind`（见上） |
| `migrations/0071_airolekind.py` | 建表 + 回填（见第 7 节），带反向删除 |
| `services/agent_configs.py` | `prepare_role(name, model_config_id, system_prompt, kinds=())` 返回体不变，由 api 层写 tag；`update_role` 增加 `kinds` 参数；`list_roles()` 加 `.prefetch_related("kinds")`；新增 `replace_kinds(role, kinds)` |
| `serializers.py` | `RoleInputSerializer` 加 `kinds = serializers.ListField(child=serializers.ChoiceField(choices=RoleKindValues), required=False, max_length=1)`；`RoleOutputSerializer` 加 `kinds = serializers.SerializerMethodField()` → `[k.kind for k in obj.kinds.all()]` |
| `api.py` | `create_role(...)` / `update_role(...)` 透传 `kinds`；`__all__` 不变（不导出内部模型操作） |
| `views_drf.py` | `RoleViewSet.create/partial_update` 取 `validated_data.pop("kinds", None)` 传给 api 层 |

写库骨架（守住"View 只分发、写库走 api"）：

```python
# services/agent_configs.py
def replace_kinds(role: AIRole, kinds: list[str]) -> None:
    """整组替换配置的类型标签。空列表表示未分类。"""
    with transaction.atomic():
        AIRoleKind.objects.filter(role=role).exclude(kind__in=kinds).delete()
        have = set(AIRoleKind.objects.filter(role=role).values_list("kind", flat=True))
        AIRoleKind.objects.bulk_create(
            [AIRoleKind(role=role, kind=kind) for kind in kinds if kind not in have]
        )
```

```python
# views_drf.py · RoleViewSet.create
kinds = serializer.validated_data.pop("kinds", None)
role = api.create_role(**serializer.validated_data, kinds=kinds or [])
```

---

## 6. 前端改动清单

| 文件 | 改动 |
| --- | --- |
| `types.ts` | `export type OpsAgentKind = "executor" \| "verifier" \| "planner"`；`OpsAgent` 加 `kinds: OpsAgentKind[]`；`OpsAgentInput` 加 `kinds: OpsAgentKind[]` |
| `constants.ts` | 加 `OPS_AGENT_KIND_OPTIONS`（`value/label`）与 `OPS_AGENT_KIND_LABELS`；`OPS_AGENT_COLUMNS` 在「名称」后插一列 `{ label: "类型", prop: "kinds", width: 130 }` |
| `agents.vue` | ① 表格加 `#cell-kinds` 插槽：chip 渲染，空显示「—」；② 抽屉表单在「名称」下加类型选择；③ `form` 初值与 `openEdit` 预填带 `kinds`；④ `save()` 的 payload 带 `kinds` |
| `api.ts` | **不改**（`createOpsAgent` / `updateOpsAgent` 本就透传 `payload`） |
| `components/OpsAgentKindTags.vue` | 建议抽个小展示件：把 `kinds` 渲染成 chips，列表与弹窗共用一处皮肤 |

类型列渲染（保持"一张表"、行不重复、`row-key` 仍是 `role_id`）：

```vue
<template #cell-kinds="{ record }">
  <OpsAgentKindTags :kinds="record.kinds" />
</template>
```

视觉口径（按 doodle-craft，不自创）：

- chip = `--app-size-xs`(12px) 文字 + `var(--app-radius-sm)` 圆角 + `1px solid color-mix(in srgb, var(--ink) 10%, transparent)` 描边 + `color-mix` 浅底；**实线**（虚线白名单不含本列）。
- 三种类型不新造颜色：复用现成模块色做描边（执行者 `--c-device`、验收者 `--c-workflow`、规划者 `--c-element`），未分类用 `--app-text-secondary`。
- 抽屉里的选择控件：`el-select` 单选（配 `kinds` 长度 1）或 `el-radio-group`；后者更贴"一列一值"的表述。

---

## 7. 迁移与回填

```python
KIND_BY_NAME_SUFFIX = (("_VERIFIER", "verifier"), ("_EXECUTOR", "executor"))


def forward(apps, schema_editor):
    AIRole = apps.get_model("ai_assistant", "AIRole")
    AIRoleKind = apps.get_model("ai_assistant", "AIRoleKind")
    for role in AIRole.objects.all().only("id", "role_id", "name"):
        for suffix, kind in KIND_BY_NAME_SUFFIX:
            if role.role_id.upper().endswith(suffix) or role.name.upper().endswith(suffix):
                AIRoleKind.objects.create(role=role, kind=kind)
                break
```

回填口径（保守）：

- 只回填**名字里明确带 `VERIFIER` / `EXECUTOR`** 的存量（当前库里 `Android-UI-VERIFIER`、`Android-UI-Executor`、`CASE_VERIFIER_PROMPT`）。
- `CASE_WRITER_PROMPT` **不猜**，留"未分类"，由运营在页面上补——猜错类型比留空更糟。
- 反向迁移：`AIRoleKind.objects.all().delete()`，不回滚成角色字段。

---

## 8. 影响面（明确"不动"的部分）

| 不动 | 原因 |
| --- | --- |
| `AIAssistant.role_id` / `AISopWorkflow` | 名片与工作流按 `role_id` 引用配置，与本表无关 |
| `resolve_workflow()` / `build_bound_roles()` | 只读提示词与模型参数；类型不参与装配 |
| `/api/ai/roles/` 路径、分页口径（前端每页 10 条切片） | `api-path-convention` + `ops-agent-config` 已定口径 |
| 任务清单 / 报告 / 计费 | 全部经 `role_id` 与 `run_name`，不读类型 |
| `engines/**` | 本次零改动（不碰红线，不需要 engines 侧规范检查） |

**可选后续（不在本次范围）**：SOP 工作流新建时按类型过滤名片候选（执行位只列"执行者"）。这会改 `task-card-sop-form` 与 `ai-assistant` 的选人逻辑，单独开变更。

---

## 9. 测试与门禁

后端：

```bash
python manage.py check
python manage.py makemigrations --check
ruff check backend/apps/ai_assistant && ruff format --check backend/apps/ai_assistant
python -m pytest -c tests/pytest.ini -m "unit or integration"
```

要补的用例（`tests/backend/apps/ai_assistant/`）：

1. 创建带 `kinds` → 响应回带、库里一行；
2. `PATCH kinds: []` → 标签清空，不删配置；
3. `PATCH kinds` 换类型 → 旧行删除、新行写入，`role_id` 不变；
4. 重复 `kinds: ["executor","executor"]` → 400（`ListField` 去重校验）；
5. `kinds` 缺省 → `[]`，老调用方不报错；
6. `DELETE /api/ai/roles/{id}/` → 标签随之删除（CASCADE）。

前端：

```bash
cd frontend && npx vitest run tests/ops-console && npx vue-tsc --noEmit && npm run lint:styles
```

要补的用例：类型列渲染（有/无标签）、抽屉预填与 payload、`row-key` 未因新列变化。

---

## 10. 风险与取舍

| 风险 | 缓解 |
| --- | --- |
| 表结构支持多值、UI 先单选 → 将来放开要改前端 | 只是删 `uniq_ai_role_kind_role` + 换控件；表与契约不用动 |
| 类型成为"没人维护的装饰字段" | 新建时必填（至少 1 项），存量保持"未分类"并在列表用灰色「未分类」chip 提示补齐 |
| 同一类型多条配置（例如两份"验收者"） | 不建 `UNIQUE(kind)`；若要"每类型只有一条默认"，用产品规则在服务层校验，别用 DB 约束（会锁死未来） |
| 列表 N+1 | `list_roles()` 必须 `prefetch_related("kinds")`，与现有 `select_related("model_config")` 同级 |
| 旧的 `AIAgent.prompt_planner` 记忆干扰 | 规划者已随 `AIAgent` 退役（migrations/0070），本次只做**标签**，不恢复三分段提示词 |

---

## 11. 实施顺序（一次变更、三个提交）

1. `feat(ai-assistant): 新增 ai_role_kinds 关联表与 kinds 契约`（model + migration + serializer + api + 单测）
2. `feat(ops-console): Agent 配置列表增加类型列与表单选择`（types + constants + agents.vue + chips 组件 + vitest）
3. `docs(openspec): 归档 ops-agent-role-kind 并同步 ops-agent-config / ai-role-registry`

OpenSpec 产物要点：

- `openspec/changes/ops-agent-role-kind/proposal.md`：为什么加类型、为什么放独立表（引 `ai-role-registry` 的 MUST NOT）、影响面为零的运行链路清单。
- `specs/ops-agent-config/spec.md` delta：列表 MUST 在「名称」后显示类型列；无类型显示「未分类」。
- `specs/ai-role-registry/spec.md` delta：新增"角色的分类标签存放在 `ai_role_kinds`，角色记录本表 MUST NOT 增加类型字段"。

---

## 12. 待决策

1. **1:1 还是 1:N**：一份配置能否同时是「执行者 + 验收者」？默认按 1:1 落地（`UNIQUE(role)`）。
2. **类型是否必填**：默认"新建必填、存量允许未分类"。
3. **规划者是否真有落点**：现在运行时只有执行者/验收者，规划者只是标签。是先给三选项（含规划者），还是先只给两个、等规划链路回来再加？
4. **是否顺手做"按类型过滤 SOP 选人"**：默认不做，另开变更。
