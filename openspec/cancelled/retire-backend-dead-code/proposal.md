# Proposal: retire-backend-dead-code

## Why

后端审计确认约 70 处死代码/死配置：退役变更（智能体下线、事件库退役、语音下线、检查器下线、scripted 评测换代）的「最后一公里」未闭环，大量零调用函数、空壳包、死枚举、死配置与前端死 UI 残留，且多处靠绕过路由或断言空桩的测试续命，形成「测试绿 ≠ 代码活」假象，持续误导后续开发。本变更集中清扫**已确认、无歧义**的部分（全仓交叉搜索零生产消费），零计费口径变化。

## What Changes

- **基础设施**：删 shared/{config,db,events} 三个空壳包、shared/auth/require_auth.py 整模块、jwt_auth.get_user_id_from_token、users.resolve_username、ops_console.IDENTITY_LABELS；超管判定收敛到 shared/users.is_superuser。
- **models/constants.py**：删 7 个死枚举（AgentStatus/ConversationStatus/MessageRole/SOPStatus/MemoryMode/ModelProvider/BugStatus）、ALL_STATUS_ENUMS、LockStatus.EXPIRED 与 LockReleaseReason.FORCE 两个死值；**同步下调 tests/arch/unit/test_ssot_enum_strenum.py 的 MIN_DISCOVERED_ENUMS 门禁**（需求方已批准联动）。
- **config/settings.py**：删 14 个零消费配置项（DEVICE_ENGINE、8 个 DEVICE_LOG_* 遗物、DEVICE_SERIAL、SERVER_PORT、SCREENSHOT_DIR、EXPORT_DIR、LOG_DIR）；修正 test_eval_runner 的无效 override。
- **task_list**：删 deepseek_billing.py / engine_adapter.py / log_history.py 三个整模块；recover_orphaned_tasks 垫片（测试改指 sweep_stale_tasks）；attachments 旧收集函数簇与别名；api.py 死函数簇（insert_task_events、store_task_media、add_usage_hourly、task_stats_by_agent、assistant_names_by_agent、materialize_config_file、set_config_load_message、build_case_requirement、case_project_code）；task_runner 死计价函数对、RESULT_STATUS_MAP、ephemeral/yaml_path 死变量、agent_id 残迹参数链；sweep_mark.write_stop_timeout_ids；media_storage.reset_media_storage；序列化器 legacy 字段（agent_id/assistant_route/attachment/case_title）与不可达旧分支。**保留** TaskEvent/TaskMedia/TaskUsageHourly 模型与表（读链仍活或属另行裁决）、attachment_filename 读回退。
- **device_pool/serial_log**：删 manager 死函数（DeviceDetector.detect、judge_status、reset_status_sync_cache、wireless_ready_hint）、Device.is_occupied、port_service.disabled_port_note。**不动** api.py 白名单与写路径（属 converge-device-pool-writes-to-api 变更）。
- **ai_assistant**：删 scripted 自测链（evaluate_target、record_eval、services/eval_rulers.py 整模块、eval_samples 的 W1-W5 死样本）——**保留 AssistantEvalRun 模型与表**（历史归档，删表另行裁决）；AssistantThreadLogView 的 report_id 不可达委托分支与 post（测试改打真实路由）；model_configs.is_referenced；api.__all__ 四个无外部调用导出摘除；不可达 raise、serializer_class=None 惰性属性、management 空壳包。
- **dashboard**：删 /api/devices/stats/ 与 /api/cases/stats/ 整条链（视图+路由+陪葬 import）；ai_usage 六函数 agents=None 死参数与 del agents；_agg_by_role/_agent_usage 空桩与 payload by_role/agents 字段；voice_today/voice_total/voice_by_model 死口径。
- **usage_ledger**：删 record_voice_event（生产零调用）；pricing.py:70 永假死分支。**不动**计价双轨与 cache_creation 参数（钱口径，属 fix-eval-usage-billing）。
- **case_manager/bug_manager**：删 serializers.py（CaseProjectSerializer 零引用）、ConflictError.log 死属性、management/commands 空目录；bug_manager _created_by 的 agent.owner_id 永死分支与 agent_id docstring（**保留** BugTicket.agent_id 字段，废弃另行裁决）。
- **前端同链删除**：ai-assistant/api/agents.ts 三个死函数与 TASK_KIND_* 死常量；dashboard 的 agent-usage-list 死 UI 块、byRole/agents 映射与类型、语音切换按钮与 voiceByModel 数据链（含「Voice 来源 Token 消耗」图表若存在）。
- **测试同删/改**：消费上述死代码的测试用例同删或改指活路径（test_eval_rulers、test_live_run 的 record_eval 段、ThreadLog 绕路由用例、agents==[] 空桩断言、test_usage_ledger 的 voice 段等）。
- 随删除同步修正受影响模块的 docstring 清单与 `__all__`（纯注释修正，不含 AGENTS 红线条款——那属 align-backend-docs-with-code）。

## 关联文档

无新增 PRD 需求编号——退役清扫变更，问题来源为后端审计报告（dev_docs/DEV_TEST/REVIEW-后端废弃代码与技术债审计.md）第四节 D-1~D-43 确认项。需求方已批准：无歧义子集范围、枚举清理与门禁联动下调。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `model-usage-ledger`: 移除「Voice 用量图表」requirement（语音通道已整体退役，图表数据恒空）；「用量来源过滤」保留 usage_summary 的 source 过滤能力、移除仪表盘 voice_today/voice_total 义务。
- `dashboard-chapter-boards`: 「Chapter shells are solid while metric cards stay dashed」中智能体用量卡的表述随死 UI 退役移除（后端恒发 agents:[]，该卡永不渲染）。
- `task-card-sop-form`: 「弹窗提交载荷按用例来源区分」对齐现行真实契约（workflow_id 必填、agent_id/device_label/case_title 已退役、material 可选）——现 spec 仍要求发送 agent_id，与前后端代码均不符，属退役遗留的规格漂移。

## Impact

- **backend**：shared/、models/、config/、task_list、device_pool、serial_log、ai_assistant、dashboard、usage_ledger、case_manager、bug_manager、ops_console（约 25 个文件删除/缩减）。
- **frontend**：ai-assistant（agents.ts/constants.ts）、dashboard（index.vue/composables/types）。
- **tests**：arch（枚举门禁）、task、device、ai_assistant、dashboard、knowledge_search、case、bug_ticket 相关用例同删/改。
- **明确排除（另行裁决/另单）**：Node 契约（D-3）、AssistantEvalRun 删表、BugTicket.agent_id 字段迁移、purge_disconnected_devices、observe 占用链、upload-file 与 devices/current 端点、ops 三端点、RETIRED_AUTH_PATHS 垫片（404→401 行为变化）、device_pool api 白名单（变更④）、usage_summary 函数本体、计价双轨/cache_creation（变更⑥）、success 历史口径垫片、ModelUsage.metadata 字段。
- **协调**：建议先合并 fix-task-runtime-p0-defects（费用回写改源后再删事件写函数）；frontend ai-assistant/AGENTS.md 中「agents.ts 仍被 task-list 引用」的失实红线由 align-backend-docs-with-code 先行修订，本变更删除 agents.ts 前须确认该修订已合并。