## 1. 步骤执行提示（模型与用例表单）

- [x] 1.1 `cm_case_steps` 新增 `anchor` / `log` 两个 JSON 列并生成迁移；验证：`makemigrations --check` 无待生成迁移，`migrate` 正向通过（本地已生成 `0024_case_step_execution_hints`）。
- [x] 1.2 `engines/agents/workflow/case_file.py` 增加公开的 `parse_step_hints(anchor, log)`（返回纯字典 + 失败原因，内部复用既有锚点/证据规则）；验证：`tests/graybox/unit/test_case_yaml_import.py` 覆盖「合法返回字典 / 未知 anchor 键 / 非法 port」。
- [x] 1.3 `api_definitions` 的 `_normalize_steps` / `_replace_steps` / `serialize_steps` 全程保留执行提示，并在校验失败时报步骤序号；验证：`tests/graybox/integration/test_case_yaml_sync.py` 断言保存后读回一致，既有 `test_case_definitions_api.py` 11 条全绿。
- [x] 1.4 前端 `CaseStep` 类型带可选 `anchor` / `log`，`toSteps()` 与步骤抽屉透传；抽屉只读展示执行提示；验证：`npx vitest run tests/case-manager` 通过（新增 `step-hints.spec.ts` 6 条），`vue-tsc --noEmit` 通过。

## 2. YAML 与用例库互转

- [x] 2.1 新增 `backend/apps/case_manager/api_yaml.py`：解析 YAML 为中性行（含 anchor/log 与元数据映射）、幂等落库、导出可执行 YAML；验证：`tests/graybox/unit/test_case_yaml_import.py`（10 条）+ `tests/graybox/integration/test_case_yaml_sync.py`（10 条）全绿。
- [x] 2.2 新增管理命令 `import_case_yaml --dir --project --owner [--dry-run] [--prune]`：遍历目录、每 YAML 一张表、结论计数；验证：`--dry-run` 输出 7 文件 / 56 条；连跑两次第二次新建 0、更新 56。
- [x] 2.3 新增 `POST /api/cases/import-yaml/`：上传导入到指定项目，缺省按文件名建表，越权返回不存在；验证：`tests/api/test_case_yaml_import_api.py` 覆盖成功/重复/非法结构/非 YAML/缺项目/越权六路（6 条全绿）。
- [x] 2.4 用例库网页入口「导入 YAML」+ 导入结论展示；验证：`vue-tsc` 与 `vite build` 通过，弹窗按项目刷新目录树并选中新表。

## 3. 平台用例执行

- [x] 3.1 `case_manager` 增加按 `case_ids` 导出 YAML 的公开 api（含归属校验与顺序保持）；验证：integration 用例覆盖「他人用例被拒」「空选择被拒」「顺序一致」。
- [x] 3.2 `task_list` 提交入参增加 `case_source` / `case_ids`（JSON 数组字符串），`platform` 时物化 YAML 配置附件并走既有 SOP 入口；验证：`tests/api/test_task_submit_platform_cases.py` 6 条全绿（生成附件、顺序、空/非法/越权/不存在）。
- [x] 3.3 前端新建任务弹窗增加「用例来源」单选与平台用例选择器（项目 → 文件 → 用例多选），切换来源清空另一侧；验证：`npx vitest run tests/task-list` 通过（`useTaskPublish.spec.ts` 11 条含 4 条新用例）。
- [x] 3.4 任务详情沿用既有配置附件展示，确认平台用例任务的 `yaml_body` 可读回；验证：`test_platform_cases_create_task_with_config_attachment` 断言附件正文含所选用例标题与执行提示。

## 4. 数据同步与收口

- [x] 4.1 执行 `python manage.py import_case_yaml --dir "D:\Govee\data\H6810" --project "H6810 用例库" --owner admin` 完成首次同步；验证：项目 #19 下 7 张表 / 56 条用例，带 anchor 的步骤 92 个、带 log 的 8 个，与源目录逐项一致。
- [x] 4.2 门禁与回归：`python run.py check` 阻塞项 **23/23 通过**；受影响后端用例 70 条全绿；`ruff check` / `ruff format --check` 覆盖改动路径无新增问题。
- [ ] 4.3 端到端人工验收：在平台用例来源下选一条带 `anchor`/`log` 的用例提交任务，确认任务详情配置正文含执行提示、执行链启动；再走一次本地 YAML 上传确认老路径不变（需真机与模型调用，未随本次改动执行）。
