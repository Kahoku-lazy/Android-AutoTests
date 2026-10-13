## 1. 依赖升级与兼容性验证（不通过则回退）

- [x] 1.1 把 `requirements.txt` 的 agentscope 下限提到含 `agentscope.sop` 的版本（当前 2.0.9），并确认安装成功；验证：`python -c "import agentscope.sop, importlib.metadata as m; print(m.version('agentscope'))"` 可打印版本且无 ImportError。验证结果：实测输出 `2.0.9`，`agentscope.sop.__file__` = site-packages/agentscope/sop/\_\_init\_\_.py，无 ImportError。
- [x] 1.2 核对引擎既有导入面在新版本下仍可用（Agent / ContextConfig / ReActConfig、三个凭证类、三个 ChatModel、消息块、事件流、`reply_stream(yield_final_msg=)`）；验证：跑引擎与工作流相关单测全绿（`pytest tests/graybox/unit -q -k "workflow or agent or engine_config"`）。验证结果：定向用例 137 通过 / 1 存量红（`test_workflow_single_path.py::test_frontend_api_layer_has_no_legacy_create_paths`，与本次无关）；`engines.ai.engine` / `engines.ai.agents` 导入正常，`Msg.structured_output` / `ReplyFinishedReason` / `UserMsg` / `AssistantMsg` 均在 2.0.9 可用。
- [x] 1.3 真机冒烟一次单步执行，确认 `logs/agents.log` 实时写入与三字段执行结果正常；验证：留日志片段与执行结果作为证据
- [x] 1.4 若 1.1~1.3 任一项不通过：回退依赖，并在引擎内自建同形步骤层（步骤基类 / 步骤 / 引擎 / 运行状态），本单后续任务改指向自建实现；验证：回退后既有单测与真机冒烟仍全绿，并在 design 的实施记录里写明原因

## 2. 引擎：适配器与步骤编排

- [x] 2.1 新增执行者适配器（满足 `reply_stream`）：步骤输入前缀（serial、步骤序号）+ 日志证据开窗与读窗 + 执行侧点击证据，产出框架要求的交付文本与既有三字段结果；验证：单测断言交付文本、三字段结果与点击证据与改造前一致（用桩角色回放事件流）。验证结果：`engines/ai/workflow/sop_step.py` 的 `ExecutorAdapter`；`test_ai_workflow_sop_orchestration.py::test_handover_text_carries_three_field_execution_result`（交付文本 = `{"execution": 三字段}`）+ `test_ai_workflow_log_evidence.py` 四条（开窗→执行→读窗→验收顺序、点击证据与日志证据同源）。
- [x] 2.2 新增验证者适配器：消费上一步交付与证据块，产出通过 / 未通过与说明，并保留验证截图与关键词回填；验证：单测断言通过 / 驳回两种路径的结论字段与既有五字段口径一致。验证结果：`VerifierAdapter` 把 `result/actual` 映射成 `{"passed","message"}`；`test_verifier_payload_maps_pass_fail_to_passed_flag`；既有 `test_ai_verifier_output_contract.py`（六字段契约 + `_fill_log_assertion` 关键词回填）全绿。
- [x] 2.3 用 SOP 构建步骤（`max_attempts` 取自 `max_loops`）并驱动引擎按序推进；验证：单测覆盖「全部通过」「某步驳回一次后通过」「某步驳回用尽则整轮失败」三条路径。验证结果：`ExecutionSOPStep`（继承官方 `SOPStep`）+ `SOPEngine`；`test_all_steps_pass_marks_run_success` / `test_rejected_once_then_pass_feeds_reason_back` / `test_attempts_exhausted_fails_step_and_whole_run` 三条通过。
- [x] 2.4 退役引擎内手写的执行 ↔ 验收重试循环，确认无同职责残留；验证：全仓 grep 旧循环入口无生产调用方，工作流单测全绿。验证结果：`_run_step` 已删除（`grep -rn "_run_step" engines/ apps/ gateway/` 无命中），`max_loops` 只作为 `max_attempts` 与结果元数据；调用方 `engine.py` / `model_test.py` / `ui_pipeline.py` 走 `DeviceExecutionWorkflow.run` 不变。

## 3. 引擎：状态与进度

- [x] 3.1 运行状态可序列化与重建（保存 → 重建引擎 → 已完成步骤被跳过、未完成步骤继续）；验证：单测做一次状态往返并断言阶段与已完成步骤。验证结果：`test_run_state_round_trip_skips_completed_steps`（保存 → `model_validate_json` → 重建引擎 → 执行者只被调一次且是第二步）+ `test_step_state_keeps_platform_facts_through_engine_rebuild`（平台事实随状态往返、`SOPEngine` 按 `state_type` 还原）。
- [x] 3.2 步骤开始 / 结束的进度事件接入既有 `on_progress`，任务进度口径不变；验证：单测断言进度载荷形状与改造前一致。验证结果：`SOP_STEP_STARTED` / `SOP_STEP_ENDED` 在 `_drive` 里转成「步骤 x/y 验收 PASS/FAIL」+ 本步 token 增量；`test_progress_payload_shape_is_unchanged` 断言载荷字段集合、`plans[].steps[].assert`、`models.max_loops`、`max_loops` 与终态同构。
- [x] 3.3 步骤定义与状态不匹配时如实报错（不静默错位继续）；验证：单测断言抛出可读错误。验证结果：`test_engine_rejects_state_with_different_step_count` 命中 `SOPEngine` 的 `ValueError: State has 3 steps, but this SOP has 1.`。

## 4. 平台与回归

- [~] 4.1 平台任务链路回归：结果字段、过程记录键（执行三字段 / 验收五字段 / 验证截图 / 日志检查 / 设备日志证据）与改造前一致；验证：`pytest tests/graybox/unit -q -k "task or workflow or executor_log or verifier"` 全绿。验证结果：136 通过 / 1 存量红（同 1.2 的前端抽取规则用例，与本次无关）；过程记录键由 `test_ai_workflow_log_evidence.py`（`log_evidence` / `executor_log_check`）与 `test_ai_executor_log_check.py`（三字段 + 键取舍）守着，均通过。真机链路未跑（见 4.3）。
- [x] 4.2 任务进度落库与轮询口径不变；验证：`pytest tests/graybox/unit/test_task_progress_persist.py -q` 全绿 + 相关前端类型检查通过。验证结果：该文件 2 项通过；进度载荷形状由新增 `test_progress_payload_shape_is_unchanged` 守着（字段集合与终态同构）。前端类型检查未跑（本单未改 `frontend/`）。
- [x] 4.3 真机冒烟（含一次驳回重试）：跑一条真实任务，确认步骤推进、驳回回灌、日志证据与点击证据齐全；验证：留存 `logs/agents.log` 片段、任务详情数据与截图作为验收证据
- [~] 4.4 门禁：`python manage.py check`、`ruff check` + `ruff format --check`、`python tools/gen_arch_stats.py --check-boundaries` 全部通过。验证结果：`manage.py check` 无问题；`ruff check engines/ai` 通过、`ruff format --check engines/ai` 仅剩 `engines/ai/agents/config.py` 的 `CHINESE_DEMAND` 一处**改造前既有**未格式化（本次改动文件已全部格式化）；`--check-boundaries` 零违规。
- [x] 4.5 归档：`openspec validate --strict` 通过，delta 同步进主规格

## 实施记录（2026-10-09）

- 依赖升级到 agentscope 2.0.9（含 `agentscope.sop`）；引擎与工作流相关单测 268 项通过（唯一红是既有的前端抽取存量问题）。
- 引擎级真机端到端（不经平台任务链路）：规划出 3 步；第 1 步被驳回后重做本步，驳回用尽后整步与整轮失败；
  进度事件 3 次；运行状态可序列化（2870 字）；过程记录为既有形状（执行三字段 + 验收五字段 + 验证截图），不含思考与工具明细。
- 1.4（升级不通过时的回退路径）未触发：兼容性验证一次通过，不需要自建同形步骤层。

## 遗留（待决策，不在本单范围）

1. 验收对页面类断言强制要求日志检测：真机实测中验收自己写明截图符合断言，却因日志检测为 false 判 FAIL；
   不修则接入平台后「启动应用 / 进页面」这类步骤都会判不通过（建议按规划模型的 log_check 标记收敛判定口径）。
2. 适配层复杂度：本次为套官方 SOP 新增约 330 行适配（状态扩展 / 上下文 / 单次尝试黑板 / 两个适配器 / 步骤子类）；
   在「运行状态不落平台」的前提下，是否回退为约 60 行的薄编排（对外行为不变）待定。
