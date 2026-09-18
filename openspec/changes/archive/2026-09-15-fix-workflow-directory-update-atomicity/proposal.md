## Why

🔴 **目录更新契约未兑现 + 写库越过 api 白名单**（D2-1 / D3-1 同一处：`WorkflowDirectoryViewSet.perform_update`）。

**文档契约**：`dev_docs/05-开发与测试/接口文档/API-工作流.md` §3.4 规定
`PUT/PATCH /api/workflow/directories/{id}/` 的请求体含 `parent_id`（int/null，**传 `null` 移到根**），并列出由 `api.py` 抛出的 400（`父目录不存在` / `同级目录名冲突`）；§5 声明 legacy 路径「行为与 router 对应端点一致」。

**实测现状**（2026-09-15，`Client().patch` + 真实 JWT，`config.test_settings`）：

| 请求 | 文档期望 | 实测 |
|------|----------|------|
| `{name, parent_id: <其他原型目录>}` | 400，且 `name` 不变 | **200**；`name` 已改，`parent_id` 不变 |
| `{parent_id: null}`（子目录移到根） | 200，`parent_id` 变 `null` | **200**，`parent_id` 不变 |
| `{name, sort_order}` | 200，两者落库 | 200，两者落库 ✅ |

根因：`WorkflowDirectorySerializer.parent_id` 是**只读**字段（`ReadOnlyField`），`validated_data` 永远不含 `parent_id` —— 于是 `perform_update` 里 `if parent_id is not None:` 的分支**永不进入**：`parent_id` 被静默丢弃（假状态反馈），跨原型移动的 400 校验不可达。

同一个函数还用 `serializer.save()` **直写库**（`name` / `sort_order`），越过 `apps/workflow/api.py`（D3「写库只经 api.py」）。两层根因与原判一致：① 写库越过 api 白名单；② `update_directory` 当时不支持 `sort_order`，视图作者只能用 `serializer.save()` 补写这个字段。

> **与原判的差异（已订正）**：本单原提「400 后 `name` 已落库」的部分写复现**不成立** —— 该 400 分支当前不可达。真正的现场是「契约未兑现 + 参数被静默丢弃 + 越权写」；修法不变：把该分支接通为**单一 api 写路径**，从而在兑现契约的同时保证失败零写库。

## What Changes

- `apps/workflow/serializers.py`：`WorkflowDirectorySerializer.parent_id` 由只读改为可写 `IntegerField(allow_null=True, required=False)`，兑现文档 §3.4 的 `parent_id` int/null 契约
- `apps/workflow/api.py::update_directory` 新增 `sort_order: int | None = None` 参数（在 `d.save()` 之前赋值 → 与其他校验一样「先校验、后落库」）
- `apps/workflow/views_api.py::perform_update` 改为**单一写路径**：只调 `wf_api.update_directory(...)`，失败即 `ValidationError`（此时**未发生任何写**），成功后 `serializer.instance` 重新取库内对象；删除 `serializer.save()` 与不可达分支
- 保留「显式 `parent_id: null` = 移到根」语义：视图把 `null` 翻译为 api 约定的空串（api 内 `parent_id == ""` → `d.parent = None`）
- 文档同步：`API-工作流.md` §3.4 错误码表补 `不能跨原型移动目录`（接通后变为可达）
- 新增回归测试 `tests/graybox/unit/test_workflow_directory_update.py`：① 失败路径（跨原型移动 + 改名）→ 4xx 且 `name`/`sort_order` **不变**；② 成功路径 → `name`、`sort_order`、同原型换父 **都落库**；③ `parent_id: null` → 移到根

- **BREAKING**：无（成功路径响应结构不变；`parent_id` 由「静默忽略」变为「按文档生效」属修 bug）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 前置分析：本会话 D2/D3 复查（缺陷 D2-1 / D3-1）
- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-工作流.md` §3.4 / §3.6 / §5
- App 约束：`apps/workflow/AGENTS.md`（legacy 与 router 双路径同改、行为一致；前端契约同步）
- 门禁：`.agents/skills/django-backend-check/references/calibration.md` §2（🔴 定义含「假状态反馈 / 契约错误」）· §3.2 写库收敛

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/workflow/api.py`（+1 参数 +2 行）· `apps/workflow/serializers.py`（`parent_id` 1 行）· `apps/workflow/views_api.py`（`perform_update` 重写）
- 文档：`dev_docs/05-开发与测试/接口文档/API-工作流.md` §3.4（+1 错误码行）
- 测试：新增 `tests/graybox/unit/test_workflow_directory_update.py`
- 验证：`manage.py check` · `makemigrations --check`（无模型改动，必须仍为 No changes detected）· `ruff check`/`format --check` · 新测试 + `tests/graybox/unit` 全量
