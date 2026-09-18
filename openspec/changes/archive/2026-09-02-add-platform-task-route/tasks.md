## 1. 配置层 config.py

- [x] 1.1 新增 `PlatformTaskConfig` dataclass（planner/executor/verifier/max_loops）——验证：ruff check config.py
- [x] 1.2 新增 `PLATFORM_PLANNER_PROMPT`（先判断职责①~④再编排工具序列）
- [x] 1.3 新增 `PLATFORM_EXECUTOR_PROMPT`（用 REASONING_TOOLS 完成 steps）
- [x] 1.4 新增 `PLATFORM_VERIFIER_PROMPT`（用查询工具二次确认）——验证：python -m py_compile

## 2. 模型层 model.py

- [x] 2.1 新增 `PlatformTask` 类：三个文本 Agent（planner 无工具 / executor=REASONING_TOOLS / verifier=PLATFORM_VERIFIER_TOOLS）——验证：ruff check model.py

## 3. 工作流层 workflow.py

- [x] 3.1 新增 `PlatformTaskWorkflow` 类：复用 DeviceExecutionWorkflow 骨架，去掉 serial 强依赖，注入 requirements/checklist/report_name——验证：ruff check workflow.py

## 4. 工具层 tools.py

- [x] 4.1 新增 `PLATFORM_VERIFIER_TOOLS`（get_case/search_cases/debug_case/fetch_page_elements/list_pages/search_elements/get_page_flow/list_page_flows/get_run_results/get_run_status）
- [x] 4.2 扩展 `AUTO_ALLOW_TOOLS`：save_page_semantic/save_page_to_elements/create_page_flow/save_page_flow/save_case/save_api_test_case/run_test/stop_run

## 5. 视图接线 views_drf.py + api.py

- [x] 5.1 views_drf.py 新增 `_build_platform_task(agent, route)` 读 route_configs["platform_task"] 建 PlatformTaskConfig
- [x] 5.2 views_drf.py 的 TaskSubmitAPIView platform_task 分支改为 PlatformTaskWorkflow.run
- [x] 5.3 api.py 新增平台任务执行辅助（或 views 内联）——验证：python manage.py check + ruff check + python tools/gen_arch_stats.py --check-boundaries

## 6. 验证

- [x] 6.1 ruff check apps/ai_assistant/ + py_compile 通过
- [x] 6.2 model_test full 验证 device_control 不回归
- [x] 6.3 更新 ARCH-08 变更记录 + 生成 HTML 报告
