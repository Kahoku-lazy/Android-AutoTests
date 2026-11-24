# Tasks: retire-backend-dead-code

> 每项删除前即时复核全仓引用（backend/frontend/engines/tests/utils/run.py）；命中生产消费者即停手上报。按 app 分提交，每提交含测试同步。

## 1. 基础设施（shared / models / config / ops 常量）

- [ ] 1.1 删 shared/{config,db,events} 三个空壳包目录与 shared/auth/require_auth.py；knowledge_search/views.py 的 _require_superuser 改调 shared/users.is_superuser。验证：grep 零悬空引用，`python run.py check` 退出码 0
- [ ] 1.2 删 jwt_auth.get_user_id_from_token、users.resolve_username、ops_console/api.py IDENTITY_LABELS。验证：grep 各名仅余删除后零命中，`python -m pytest -c tests/pytest.ini tests/auth tests/ops_console -q` 通过
- [ ] 1.3 constants.py 删 7 死枚举 + ALL_STATUS_ENUMS + LockStatus.EXPIRED + LockReleaseReason.FORCE；**同一提交**下调 test_ssot_enum_strenum.py MIN_DISCOVERED_ENUMS（14→7）并修注释。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过
- [ ] 1.4 settings.py 删 14 个死配置项（先核对 .env.example 与 run.py/vite env 读取，SERVER_PORT 只删 settings 项不动 env）；修 tests/knowledge_search/integration/test_eval_runner.py:32 无效 override。验证：`python manage.py check` 通过，`python -m pytest -c tests/pytest.ini tests/knowledge_search tests/config -q` 通过
- [ ] 1.5 重写 tests/arch/unit/test_channels.py TestAgentScopeChannel：断言 engines/agents **不得存在**（与 utils/check_gates.py 退役门禁一致），删 :74-87 旧目录结构断言，:5 docstring 同步。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过（改前该测试必失败，改后与门禁同向）

## 2. task_list

- [ ] 2.1 git rm deepseek_billing.py、engine_adapter.py、log_history.py 三整模块。验证：grep 三名零 import，`python run.py check` 通过
- [ ] 2.2 删 api.recover_orphaned_tasks 与 __all__ 项；tests/ai_assistant/unit/test_ai_startup_recovery.py、test_ai_api_public_exports.py 改指 sweep_stale_tasks。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q` 通过
- [ ] 2.3 删 attachments.py 别名与旧收集函数簇（parse_task_attachment_bytes/collect_task_files/collect_document_files/MAX_CASE_DOCUMENTS）。验证：grep 零调用，`python -m pytest -c tests/pytest.ini tests/task -q` 通过
- [ ] 2.4 删 api.py 死函数簇（insert_task_events/store_task_media/add_usage_hourly/task_stats_by_agent/assistant_names_by_agent/materialize_config_file/set_config_load_message/build_case_requirement/case_project_code）与 __all__ 同步；build_sop_run_input 仅测试消费——连同 test_task_submit_sop.py 对应段处置。**保留三张表模型**。验证：grep 各名零生产调用，`python -m pytest -c tests/pytest.ini tests/task tests/dashboard -q` 通过
- [ ] 2.5 task_runner.py 删 _price_call_costs/_price_costs（含 pricing import）、RESULT_STATUS_MAP（test_task_status_symbols.py 同删/改）、ephemeral/yaml_path 死变量与恒假清理分支、agent_id 参数链（run_task_async 签名 + api.py 三派发点）。验证：`python -m pytest -c tests/pytest.ini tests/task -q` 通过
- [ ] 2.6 删 sweep_mark.write_stop_timeout_ids（test_task_sweep.py 对应段同删；文件格式契约注释补进 sweep_mark 模块 docstring）、media_storage.reset_media_storage。验证：`python -m pytest -c tests/pytest.ini tests/task/unit -q` 通过
- [ ] 2.7 serializers.py 删 legacy 字段（agent_id/assistant_route/attachment/case_title）与不可达 agent_id-only 分支；case_ids 校验收敛到序列化器一处（views._case_ids 重复解析删除）；docstring 同步。验证：`python -m pytest -c tests/pytest.ini tests/task -q` 通过，前端提交回归（tests/task/api）不受影响

## 3. device_pool / serial_log

- [ ] 3.1 删 manager.DeviceDetector.detect、judge_status、reset_status_sync_cache、wireless_ready_hint（test_connectable_serials.py 对应段同删）、models.Device.is_occupied、port_service.disabled_port_note 与 __all__ 项。**不动 api.py 白名单**。验证：`python -m pytest -c tests/pytest.ini tests/device tests/serial_log -q` 通过

## 4. ai_assistant

- [ ] 4.1 删 scripted 链：api.evaluate_target/record_eval 与 __all__ 项、services/eval_rulers.py 整模块、eval_samples W1-W5 样本；test_eval_rulers.py 整文件与 test_live_run.py record_eval 段同删。**保留 AssistantEvalRun 模型**。验证：grep 零悬空，`python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 通过
- [ ] 4.2 删 views_drf.AssistantThreadLogView 的 report_id 委托分支与 post；绕路由测试改打真实 URL/LogFileView。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api -q` 通过
- [ ] 4.3 删 model_configs.is_referenced；api.__all__ 摘除 list_messages/finish_message/replace_kinds/get_role（函数本体保留内部使用，get_role 测试评估改内部直调）；删 api.py:280 不可达 raise、views_drf serializer_class=None 两处、management 空壳包。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 通过

## 5. dashboard / usage_ledger

- [ ] 5.1 删 /api/devices/stats/ 与 /api/cases/stats/ 链（urls 两条、两视图、_user_cases_q、三个 model import）。验证：grep 路径零命中，`python -m pytest -c tests/pytest.ini tests/dashboard -q` 通过
- [ ] 5.2 ai_usage.py 删六函数 agents=None 参数与 del agents、_agg_by_role/_agent_usage 空桩、payload by_role/agents 字段、voice_by_model；docstring 改逐次账口径；tests/dashboard 空桩断言同删。验证：`python -m pytest -c tests/pytest.ini tests/dashboard -q` 通过
- [ ] 5.3 usage_ledger 删 api.record_voice_event 与 voice_today/voice_total 输出（test_usage_ledger.py voice 段同删）、pricing.py:70 永假分支。**不动 rates/pricing.json 双轨与 cache_creation**。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` 通过

## 6. case_manager / bug_manager

- [ ] 6.1 git rm case_manager/serializers.py；删 ConflictError.log 属性、management/commands 空目录；api_rows docstring 清单修正（list_rows→get_sheet）、__all__ 补 automation_case_identity。验证：`python -m pytest -c tests/pytest.ini tests/case -q` 通过
- [ ] 6.2 bug_manager 删 _created_by 的 agent.owner_id 永死分支、extract.py:46 agent_id docstring；测试 SimpleNamespace 伪造 agent_id 改真实形状。**保留 BugTicket.agent_id 字段**。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket -q` 通过

## 7. 前端同链删除

- [ ] 7.1 前置检查：align-backend-docs-with-code 对 frontend ai-assistant/AGENTS.md「agents.ts 仍被引用」红线的修订已合并；未合并则跳过本项并上报。删 api/agents.ts 三死函数与 constants.ts TASK_KIND_* 两常量。验证：`cd frontend; npx vue-tsc --noEmit; npx vitest run tests/ai-assistant` 通过
- [ ] 7.2 dashboard 删 agent-usage-list 死 UI 块、byRole/agents 映射与 AgentUsage/ByRoleMetric 类型、语音切换按钮与 voiceByModel 数据链（含 Voice 图表若存在）；types 中 planner_input/yaml_body/load_message 无消费声明同删。验证：`npx vue-tsc --noEmit; npx vitest run; node tests/check-style-gates.mjs` 通过

## 8. 关单门禁

- [ ] 8.1 全量核对：`python run.py check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 零违规；`python -m pytest -c tests/pytest.ini -m "unit or integration or api"` 通过；ruff check/format --check 相关路径通过
- [ ] 8.2 逐文件暂存、按域分提交（chore/refactor），推特性分支提 PR，确认 python 与 frontend 两个 CI job 全绿后合并