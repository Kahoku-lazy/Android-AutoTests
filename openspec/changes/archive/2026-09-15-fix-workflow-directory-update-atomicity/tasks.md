## 1. 复核（已完成，结论见 proposal.md「与原判的差异」）

- [x] 1.1 复核「双写」前提：实测 `PATCH /api/workflow/directories/{id}/` 带 `parent_id` → 200 且父级不变；确认 `WorkflowDirectorySerializer.parent_id` 为 `ReadOnlyField`，`perform_update` 的 `parent_id` 分支**不可达**（无部分写）
- [x] 1.2 复核写库收敛：确认 `serializer.save()` 直写 `name`/`sort_order`，越过 `apps/workflow/api.py`
- [x] 1.3 复核契约：`API-工作流.md` §3.4 要求 `parent_id` int/null（null = 移到根）且列出 api.py 的 400，故「移动」属文档承诺能力
- [x] 1.4 复核 `update_directory` 不支持 `sort_order`：签名为 `(dir_id, name=None, parent_id=None)`

## 2. 修改

- [x] 2.1 `apps/workflow/api.py`：`update_directory` 增 `sort_order` 参数并在 `d.save()` 前赋值
- [x] 2.2 `apps/workflow/serializers.py`：`parent_id` 改为可写 `IntegerField(allow_null=True, required=False)`
- [x] 2.3 `apps/workflow/views_api.py`：`perform_update` 改为单一 api 调用（含 null→空串翻译、`serializer.instance` 刷新），删除 `serializer.save()`
- [x] 2.4 `dev_docs/05-开发与测试/接口文档/API-工作流.md` §3.4 错误码表补 `不能跨原型移动目录`
- [x] 2.5 新增 `tests/graybox/unit/test_workflow_directory_update.py`：① 跨原型移动 + 改名 → 4xx 且 name/sort_order 不变；② 同原型换父 + 改名 + sort_order → 三者都落库；③ `parent_id: null` → 移到根

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → `No changes detected`
- [x] 3.2 `python -m ruff check apps/workflow tests/graybox/unit/test_workflow_directory_update.py` → All checks passed；`ruff format --check` 我的 2 个文件（新测试 + views_api.py）→ 已格式化（api.py / serializers.py 的既有格式债见「遗留」）
- [x] 3.3 新测试 4 passed；`tests/graybox/unit` **82 passed**（基线 78 + 新增 4）；`tests/arch/test_channels.py` 6 passed；`gen_arch_stats.py --check-boundaries` 零违规
- [x] 3.4 范围核对：`git diff --numstat` = api.py 9/1 · serializers.py 3/0 · views_api.py 24/13（含既有会话改动）· 文档 1/0 · 新增测试 113 行；无迁移文件

## 4. 遗留（不在本单范围）

- `apps/workflow/api.py` / `apps/workflow/serializers.py` 在 **HEAD 即**不满足 `ruff format`（已用回退法核实：revert 到 HEAD 后仍报同样 2 文件）。全仓同类文件共 9 个，属既有格式债，归 D2-7 门禁项（B5）统一处理，本单不顺手 reformat 以免产生无关 diff
