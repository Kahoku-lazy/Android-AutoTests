## 1. 校验与执行器语义对齐

- [x] 1.1 `apps/case_manager/api_ai.py` `_REQUIRED_FIELDS` 移除 `adb_start_app`/`adb_kill_app` 两条——验证 `validate_steps('ui_automation', [{"type":"adb_start_app","xpath":"","description":"启动"}])` 返回 True，`ruff check apps/case_manager` 通过

## 2. AI 等待能力与轮询指引

- [x] 2.1 `apps/ai_assistant/agent_scope/tool_registry.py` 新增 `sleep` 工具（分类「测试执行」、module common/action sleep、seconds 1-30、read_only）+ handler；`get_run_status` 描述补轮询间隔指引——验证 `TOOL_SCHEMAS` 含 sleep、`resolve("common","sleep")` 可调用（shell 实测等待 2 秒）、ruff 通过

## 3. 数据修正与端到端

- [x] 3.1 经 `save_ai_definition` 修正 TC-NAV-004 第 1 步 xpath 为 ""——验证 DB 中 steps[0].xpath == "" 且 `validate_steps` 通过
- [x] 3.2 `apps/test_runner/api.py` `start_run` 未传包名时取用例 `package_name`（`adb_start_app` 空 xpath 回退依赖该值）；`save_case` 描述补"xpath 可为空"——验证 ruff + 真机执行（见 3.3）
- [x] 3.3 真实设备端到端：`start_run` 重跑 TC-NAV-004 → 轮询 `get_run_status` 至终态——验证结果 **pass**（应用真实启动、Tab 断言通过）、设备释放
- [x] 3.4 全部门禁：`manage.py check` + `ruff check apps/case_manager apps/ai_assistant apps/test_runner` + `python tools/gen_arch_stats.py --check-boundaries` 全绿
- [x] 3.5 `openspec archive fix-device-launch-and-ai-polling` 归档本 change
