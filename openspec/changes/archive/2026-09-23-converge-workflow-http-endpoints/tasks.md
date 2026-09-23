## 1. 后端：让 router 单套可承接全部语义

- [x] 1.1 `apps/workflow/serializers.py`：`WorkflowDocumentDetailSerializer.directory_id` 显式声明为 `serializers.IntegerField(allow_null=True, required=False)`，`config` 改为 `required=False`。验证：实测 `directory_id` 字段不再是 `ReadOnlyField`；`test_workflow_single_path.py` 的创建归属用例通过
- [x] 1.2 `apps/workflow/views_api.py`：`WorkflowDocumentViewSet.perform_create` / `perform_update` 改为按提交字段合并（新增 `_directory_id_from()` 归一 `null` / 空串 / 非法值）。验证：`test_partial_update_keeps_omitted_fields`（只提交 title 返回 200、config 与 description 保持）、`test_update_can_change_and_clear_directory`、`test_update_without_directory_id_keeps_it`、`test_cross_prototype_directory_rejected_without_write` 全部通过
- [x] 1.3 `apps/workflow/views_api.py`：导入动作声明 `url_path="import"`。验证：`resolve("/api/workflow/documents/import/")` 命中 `WorkflowDocumentViewSet` 且 `actions == {"post": "_import"}`；`test_import_uses_router_action_route` 通过

## 2. 后端：删掉 legacy 一套

- [x] 2.1 `apps/workflow/urls.py`：收敛为 `urlpatterns = router.urls`，删除两套 pattern 与 `from . import views`，docstring 写明收敛缘由。验证：`resolve()` 对 `…/create/` 中原型 / 目录两条抛 `Resolver404`；集合 / 详情 / 动作路由命中对应 ViewSet
- [x] 2.2 删除 `apps/workflow/views.py`（13 个 legacy 视图）。验证：`grep -rn "workflow.views\|wf_proto_\|wf_dir_\|wf_doc_" apps/ tests/ tools/ gateway/ shared/` 零命中；`python manage.py check` → System check identified no issues
- [x] 2.3 `apps/workflow/serializers.py`：删除 `WorkflowDirectoryTreeSerializer`。验证：全树 grep 零命中（node_modules 除外）；目录树接口仍返回 `data.tree`
- [x] 2.4 `apps/workflow/views_api.py`：两个 ViewSet 加 `lookup_value_regex = r"\d+"`。验证：`GET /api/workflow/prototypes/create/` 与 `/directories/create/` 均 404（不再是 405 / 500），`test_literal_segment_is_not_treated_as_primary_key` 通过

## 3. 前端：调用面与信封读法统一

- [x] 3.1 `frontend/src/modules/workflow/api.ts`：`createWorkflowPrototype` → `POST /workflow/prototypes/`；`createWorkflowDirectory` → `POST /workflow/directories/`；`saveWorkflowDocument` → `POST /workflow/documents/`；`importWorkflowDocument` 保持 `POST /workflow/documents/import/`，`overwrite` 只走 query。验证：文件内不再出现 `/create/`（`test_frontend_api_layer_has_no_legacy_create_paths`）
- [x] 3.2 `frontend/src/modules/workflow/composables/usePrototypes.ts`：创建原型后从 `data.data` 取原型。验证：`test_use_prototypes_create_reads_envelope_data_not_prototype` 通过
- [x] 3.3 `frontend/src/modules/workflow/stores/libraryStore.ts`：`createFolder` / `createFlowDoc` / `importDoc` 读 `res.data.data`；`savePageFlowPayload` 与 `renameNode` 的两处 `res.data.document` 改为 `res.data.data`。验证：`test_frontend_reads_standard_envelope_only` 通过（平铺键零残留）
- [x] 3.4 `apps/AGENTS.md` §1.3：删除 workflow legacy 特例条目，保留 report_generator 特例。验证：该节只剩 report_generator 一条特例

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_workflow_single_path.py`（13 条）. 验证：`python -m pytest tests/graybox/unit/test_workflow_single_path.py -q` → 13 passed
- [x] 4.2 字段合并语义契约用例（并入 4.1 的文件）：创建归属生效、只提交 title 返回 200 且 config / description 保持、PUT 改归属 / 显式 null 移到根 / 未传不动、跨原型 4xx 且零落库、非法 doc_type 400 零落库. 验证：全部通过
- [x] 4.3 `tests/graybox/unit/test_workflow_prototype_envelope.py`：docstring 更新（不再有"被 router 抢占"的叙事），新增 `test_use_prototypes_create_reads_envelope_data_not_prototype`. 验证：3 passed
- [x] 4.4 `tests/graybox/unit/test_api_path_callers.py`：规模下限未漂移（前端只改路径字符串、调用点数量不变；tests 面因新增两条负向用例 +2）。新增的两条负向字面量按既有机制登记进 `EXCEPTIONS` 并注明理由。验证：9 passed，规模断言未空跑

## 5. 门禁与验收

- [x] 5.1 后端门禁：`python manage.py check` → no issues；`makemigrations --check --dry-run` → no changes；本地总门禁 `python run.py check` → **阻塞项 10/13 通过**（ruff format / ruff lint / django-check / vitest / vite-build / boundary 等全 PASS，其中 vitest 61 文件 350 用例全过、vite-build 通过）。3 条失败均为既有基线且与本变更无关：`prettier`（`src/App.vue`、ai-assistant 等存量 `.vue/.css`）、`cred-frontend`（`LoginView.vue` 的 `v-model:password` 误报）、`vue-file-size`（6 个既有超 500 行 Vue 文件）——本变更未改任何 `.vue/.css/js`
- [x] 5.2 单元套件：`python -m pytest tests/graybox/unit -q` → **428 passed / 1 failed**。唯一失败是 `test_engine_hierarchy_contract.py::test_engine_impl_does_not_import_algorithms` 读 `engines/device/android/u2.py` 抛 `FileNotFoundError`——该路径被**另一个并发会话**的 engines 迁移删除（`git status` 显示 `D engines/device/**` + 未跟踪 `engines/ai/device/`），与本变更无关。本变更涉及的用例全绿：`test_workflow_single_path.py`（13）、`test_workflow_prototype_envelope.py`（3）、`test_workflow_directory_update.py`（4）、`test_api_path_callers.py`（9）；前端 `vitest --project workflow/p0` 7/7 通过
- [x] 5.3 活平台黑盒验收（`temps/wf_write_api_probe.py`，平台已启动）→ **18/18 PASS**：三条旧 `/create/` 地址返回 404/405 且不产生资源；`GET /prototypes/create/` 404（非 500）；集合路由创建原型/目录/页面流均 201 + 标准信封；创建时 `directory_id` 真正落库（15 == 15）；只改标题返回 200 且 `config` / `description` 保持；保存画布后描述未被清空；导入走动作路由 200；目录改名 PATCH、文档移到根、目录删除 DELETE、原型改名 PATCH 全部通过
- [x] 5.4 真实浏览器验收（`temps/wf_write_ui_probe.py`，Playwright）→ **11/11 PASS**：登录 → 页面流「+ 新建原型」→ 工作台「+ 根目录」→ 在选中目录下「+ 页面流」→ 资源树确认文档出现且缩进深于目录（padding 24 vs 10，归属正确）→ 右键「重命名」页面流成功（回归：此前必现 400）→ 目录改名 → 目录删除；全程无 ≥400 的页面流响应、无失败提示

## 6. 归档

- [x] 6.1 已归档为 `openspec/changes/archive/2026-09-23-converge-workflow-http-endpoints`；delta 并入 `openspec/specs/workflow-http-envelope`（Totals: +2 -1，即新增「页面流写操作只有一套路由且返回标准信封」「文档更新按提交字段合并并支持归属写入」，移除「Legacy 平铺写端点必须可达」）
- [x] 6.2 主 spec 复核：`openspec validate workflow-http-envelope --type spec --strict` → valid；主 spec 需求列表已不含「Legacy 平铺写端点必须可达」（grep 命中 0）；`openspec validate --specs --strict` → 51 passed / 14 failed，与上一变更记录的既有基线完全一致，未被本变更放大
