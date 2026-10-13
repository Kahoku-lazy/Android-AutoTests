## 1. 引擎：过程日志与事件流

- [x] 1.1 新增角色过程日志写入器模块：追加写、固定列（时间戳 | 角色 | 模型名 | 事件类型 | 内容）、自动创建目录与文件、并发写入不串行、UTF-8；验证：新增单测 `tests/graybox/unit/test_agent_process_log.py` 覆盖"首次运行自动创建""行格式匹配""两条并发写入不串行"，`pytest tests/graybox/unit/test_agent_process_log.py` 全绿
- [x] 1.2 给 `TaskRequest` 增加过程日志落点字段，未注入时回落到 `<当前工作目录>/logs/agents.log`；验证：单测断言未注入与注入两种情形下的实际落点，并断言引擎侧无平台 import（沿用 `tests/graybox/unit` 现有边界断言）
- [x] 1.3 在 `engines/ai/messaging` 增加"事件 → 过程记录"映射：思考块、工具调用、工具返回、截图表；验证：单测用构造事件断言映射出的事件类型、内容与超长截断标注，并断言结果中不含 base64
- [x] 1.4 角色执行改为消费 `reply_stream` 事件流：事件到达即写日志，同时仍组装既有的角色结果对象（字段与语义不变）；验证：引擎单测 + `python manage.py model_test executor "启动 govee 应用" --serial <真机>` 冒烟，确认执行全程 `logs/agents.log` 持续新增行且角色结果对象字段未变
- [x] 1.5 三个角色（规划 / 执行 / 验收）的系统提示词加入"思考与回复使用中文"约束；验证：单测断言三份提示词均含中文要求，且输出契约的字段说明未被改动；真机跑一轮抽样确认思考与回复为中文
- [x] 1.6 工作流停止装配与落库思考 / 工具明细（移除 trace 裁剪与写入），任务 `result` 不再出现 `executor_trace` / `verifier_trace`；验证：更新后的 `pytest tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_verifier_output_contract.py` 通过，且新增断言"新过程记录无 trace 键"

## 2. 平台后端：落点注入与过程记录瘦身

- [x] 2.1 `apps/ai_assistant/engine_adapter.py` 注入过程日志落点（`<BASE_DIR>/logs/agents.log`）；验证：单测断言构造出的请求带该落点，且与 `settings.BASE_DIR` 一致
- [x] 2.2 过程记录只保留展示与判定所需数据（规划步骤、执行结果、验收结论、验证截图、日志检查、设备日志证据）；验证：`pytest tests/graybox/unit/test_task_progress_persist.py` 通过，并新增断言 result 中无思考与工具明细

## 3. 前端：任务详情页瘦身

- [x] 3.1 移除任务详情页步骤卡片的「Agent 过程（输入 / 思考 / 工具 / 文本）」折叠区，以及仅为它服务的 helper、类型与常量；验证：`npm run build` 与 `vue-tsc` 通过，相关前端单测（`task-detail` 相关）全绿
- [x] 3.2 存量任务兼容：旧过程记录里仍带 trace 字段时不报错、不渲染空白区块；验证：手工打开一个改造前创建的任务详情页，页面正常且不出现过程区块

## 4. 退役「模型调试」

- [x] 4.1 后端移除模型调试配置与调试对话接口及其路由注册，并把"按智能体配置装配三角色模型"的函数拆到独立模块，命令行 `model_test` 与 `planner_eval` 改用新模块；验证：`python manage.py check`、`ruff check apps/ai_assistant`、`pytest tests/graybox/unit/test_ai_debug_assembly_entry.py` 通过
- [x] 4.2 删除仅服务调试对话的单测（`test_ai_model_debug.py`、`test_ai_debug_log_check.py`），并全仓 grep 确认无残留引用；验证：`pytest tests/graybox/unit -q` 通过，`grep -r "run_role_chat\|build_debug_role\|build_role_debug_configs"` 无命中
- [x] 4.3 前端删除模型调试页及其样式、常量、composable、helper、路由与装配台「模型调试」来源（工具箱来源由五源降为四源）、共享类型；验证：`npm run build`、`vue-tsc` 通过，装配台来源数量相关单测更新后全绿
- [x] 4.4 作废在办变更 `2026-09-29-restyle-model-debug-role-band`（其目标页面已退役）；验证：`openspec list` 中不再出现该变更，且仓库内无该变更目录

## 5. 验收与回归

- [x] 5.1 后端门禁：`python manage.py check`、`ruff check`（相关路径）、`pytest tests/graybox/unit -q` 全绿
- [x] 5.2 前端门禁：`npm run build` + `vue-tsc` + eslint/prettier 通过（范围 `frontend/src`）
- [x] 5.3 架构边界：`python tools/gen_arch_stats.py --check-boundaries` 通过（引擎仍不依赖平台、前端不新增跨模块调用）
- [x] 5.4 真机冒烟（一条三步以内任务）：过程中 `logs/agents.log` 持续追加，行内含时间戳 / 角色名 / 模型名，思考与回复为中文，截图事件只记路径；任务详情页只见规划步骤、每步执行结果与既有证据区块；验证：留存日志片段与详情页截图作为验收证据
- [x] 5.5 归档：`openspec validate --strict` 通过，delta 同步进主规格，并确认 `openspec/specs/ai-model-debug/` 已随退役移除

## 实施记录（2026-10-09）

- 引擎：新增过程日志写入器与事件流记录器；三角色改走 `reply_stream`，思考 / 工具调用 / 工具返回实时落盘；
  三角色提示词置顶「输出语言（最高优先级）」，真机实测思考与中间说明已转为中文。
- 平台：`TaskRequest` 新增过程日志落点，`engine_adapter` 注入 `<BASE_DIR>/logs/agents.log`；
  过程记录不再装思考与工具明细，相关裁剪函数与常量一并删除（`tool_usage` 改为按轮取，跳步切片机制随之退役）。
- 前端：任务详情页去掉「Agent 过程」区块；模型调试页、路由、常量、composable、helper、装配台来源（五源降为四源）全部移除。
- 退役：后端调试接口与 `model_debug.py` 删除，装配函数拆到 `model_assembly.py`；在办单
  `2026-09-29-restyle-model-debug-role-band` 已作废（目录删除）。
- 验证：`manage.py check` 通过、`ruff check` + `ruff format --check` 通过、
  定向单测 68 passed、`gen_arch_stats.py --check-boundaries` 零违规；
  前端 `vue-tsc` 通过、`eslint` 0 error（68 warning，无新增）、相关 vitest 44 passed；
  真机跑通一步执行，`logs/agents.log` 实时追加且行内含时间戳 / 角色 / 模型 / 任务与步骤 / 事件。

## 遗留（不在本单范围）

- 平台界面未起服务人工核验：任务详情页与工具箱的展示改用类型检查 + 相关前端单测 + 路由删除后的 grep 断言验证，
  未做「起服务点开页面」的人工确认。
- `apps/ai_assistant/log_history.py` 的调试回溯能力（`history_evidence` / `extract_basis_time`）随调试对话退役后
  已无生产调用方（仅单测覆盖），建议另立小单删除，顺带清掉 `window_id="model-debug-history"` 标签与对应单测。
- `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 仍写有 `/api/ai/model-debug/{role}/`，接口文档需随退役同步。
- 运行环境存量红（与本单无关，未修）：`test_workflow_single_path` 的 workflow api.ts 抽取、`test_auth_frontend_contract`
  与 `test_auth_validation_parity` 的前端抽取规则失效（前端侧并发改动导致）；前端 `prettier --check` 因 `core.autocrlf`
  导致 20 个存量文件报 CRLF。
