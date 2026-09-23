## 1. 后端路由与视图

- [x] 1.1 `apps/workflow/urls.py`：拆出 `literal_write_patterns`（`prototypes/create/`、`directories/create/`、`documents/create/`、`documents/import/` 四条字面量写路径）并置于 `router.urls` 之前，其余 legacy 路径顺序、名称与视图不变；路由顺序原因写成文件内注释。验证：`django.urls.resolve()` 对这四个路径分别命中 `prototypes_create` / `directory_create` / `documents_create` / `documents_import`，不再命中任何 `*ViewSet`
- [x] 1.2 `apps/workflow/views_api.py`：`WorkflowDirectoryViewSet` 覆写 `destroy`，删除成功后返回 `Response({})`（与 `WorkflowDocumentViewSet.destroy` 同理由），失败仍按 `wf_api.delete_directory` 的状态码返回。验证：`DELETE /api/workflow/directories/{id}/` 响应体为 `{status: true, data: {}}`，且目录确实不再出现在列表中

## 2. 前端调用面

- [x] 2.1 `frontend/src/modules/workflow/api.ts` 三处调用改走标准方法：`updateWorkflowDirectory` → `client.patch(...)`（去掉 `action: 'update'` 包装）、`deleteWorkflowDirectory` → `client.delete(...)`、`updateWorkflowPrototype` → `client.patch(...)`。验证：方法-路径探针扫描 `frontend/src` 的 34 个调用点，0 处「方法不在命中 router 视图白名单内」
- [x] 2.2 复核 `frontend/src/modules/workflow/stores/libraryStore.ts` 的目录改名 / 删除分支：仍以信封 `status` 判定成功，不新增「2xx 即成功」的空体特判（删除分支靠 1.2 的非空体支撑）。验证：`libraryStore.ts` 中目录分支的 `res.data?.status` 判定保持不变，注释与实际一致

## 3. 守护测试

- [x] 3.1 `tests/graybox/unit/test_api_path_callers.py`：`_CALL_RX` 增加动词捕获组，`Caller` 记录 `method`；新增用例断言「路径解析命中带动作白名单的 router 视图时，方法必须在白名单内」，函数视图跳过。验证：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` → 9 passed，且 `test_scanner_finds_the_expected_volume` 的规模下限仍满足（方法捕获未让任何面少扫）
- [x] 3.2 负向自检：把 `api.ts` 的目录改名临时改回 `client.post(...)`，新断言必须失败并在错误信息里列出方法、路径与白名单动作；还原后重新通过。验证：两次 `pytest tests/graybox/unit/test_api_path_callers.py -q -k method` 结果分别为 1 failed / pass（失败信息含 `api.ts:87 POST → WorkflowDirectoryViewSet 仅接受 ['delete','get','patch','put']`）

## 4. 门禁与验收

- [x] 4.1 后端门禁：`python manage.py check` → System check identified no issues；`python -m ruff check apps/workflow tests/graybox/unit/test_api_path_callers.py` → All checks passed；`python -m ruff format --check` → 13 files already formatted（首次发现 `missing = [...]` 行超宽，已按 ruff 格式折行）
- [x] 4.2 单元套件：`python -m pytest tests/graybox/unit -q` → **411 passed**（含 `test_workflow_prototype_envelope.py`、`test_workflow_directory_update.py`、`test_api_path_callers.py` 9 条、`test_api_path_convention.py`），零失败
- [x] 4.3 全链路验收（平台在跑：后端 8766 / 前端 5173 / Redis）：
  - 黑盒 HTTP（`temps/wf_write_api_probe.py`）：新建原型 201 → 新建目录 201 → 新建页面流 201 → 导入 201 → 目录改名 200 → 原型改名 200 → 目录删除 200（`{status:true,data:{}}`）+ 删除后列表为空 → 清理探针原型 200，**9/9 PASS，全程无 405**
  - 真实浏览器（`temps/wf_write_ui_probe.py`，Playwright）：登录 → 页面流「+ 新建原型」→ 自动进入 `/workflow/prototypes/5` → 「+ 根目录」建目录 → 「+ 页面流」建文档并进入画布态 → 回浏览态确认文档出现在资源树 → 右键「重命名」→ 右键「删除目录」→ 清理，**9/9 PASS，无 405 响应、无失败提示**
- [x] 4.4 清理一次性探针 `temps/scan_method_path.py`（其断言已固化进 3.1 的守护用例）；保留两个验收探针 `temps/wf_write_api_probe.py` / `temps/wf_write_ui_probe.py` 供复跑。附带：前端 `npx eslint src/modules/workflow/api.ts` 0 问题；`prettier --check` 的告警经比对为既有基线（改动前的同一文件同样不合规），未新增

## 5. 归档

- [x] 5.1 `openspec validate fix-workflow-create-route-shadowing --strict` 通过后执行 `openspec archive fix-workflow-create-route-shadowing -y` → 归档为 `openspec/changes/archive/2026-09-23-fix-workflow-create-route-shadowing`，delta 已 sync：`api-path-convention` +1 requirement、`workflow-http-envelope` +2 requirements（Totals: +3 ~0 -0）
- [x] 5.2 主 spec 复核：`openspec validate api-path-convention --type spec --strict` 与 `openspec validate workflow-http-envelope --type spec --strict` 均 valid；新增需求标题与场景齐全、无占位符。**偏离**：`openspec validate --specs --strict` 总览为 51 passed / 14 failed，14 条失败全部是与本变更无关的既有 spec（`admin-managed-shared-agent`、`ai-*`、`auth-*` 等，失败原因是 Purpose 仍是占位符），本变更涉及的两个 spec 不在其中，未新增失败项
