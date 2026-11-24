# REVIEW — 后端废弃代码与技术债审计（backend/）

> 审计时间：2026-11-19 16:25–16:55（Asia/Shanghai）
> 审计方式：全程只读，未修改任何代码与规则文档。lead 全局标记扫描 + `--check-boundaries` 实测；四个只读子代理并行深查全部 12 个 app 与 shared/gateway/config/models；**全部 P0 级指控与关键红线指控由 lead 亲自 read/grep 二次验证**。
> 死代码判定口径：全仓交叉搜索（backend/、frontend/、engines/、tests/、utils/、run.py、openspec/），含 URL 路径字符串、getattr/字符串路由、管理命令名、settings 字符串等动态引用形态；engines 侧已验证零 `apps.*`/`django.*` import，不构成隐式调用方。
> **与既有报告的关系**：本日 15:49–16:10 已产出 [REVIEW-Agent文档审计复核与修复方案.md](REVIEW-Agent文档审计复核与修复方案.md)（下称「前报告」）。本报告与其重叠的条目标注前报告编号（A1/A2/B4/C1/D2/D3/S1/N2 等），**不重复立单**；其余为本次新增发现。
> **时效警示**：前报告披露另一会话正在实施 `fix-agentscope-usage-defects`（涉及 record.py/runner.py/usage_ledger/*）。本报告行号以审计时点实测为准，动手前须与该会话协调，避免撞车。

---

## 一、总体结论（结论先行）

**backend 主链路健康、分层纪律总体良好，但「退役变更的最后一公里」普遍未闭环。** 本次审计确认：

| 类别 | 规模 | 最严重项 |
|---|---|---|
| P0 功能缺陷 / 安全债 | 6 项（lead 全部亲验） | 中断任务费用被清零；设备锁可伪造身份；心跳瞬时故障永久停跳 |
| 红线违规 / 规则冲突 | 2 处确认违规 + 3 处越权 + 1 处两级规则冲突 | dashboard 跨 App import `usage_ledger.rates`；device_pool 写库整体绕过 api.py |
| 确认死代码 / 死配置 | **约 70 处**（3 空壳包、3 整模块、7 死枚举、14 死配置项、40+ 死函数、多条完整退役链） | scripted 自测链、事件/小时计费写链、observe 占用链 |
| 疑似死代码（需裁决） | 约 12 处 | publish 无前端入口（已登记 D2）、ops 3 端点、upload-file 端点 |
| 一般技术债 | 30+ 项 | 吞异常无日志（账本/仪表盘）、N+1、6 个超长函数、计价双轨 |
| 文档漂移 | 30+ 处（AGENTS/ARCH/PRD/活跃 spec/docstring 六个层面） | WS 生产点（已登记 B4）、task_list AGENTS 三处关键失真 |
| 门禁盲区 | 3 处 | `--check-boundaries` 漏报 rates import；CI 只 collect-only（已登记 N2）；test_channels 与退役门禁互相矛盾（已登记 C1） |

**正面结论**：serial_log 是分层模板（唯一写点 api.py、JSON 退役彻底）；report_generator 表/端点/前端三线一致退役；case_manager 旧四类型经三步迁移收敛干净；JWT 吊销落库、响应信封、snake_case、Redis 退役均执行到位；ai_assistant/dashboard 无 >80 行函数、无裸 except。**问题不在架构设计，而在退役清扫与文档同步的系统性欠账。**

---

## 二、P0：功能缺陷与安全债（lead 已逐条亲验）

### P0-1 清扫逻辑把中断任务的费用清零【新增】
- **位置**：[api.py:181](../../backend/apps/task_list/api.py#L181)（sweep 调用）→ [api.py:1198-1215](../../backend/apps/task_list/api.py#L1198) `rollup_task_cost`。
- **事实链（已验证）**：`rollup_task_cost` 聚合 `TaskEvent(event_type="ModelCallEndEvent")` 回写 `cost_*`；但 `insert_task_events`（api.py:1012）全仓零调用方，TaskEvent **生产写点已随事件库退役消失**（event_store/fold/TaskEventSink 均不存在）。正常完成任务走 ledger（task_runner.py:534-535 `summarize_ledger_cost`），而**心跳超时被 sweep 收口的任务，cost_total 被恒写 0**——真实费用在 usage_ledger 里，任务表却显示免费。
- **处置**：`rollup_task_cost` 改读 `usage_ledger.api` 的费用汇总，或随事件表退役一并删除。属缺陷修复（恢复正确数据），非口径变更。

### P0-2 用例编写/需求拆解是占位桩：一条永远假成功并写假用例行入库，一条永远失败【已登记 A2，有意暂缓】
- **位置（已验证）**：[task_runner.py:439-441](../../backend/apps/task_list/task_runner.py#L439) `_attempt` 写死 `return {"passed": True, "rows": [{"title": task.title or "用例", "module": "默认"}]}`，经 `import_case_rows` 把假用例写进用例库；[task_runner.py:464-474](../../backend/apps/task_list/task_runner.py#L464) `_finish_team` 把上传文档的 Markdown 正文传给 `run_team_breakdown`，引擎侧 `json.loads` 必然失败 → 需求拆解永远 failed。
- **定性修正（沿用前报告）**：暂缓有书面记录（活跃变更明文「GoalPipeline 生产接线…需求方明确暂缓」），不是失控缺陷；但 **interim 编造数据入库不可接受**，且前报告 N10 指出 A1（发布门禁恒假）与 A2 耦合——只修 A1 不修 A2 会打开编造数据闸门。
- **处置**：按前报告决策项 1 执行（推荐 b：fail-closed，不入库、明确失败原因）。

### P0-3 lock_device 允许请求体伪造 user_id【新增，安全】
- **位置（已验证）**：[device_pool/views.py:348](../../backend/apps/device_pool/views.py#L348) `user_id = getattr(request, "user_id", "") or request.data.get("user_id", "")` —— 身份为空时回退客户端 body，可把设备锁到任意用户名下（manager.py:508-514 用该值写 `locked_by`）。其余端点均只信 JWT 注入的 `request.user_id`。
- **处置**：删除 body 回退分支。一行修复。

### P0-4 心跳遇瞬时 DB 故障即永久停跳 → 活任务被误收【新增】
- **位置**：[task_runner.py:311-313](../../backend/apps/task_list/task_runner.py#L311) `_beat` 任何异常（含瞬时连接错误）置 `still=False`，不再挂下一拍；`SWEEP_STALE_SECONDS=45`（api.py:162）后 sweep 把仍在运行的任务收成 `interrupted/process_lost`；工作线程随后 `claim_terminal` 因状态非 running 抢不到（api.py:554），**真实结果丢失**。
- **处置**：心跳失败重试下一拍，或连续 N 次失败才停跳。

### P0-5 View 直写 ORM 清空任务 → 截图文件泄漏【新增】
- **位置（已验证）**：[task_list/views.py:291](../../backend/apps/task_list/views.py#L291) `AgentTaskClearAPIView.post` 直接 `Task.objects.all().delete()`，绕过 [api.clear_agent_tasks](../../backend/apps/task_list/api.py#L701)（后者还删截图文件）→ 每次清空都泄漏磁盘媒体。另 views.py:90-91、151-152 在 View 内 `task.save()` 直写 result。
- **附带发现**：View docstring 称「清空**当前用户可见**的全部任务」，实际 `Task.objects.all()` **无用户过滤、全平台删除**（api.clear_agent_tasks 同样 `del agent` 全删）——调试端点的权限面与文案双重失真，需一并裁决。
- **处置**：clear 改调 api；result 初始化下沉 api 写原语；明确该端点是否应按用户过滤。

### P0-6 评测真模型调用永远按 0 token 入账【新增，钱口径】
- **位置（已验证）**：[live_runner.py:158-165](../../backend/apps/ai_assistant/services/live_runner.py#L158) usage 字典硬编码 `input_tokens: 0, output_tokens: 0`；A1 探针是两轮真模型调用（engines/backend_bridge/workflow/eval_probe.py:51-57 原样透传），`assistant_eval` 来源账行费用恒 0。docstring「用量带回给账本」与事实相反。
- **处置**：从 reply_stream 事件/record.usages 提取真实 token（参照 assistant_threads.py:255 做法）。**涉及钱与 token 统计口径，必须先提变更申请**；建议与前报告 A4（双模型错账）合并为一份钱口径变更申请。

### P0-7 publish 端点无前端调用方，新名片永远 draft、测试对话必然被拒【已登记 A1/D2】
- **位置（已验证）**：ai_assistant/urls.py:44-48,79-83；views_drf.py:507-547；frontend/src/modules/ai-assistant 全目录 grep `publish` **零命中**。连锁：`_snapshot_for`（assistant_threads.py:155-156）要求 published，否则抛「助手尚未发布」。
- **处置**：按前报告执行顺序 2/5（A1 门禁修复 + D2 发布 UI），不重复立单。

---

## 三、红线违规与规则冲突

### R-1 dashboard 跨 App import usage_ledger 内部计价件【确认违规，门禁漏报】
- [dashboard/ai_usage.py:20](../../backend/apps/dashboard/ai_usage.py#L20) `from backend.apps.usage_ledger.rates import DISPLAY_FX_DATE, DISPLAY_FX_USD_CNY`（lead 亲验）。rates.py 非 Model 非 api.py，违反 apps/AGENTS §1.2。
- **门禁盲区**：`python utils/gen_arch_stats.py --check-boundaries` 实测**零违规通过**——检查器不覆盖「跨 App import 内部常量/计价件」形态。
- **处置**：usage_ledger.api 增只读导出（如 `display_fx()`），dashboard 改调 api；同时补边界检查器规则。

### R-2 device_pool 写库整体绕过 api.py，api 白名单形同虚设【确认违规 + 死代码】
- 真实写路径：View → registry/state_machine（views.py:170,176,215-216,242,287-294,319,334,351,359）；[api.py](../../backend/apps/device_pool/api.py) 白名单 6 函数（list_devices/ensure_device/acquire_device/release_device/release_device_locks_for_device/use_device）**全仓零调用方**，`get_online_devices` 唯一调用方 engine_adapter 本身是死模块（见 D-8）→ 传递性死亡。
- api.py:4 docstring「写逻辑下沉到 service.py」——service.py 不存在（实为 manager.py）；device_pool/AGENTS.md 为 **0 字节空文件**（已登记 S1 名单）。
- **处置（需裁决）**：a) View 写操作收敛进 api.py（manager 作内部实现）；或 b) 删死白名单、修订 app 级 AGENTS 明确「manager 即写库层」。现状是规则与代码互相矛盾，两条路都走变更流程。

### R-3 ai_assistant View/启动钩子绕过 api 门面直调 services【确认越权】
- views_drf.py:497-499 直调 `services.live_runner.start_live_eval`；views_drf.py:363,383 直调 `services.log_ticket`；**apps.py:15-18 ready() 直调 `services.mark_interrupted_running`，该函数在 service 内直接 `thread.save()`（assistant_threads.py:347）且不在 api.__all__**——一条完全绕开门面的写库路径；views_drf.py:518 调 api 私有函数 `_release_payload_for_assistant`，发布门禁散在视图层。
- 背景：ai_assistant/AGENTS.md:7「写库只在 api.py」与实际架构不符——ORM 写入分布在 services/ 五个模块，api.py 只是门面（见文档漂移 DOC-6）。
- **处置**：api 增补编排导出；发布门禁下沉 publish_assistant/publish_workflow；AGENTS 表述走变更申请改为「写库入口只经 api.py，内部写库层在 services/」。

### R-4 knowledge_search View 层业务编排越权【确认】
- [views.py:213-257](../../backend/apps/knowledge_search/views.py#L213) `EvalRunListAPIView.post` 45 行编排：题量上限校验、running 冲突检查、跨 App ORM 读 AIModelConfig、三份快照组装、随机种子、成本预估；`_retrieval_snapshot`（39-57）同样 View 内读 ORM 拼快照。魔法值 100（:223）、2**31（:253）。
- **处置**：api.py 增「触发评测」编排函数，View 退回分发；常量命名化。

### R-5 case_identity 纯函数例外：两级规则冲突【需裁决】
- dashboard/ai_usage.py:17、report_generator/report_inventory.py:21、bug_manager/api.py:18 import `task_list.case_identity`。**task_list/AGENTS.md 明文允许**，但上级 apps/AGENTS §1.2 严禁跨 App 内部实现 import 且上级优先。
- **处置**：要么把 `case_identity_label` 收进 task_list/api.py 导出，要么修订上级红线例外清单（改规则必须先请示）。不要静默维持现状。

### R-6 其他边界事实
- task_runner.py:131,170 import `usage_ledger.pricing.price_usage`——所在函数 `_price_call_costs`/`_price_costs` 全仓零调用（死函数），且与归档变更 unify-platform-usage-billing tasks 2.2「删除对 price_usage 的直接调用」声明矛盾（删了调用点、留了函数与 import）。随死代码删除。
- [pricing.py:17,215](../../backend/apps/usage_ledger/pricing.py#L215) import 并调用 engines `DeepSeekBilling._is_peak_time` **私有方法**，绕过 engines/backend_bridge/model_billing 宣称的唯一公开入口；`cost()/snapshot()` 生产零消费（仅 tests）。高峰规则复用应在 engines 侧立公开函数（走 engines AGENTS 流程）。
- serial_log/port_service.py:30 import engines 私有函数 `uart_log.detect._port_in_use`——方向合规但碰私有实现，建议 engines 暴露公共探测口。
- shared→app 反向依赖（分层 smell）：shared/users.py:63 import ai_assistant.api；jwt_auth.py:56 惰性 import accounts.api（有防环注释）；accounts/api.py:234 import ai_assistant.api。均走对方 api.py 合规、无环，但 shared 底座反向依赖具体 App，登记为分层债。

---

## 四、确认死代码清单（约 70 处，均附全仓搜索证据）

> 处置默认值：随「退役清扫」OpenSpec 变更批量删除，代码与消费它的测试同删；涉表结构者单列迁移评审。

### 4.1 基础设施（shared / models / config / gateway）

| # | 位置 | 内容 | 备注 |
|---|---|---|---|
| D-1 | backend/shared/{config,db,events}/ | 三个 0 字节空壳包，全仓零引用 | 整目录删 |
| D-2 | [shared/auth/require_auth.py](../../backend/shared/auth/require_auth.py) | 整模块（require_auth/require_superuser）零消费者；原消费方 evaluator/test_runner 已退役 | 超管判定另有 knowledge_search/views.py:65 与 shared/users.py:23 两份同构实现，收敛到 users.is_superuser 一处 |
| D-3 | [models/ui_nodes.py](../../backend/models/ui_nodes.py) | Node 全仓零消费者（engines 只产原始 XML）；自述「保留为数据契约」所依赖的 engine-protocol 规格已归档 | 可退役；若留契约须重新立项，否则属无主死代码 |
| D-4 | [models/constants.py](../../backend/models/constants.py) | 7 死枚举：AgentStatus(:46)、ConversationStatus(:53)、MessageRole(:60)、SOPStatus(:68)、MemoryMode(:111)、ModelProvider(:118)、BugStatus(:103)；ALL_STATUS_ENUMS(:127) 零引用；活枚举死值 LockStatus.EXPIRED(:27)、LockReleaseReason.FORCE(:36) | **归档任务声称已删 ConversationStatus 实际仍在（退役未闭环）**；⚠️ 删 7 个后打破 [test_ssot_enum_strenum.py:26](../../tests/arch/unit/test_ssot_enum_strenum.py#L26) `MIN_DISCOVERED_ENUMS=11` 下限门禁，须同步改门禁 |
| D-5 | [config/settings.py](../../backend/config/settings.py) | 14 个零消费配置项：DEVICE_ENGINE(:188)、DEVICE_LOG_SERIAL_PORT/BAUD/BUFFER_SECONDS/BUFFER_MAX_LINES/WINDOW_SECONDS/BASELINE_SECONDS/LOG_DIR/FILE_MAX_BYTES(:258-278)、DEVICE_SERIAL(:350)、SERVER_PORT(:351，run.py/vite 直读 env)、SCREENSHOT_DIR(:364)、EXPORT_DIR(:367)、LOG_DIR(:368) | tests/knowledge_search/integration/test_eval_runner.py:32 `settings.LOG_DIR=tmp_path` 是**无效 override**，一并修 |
| D-6 | [gateway/middleware.py:13-19,87](../../backend/gateway/middleware.py#L13) | RETIRED_AUTH_PATHS 5 条 `/api/ai/auth/*` 免 JWT 垫片，前端零调用；APPEND_SLASH=False 下本就 404 | 删除有轻微行为变化（未登录 404→401），随 api-path-convention 收尾 |
| D-7 | shared/auth/jwt_auth.py:206-209 `get_user_id_from_token`；shared/users.py:8-20 `resolve_username`（含裸 except）；ops_console/api.py:61 `IDENTITY_LABELS` | 三个死函数/死常量，全仓仅定义处 | 删除 |

### 4.2 task_list（事件/计费写链整体退役，读链残留）

| # | 位置 | 内容 |
|---|---|---|
| D-8 | [deepseek_billing.py](../../backend/apps/task_list/deepseek_billing.py) | 自述「已废弃占位，请 git rm」；task_cost.py 已接管；**AGENTS.md:10 仍写「计费 deepseek_billing」** |
| D-9 | [engine_adapter.py](../../backend/apps/task_list/engine_adapter.py) | 整模块死亡（resolve_device_serial 零调用）；AGENTS 仍写「task_runner→engine_adapter→引擎」 |
| D-10 | [log_history.py](../../backend/apps/task_list/log_history.py) | 整模块死亡，且仍读退役 JSON（device_log_keywords.json）——serial_log/AGENTS:32 红线违例样本（虽无人调用）。keywords.py/sources.py 已合规切库 |
| D-11 | api.py:214-216 `recover_orphaned_tasks` | 兼容旧入口垫片，生产零调用（启动走 apps.py:48→sweep_stale_tasks）；仅 2 个测试消费，改指向 sweep |
| D-12 | attachments.py:164-166 `parse_task_attachment_bytes` 别名；:184-210 `collect_task_files`；:295-318 `collect_document_files`；:15 `MAX_CASE_DOCUMENTS` | 旧收集函数簇，零调用 |
| D-13 | api.py 死函数簇：`insert_task_events`(:1012)、`store_task_media`(:1021)、`add_usage_hourly`(:1146)、`task_stats_by_agent`(:129)、`assistant_names_by_agent`(:783)、`materialize_config_file`(:298)、`set_config_load_message`(:359)、`build_case_requirement`(:330)、`case_project_code`(:353)、`clear_agent_tasks`(:701，View 绕过另起一套) | TaskEvent/TaskMedia/TaskUsageHourly **生产写点全部消失**；TaskUsageHourly 仅剩 dashboard 归档只读。`build_sop_run_input`(:324) 仅测试消费。⚠️ insert_task_events 删除与 P0-1 联动 |
| D-14 | task_runner.py：`_price_call_costs`(:120-155)、`_price_costs`(:158-189)（重复计价逻辑）、`RESULT_STATUS_MAP`(:24-27，仅测试)、`ephemeral/yaml_path` 死变量(:482-483)与恒假清理分支(:575-576)、`agent_id` 残迹参数链(:343-346,412,477,584，所有调用点恒传 0) | 生产计费走 api.summarize_ledger_cost |
| D-15 | sweep_mark.py:13-22 `write_stop_timeout_ids` | 仅测试消费；run.py:431-445 自己重复实现同一路径同一 JSON 形状。删写函数，把文件格式契约写进 sweep_mark 注释作单一真相源 |
| D-16 | media_storage.py:230-233 `reset_media_storage` | 零调用（含 tests） |
| D-17 | serializers.py legacy 字段：agent_id(:21-29)、assistant_route(:44)、attachment(:46)、case_title(:36)；validate 的 agent_id-only 旧路径(:48-51)不可达（View 强制 workflow_id） | 前端不发、View 不读 |
| D-18 | models.py:21-22 `attachment_filename` **写侧已死**（前端提交不传、create_task 形参无人填非空值）；**读侧仍活**（TaskBoard.vue:197 渲染历史行） | 保留读回退；create_task 的 attachment 形参与 planner_input 分支经变更退役。planner_input/yaml_body/load_message 仅存前端 types 无组件消费 |

### 4.3 device_pool / serial_log

| # | 位置 | 内容 |
|---|---|---|
| D-19 | api.py 白名单 6 函数 + get_online_devices | 见 R-2，整体空转 |
| D-20 | manager.py：`DeviceDetector.detect`(:74-94)、`judge_status`(:386-400)、`reset_status_sync_cache`(:54-59，docstring 称测试用但无测试用)、`wireless_ready_hint`(:136-153，仅测试)；models.py:37-39 `Device.is_occupied` | 零调用 |
| D-21 | manager.py:359-364 `purge_disconnected_devices` | 过滤 status="DISCONNECTED"，但枚举只有 ONLINE/BUSY 且全仓无写入点 → 只清历史遗留行。**疑似**，确认存量后删或降为一次性命令 |
| D-22 | port_service.py:138-150 `disabled_port_note` | 零调用（AI 日志查询工具已不调） |
| D-23 | observe 占用链：views.py:293-294,327-335、urls.py:27 disconnect-observe、manager.py:578-601、contracts.py:26 RUNNER_OCCUPIED_PREFIXES | 前端 connect 只发 {activate}，全仓无 mode="observe" 触发者；runner 前缀保护分支空转（acquire_device 已死）。原消费方设备检查器已随 element_locator 下线。**疑似整链退役**，确认后走 OpenSpec |
| D-24 | **口径修正**：[pool.py](../../backend/apps/device_pool/pool.py) DevicePool 单例**不是死代码**——列表 current 字段与 activate/connect 依赖它，前端消费 current。但作用域已缩到 app 内，`device` 应从 api.__all__ 移除 | 保留 |

### 4.4 ai_assistant / dashboard

| # | 位置 | 内容 |
|---|---|---|
| D-25 | scripted 自测整条链：api.py:474-509 `evaluate_target`（零调用）→ :600-610 `record_eval`（仅死函数与测试）→ models.py:208-227 `AssistantEvalRun`（自述只保留历史）→ services/eval_rulers.py 整模块 → eval_samples.py W1-W5 死样本（GATE_IDS 过滤后永不出现） | 上一代评测残留，仅测试续命；api.eval_passed:631 已明示旧记录不参与判定。表删/归档需裁决 |
| D-26 | dashboard/urls.py:19-20 + views.py:211-244 `/api/devices/stats/`、`/api/cases/stats/` 整条链 | 全仓仅定义处；陪葬 _user_cases_q(:57-60) 与三个 model import(:13) |
| D-27 | ai_usage.py 六函数 `agents=None` 死参数(:24,126,386,417,438,474) + `del agents`；四处 docstring 仍写「None 时自行装载」与行为相反 | 全仓无调用方传 agents |
| D-28 | ai_usage.py:114-123 `_agg_by_role`/`_agent_usage` 空桩（恒 {}/[]）+ payload by_role/agents 字段 + 前端死 UI（index.vue:287-302 agent-usage-list 永不渲染；useDashboardStats.ts:160-161 映射无组件消费） | 测试断言 agents==[] 把空桩钉死。契约双边同删 |
| D-29 | views_drf.py:327-345 AssistantThreadLogView 的 report_id 委托分支 | 路由不可达（带 report_id 的路径直挂 LogFileView）；测试绕过路由直传 kwarg 续命；post 经 HTTP 恒 409 无调用方 |
| D-30 | services/model_configs.py:81-83 `is_referenced` | 零调用；delete_model_config:74 内联同一查询 |
| D-31 | api.py __all__ 四项无外部调用：list_messages(:138)、finish_message(:122)、replace_kinds(:147)、get_role(:135，仅测试) | 从 __all__ 摘除，函数本体保留内部使用 |
| D-32 | services/sop_workflows.py:8-18 `WORKFLOW_FIELDS` | 仅测试契约守卫引用，生产从不读取。定性「测试专用契约常量」，保留则注明 |
| D-33 | 零散：api.py:280 不可达 raise；views_drf.py:510,531 `serializer_class=None` 惰性属性；management/ 空壳包；eval_samples enabled 机制恒空转（全部 enabled=True，enabled_only=False 无调用） | 随手清理 |
| D-34 | 前端 ai-assistant/api/agents.ts:6-26 三函数调用已退役的 /api/ai/agents/*（必 404，无人 import）；constants.ts:7-8 两个 TASK_KIND 死常量 | 模块 AGENTS 声称的引用方不存在（已登记 D1）。EVAL_* 仍活，保留 |

### 4.5 case_manager / report_generator / bug_manager / usage_ledger / ops

| # | 位置 | 内容 |
|---|---|---|
| D-35 | [case_manager/serializers.py:8-20](../../backend/apps/case_manager/serializers.py#L8) `CaseProjectSerializer` | 全仓仅定义处；ViewSet 走手写序列化。整文件删 |
| D-36 | case_manager/api_projects.py:37 `ConflictError.log` 属性 | 零消费 |
| D-37 | case_manager/management/commands/ 空目录（import_case_yaml 已退役） | 删空目录 |
| D-38 | bug_manager `agent_id` 快照链：api.py:228 `getattr(task,"agent_id",0)` **生产恒 0**（Task 无此字段，lead 亲验）；api.py:323-324 `_created_by` 的 agent.owner_id 回落**永死分支**；models.py:46 BugTicket.agent_id（带 db_index）；前端 types.ts:38 声明无组件消费；测试用 SimpleNamespace(agent_id=7) 掩盖事实 | 删回落分支与 docstring；字段废弃需迁移 + 前端 DTO 同步（裁决项） |
| D-39 | usage_ledger/api.py:318-384 `record_voice_event` | 生产零调用（唯一调用方 knowledge_assistant app 已删），仅测试消费；默认模型回落 qwen3.5-omni-plus-realtime 是语音遗物 |
| D-40 | voice 口径残留链：api.py:654-655 voice_today/voice_total 恒空 + ai_usage.py:276 voice_by_model + 前端 dashboard/index.vue:52,340-348 语音切换按钮 | 前后端一条链，随退役变更同删（展示口径，非计费口径） |
| D-41 | usage_ledger/pricing.py:70 `return "Realtime" if …` | :68 已拦截所有含 realtime 的名字，该条件**永假**，死分支 |
| D-42 | usage_ledger/pricing.py:80 `price_usage(cache_creation_tokens=…)` | 接收后从未使用；ModelUsage.cache_creation_tokens 只存不算（api.py:269,443 照传）。涉钱口径，登记事实 |
| D-43 | report_generator/models.py（6 行墓碑）/admin.py（1 行） | Report/ReportTemplate 表已删（迁移 0003 DeleteModel），无消费者。**迁移 0001-0003 必须保留**（删掉会让已部署库迁移图断裂）；app 必须留 INSTALLED_APPS（路由挂载依赖）。墓碑可保留（防复活声明）或删 |

---

## 五、疑似死代码 / 需裁决项（不宜径删）

| # | 位置 | 事实 | 裁决问题 |
|---|---|---|---|
| S-1 | task_list/urls.py:23 `POST /api/tasks/upload-file/`（views_upload.py:93-178） | 前端零调用，仅路径解析测试 | 是否有仓外脚本消费？保留则先修文件名卫生（见 T-12） |
| S-2 | device_pool/urls.py:23 `GET /api/devices/current/` | 前端用列表 current 字段，仅 devices.yaml 契约消费 | 与测试契约一并评估退役 |
| S-3 | ops_console/urls.py:36-49 `model-grants/`、`grant-author/`、`revoke-author/` | 前端零调用；grant-author 属在途变更 assistant-author（前端只做隐藏未做授予 UI）；model-grants 属已归档变更声称的前端未落地 | **补前端 UI 还是收编 Django Admin？** 后端先行/前端欠账，非纯废弃 |
| S-4 | usage_ledger/api.py:613 `usage_summary` | dashboard 已改调 usage_dashboard，生产零调用；但活跃 spec model-usage-ledger:99 仍要求 | 删前同步 spec |
| S-5 | report_inventory.py:242-243,280-291 `workflow_kind`/`module_count` 输出 | 前端 types 无此二字段、零渲染、无测试断言 | 确认意图后删，或补契约+DTO+测试 |
| S-6 | RoleViewSet/ModelConfigViewSet/AssistantViewSet 的 GET retrieve | 前端只用 list/create/patch/delete | 标准 CRUD 面，暂保留登记观察 |
| S-7 | usage_ledger/models.py:33 `metadata` 字段 | 所有写入方都填，全仓无读取方 | 审计追溯用途登记或退役（迁移评审） |
| S-8 | `_TERMINAL_STATUSES` 含 "success" 历史口径（report_inventory.py:30，task_runner.py:25、api.py:89、ai_usage.py:359 同样容忍） | 平台-wide 垫片 | 先查存量库是否仍有 status="success" 行，再统一清理 |
| S-9 | revision 乐观锁（已登记 D3） | 前端从不提交 revision → 静默放行后写者赢 | 前端补带 revision 或退役机制 |
| S-10 | knowledge_search/views.py:92 GET settings 恒返 `reindex_required: False` | PUT 后刷新页面「需重建索引」提示即消失，即使索引确实过期 | GET 用 retrieval._epoch_matches 实算 staleness |

---

## 六、一般技术债

### 吞异常 / 错误不上报（违反「错误要上报」）
| 位置 | 事实 |
|---|---|
| [usage_ledger/api.py:314-315](../../backend/apps/usage_ledger/api.py#L314) | `except (OperationalError, ProgrammingError): return None` **无日志**——record_run_usages（任务收口唯一入账路径）DB 抖动时费用静默缺失无痕迹，违反本 App AGENTS 红线 5「入账失败只记日志」 |
| usage_ledger/api.py:633-639,657-669 | usage_summary/usage_dashboard 捕获后返回空结构，无日志 |
| [usage_ledger/pricing.py:33-36](../../backend/apps/usage_ledger/pricing.py#L33) | 价目表读取失败静默返回空表 → **全部模型变 unpriced、费用归零**，无日志（钱相关事实） |
| [dashboard/ai_usage.py](../../backend/apps/dashboard/ai_usage.py) :48,76,85,104,277,330,401,429,452,495 | 十处 DB 异常无日志吞掉（:330 甚至 pass）——真实 DB 故障伪装成「用量为 0」 |
| ai_assistant/services/assistant_threads.py:216-217 | _run_turn broad except 只写用户消息不落日志，堆栈丢失（同模块 :229 有日志，对照） |
| task_list/api.py:1189-1195 `summarize_ledger_cost` | except 返回 0+note 未记日志 |
| device_pool/manager.py:110-111,168-170,185-186 | adb devices/getprop 失败静默空集/空串，无日志 |

### 计价双轨与口径冲突（钱相关，仅报事实，处置须变更申请）
- [rates.py:58-67](../../backend/apps/usage_ledger/rates.py#L58)（RATES，8 模型）与 pricing.json（13 模型）并存；pricing.py:101-114 先查 rates 再落 json → **pricing.json 的 4 个 deepseek 条目被完全遮蔽永不可达**。
- **键名失配地雷**：pricing.json deepseek 条目用 `input_cache_hit/input_cache_miss/output`，json 兜底路径读 `input_per_million/output_per_million/per_10k_chars`（pricing.py:135-139）——若 RATES 对应条目被移除，兜底按 0 计价。
- `qwen3.5-omni-plus-realtime` 两表口径冲突（RATES 80/300 元 priced vs json 0/0 unpriced）。
- pricing.json 语音条目（sambert×3、qwen3-tts-flash、livetranslate、omni-flash、asr）对应能力已下线；唯一存活条目 text-embedding-v4（retrieval.py:232 入账）。

### 性能
- **任务列表 N+1**：views.py:207 `.only(*TASK_LIST_FIELDS)` 缺 workflow_id/orchestration/kind/case_identity 四字段，序列化（api.py:855-865）逐行 deferred 加载 → 每行 4 条额外 SQL × 100 行；每行调 get_sop_workflow 未批量预取。
- **列表按 result 字符串过滤**：views.py:203 `result__contains=f'"workflow_id": {workflow_id}'` 依赖 json.dumps 空格格式，而 Task.workflow_id 列已存在（迁移 0009 回填）却不用。
- **bug sync 双倍提取 + N+1**：api.py:71 先 build_bug_drafts 判 skip，record_task_bugs(:40) 内再建一次；每次提取触发 _interrupt_reason 的 TaskEvent 查询（每任务一条 SQL）；`sync_visible_tasks` 全表扫描**无 owner 过滤、无扫描上限**（对比 report 侧 ≤1000/来源预算），任何登录用户可触发全量补录。
- case_manager/api_rows.py:275,288 `_lock_count` 同一事务调两次（SELECT FOR UPDATE + COUNT ×2）。

### 超长函数（>80 行）
| 位置 | 行数 |
|---|---|
| task_list/task_runner.py:477-581 `run_task_async` | ≈105（:558 用 `locals().get("step_rows")` 取局部变量，脆弱） |
| usage_ledger/api.py:216-315 `record_usage` | 100（19 参数+计价+幂等写混杂） |
| knowledge_search/eval_runner.py:108-205 `_run_async` | 98（正题/负题循环高度重复，可抽 _eval_one） |
| usage_ledger/api.py:387-473 `recalculate_usage_costs` | 87 |
| usage_ledger/pricing.py:73-156 `price_usage` | 84（rates+json 双逻辑） |
| task_list/views_upload.py:97-178 post | 82 |

### 重复逻辑（跨 App 重复有防火墙的结构性原因，但可沉纯函数）
- `_report_locator` 两份（report_inventory.py:294-310 vs bug api.py:327-343）→ 沉 task_list 纯函数（仿 case_identity 先例）；`_iso` 两份；`_task_title` 两份；`_user_id` 四份且语义不一致（dashboard 返 None/id，ai_assistant 返 str）→ 收进 shared。
- views_upload.py:44-82 docx/pdf 解析与 attachments.py:39-84 重复；扩展名白名单第二份(:16-35)。
- views.py:319-326 与 media_views.py:22-31 同一份 ETag/Cache-Control 逻辑两份拷贝。
- 厂商展示名逻辑两份（usage_ledger/api.py:521-523 vs :681）。
- serializers.py choices 与 models 常量双源（ai_assistant/serializers.py:5-6 自述「改一处必须改两处」）。
- 汇率 6.7132/日期三处重复（rates.py 真相源 + 前端 useDashboardStats.ts:57,156-157 + index.vue:53 兜底硬编码）。

### 健壮性 / 安全卫生
- **RefreshView 异常消息字符串分流**（accounts/views.py:141-146）：靠 `"expected refresh" in msg` 判断错误类型，与 jwt_auth 英文文案硬耦合；:127 类型检查与 verify_token 重复。
- **上传文件名未净化**（views_upload.py:112）：`f"{uuid4.hex}_{uploaded.name}"` 未经 _safe_name，含 `../` 可越出 UPLOAD_DIR（写侧无守卫，删侧才有）——疑似路径穿越，与 S-1 联动。
- **mass-assignment**（case_manager/views_drf.py:127）：`**(request.data or {})` 直灌 update_row，body 含 project_id/case_id/user_id 会 TypeError→500。
- **GET 带写副作用**：serial_log GET /ports/ 经 reconcile/list_ports 调 ensure_log_ports 写库（非幂等）；device_pool GET 列表自动切换全局 current 指针（多用户竞争，注释自认）；_current_probe_cache 无上限无锁。
- **生产代码探测测试进程**：eval_runner.py:60-61、assistant_threads.py:177、live_runner.py:26、apps.py:13 的 `"pytest" in sys.modules` → 宜 settings.TESTING 单源。
- **魔法值**：写工具集合两处真相源（api.py:450 "adb_tap" 哨兵 vs live_rulers.py:5 _WRITE_TOOLS）；前端 EVAL_UNAVAILABLE 逐字复制后端错误文案（改文案必断前端判断）；CAP_NOTE「10 个」与 engines MAX_PORTS=10 双份；SWEEP_STALE_SECONDS=45 与 HEARTBEAT_SECONDS=15 分居两处无注释；case_limit 999 双源（api_projects.py:62 vs models.py:39 常量）；eval estimate_cost 硬编码 200/80/60 且 chunk_size 与实际配置脱节。
- **计数语义失真**：bug api.py:245-256 无字段变化也返回 updated=True（计数虚高）；skipped 恒 0，skip 口径散在两处。
- **弱密钥兜底**：jwt_auth.py:40 secret 缺省 "change-me"（仅 DEBUG 态可用，生产守卫会拒绝）。
- **命名误导**：bug `_visible_bugs` docstring 称按可见 agent 过滤，实际返回 all()（Agent 可见性体系退役遗留语义）。
- `__import__("json")`/`__import__("sys")` 反模式（views_drf.py:676、apps.py:13）；assistant_threads.py:23 `__all__` 含不存在的 "create_thread"（import * 会 AttributeError）。

---

## 七、文档漂移清单（30+ 处）

> 改 AGENTS 红线/依赖边界条款**必须先提变更申请**；纯 docstring 修正可随退役单附带。建议与前报告 D-DOC 批合并为一个 docs 变更 + 一份红线变更申请。

| # | 位置 | 漂移 |
|---|---|---|
| DOC-1 | apps/AGENTS.md:41 + ARCH/PRD + **活跃 spec knowledge-assistant-voice**（归档 tasks 声称已删实际仍在） | WS 生产点宣称 1，代码为 0（已登记 B4；lead 亲验 routing.py 空清单） |
| DOC-2 | apps/AGENTS.md:38 | 公开路径只写 /api/auth/* /admin/ /static/；实际 _is_public 为 8 条前缀（/api/auth/* 表述过宽，logout/me 需 JWT）+ 三条旁路（RETIRED_AUTH_PATHS、log ticket、DRAIN 回环），漏 /media/ 与文档面 |
| DOC-3 | task_list/AGENTS.md:9,10,17,22 | 宣称 GET /api/tasks/{id}/report/（已下线，测试断言 404）；「事件写 event_store；计费 deepseek_billing」「task_runner→engine_adapter」（三者均死）；「读 AIAgent、filter_agents_for_user」（均已不存在，实际读 AssistantRelease） |
| DOC-4 | device_pool/AGENTS.md、dashboard/AGENTS.md、case_manager/AGENTS.md 均 **0 字节**；knowledge_search **无 AGENTS.md** | app 级约束真空（已登记 S1） |
| DOC-5 | bug_manager/AGENTS.md:9,22 | 「两类问题」实际三类（漏 requirement_breakdown）；依赖方向漏 TaskEvent 读 |
| DOC-6 | ai_assistant/AGENTS.md:7 | 「写库只在 api.py」——实际 ORM 写入分布 services/ 五模块，api 只是门面（见 R-3） |
| DOC-7 | usage_ledger/AGENTS.md:12 + 红线 2 | 「DeepSeek 走 engines/model_billing，其它读 pricing.json」——实际 DeepSeek 走 rates.py；「厂商只有两类」——已含 openai/grok（前报告 D5/N5 已登记）；文件表漏 rates.py |
| DOC-8 | accounts/apps.py:1 | 「本应用没有自有表」——实有 acc_token_revocations |
| DOC-9 | apps/__init__.py:1 | 「5 existing + 2 planned + 3 reserved」——实际 12 个 app |
| DOC-10 | ops_console/views.py:3-8 + AGENTS 接口表 | 端点清单缺 5 条；写口清单漏 ai_assistant.api 四授权函数；api.py __all__ 漏 set_model_use/set_assistant_author |
| DOC-11 | tests/AGENTS.md 迁移状态表 | 仍列 knowledge/、engines/agents/ 为 ✅（两目录已不存在）；自测与检测指令.md:75 业务 marker 仍列已退役 test_runner |
| DOC-12 | dashboard/ai_usage.py:1,3-4,129,238,293,300 | 「只读小时用量表」口径——实际主数据源是逐次账 ModelUsage，小时表仅归档读取；_task_qs「已登录用户可见」实际不按用户过滤 |
| DOC-13 | bug_manager/extract.py:1-7 | 自述「Pure extraction rules / knows nothing about Django models」——_interrupt_reason(:308-338) 函数内 import TaskEvent 并 ORM 查询。二选一：读取上移 api 注入，或如实改 docstring |
| DOC-14 | jwt_auth.py:1（FastAPI 面已退役）、drf_auth.py:7-9（DRF 迁移早已完成）、task_cost.py:3-6（引用三个不存在的 engines 模块）、upload_cleanup.py:1、task_runner.py:3、device_pool/api.py:3-4、manager.py:9-10、models.py:14（OFFLINE 枚举不存在）、serial_log/urls.py:1（「九个端点」实际 10）、views_upload.py:94（旧路径 /api/ai/upload-file）、api_rows.py:5（list_rows 不存在）、api_projects.py:4-7、case models.py:4-8、ks views.py:1-12、retrieval.py:5、assistant_threads.py:238-239（二元组实际四元组）、eval_rulers.py:1（五把尺子实际 7 项）、api.py:371（「供旧测试过渡」实际是生产回退路径）、test_ssot_enum_strenum.py:25（「constants 11」实际 14） | 纯 docstring 漂移合集，随退役单顺手修 |

---

## 八、门禁与测试盲区

1. **`--check-boundaries` 漏报**（lead 实测）：R-1 的 rates import 存活，检查器零违规通过——不覆盖「跨 App import 内部常量/计价件」形态。需补规则。
2. **CI python 门禁只跑 `pytest --collect-only`**（已登记 N2）：解释了 P0 缺陷与失效测试为何能存活。治理决策见前报告决策项 5。
3. **test_channels.py 自相矛盾**（已登记 C1/N3，lead 亲验）：[test_channels.py:79](../../tests/arch/unit/test_channels.py#L79) 断言 engines/agents **必须存在**，实测目录不存在；check_gates.py:475-477 退役门禁要求**不得存在**。真跑 unit 必失败，被 collect-only 掩盖。
4. **枚举下限门禁联动**：删 D-4 的 7 个死枚举会打破 MIN_DISCOVERED_ENUMS=11（现实际 14），须同步改门禁。
5. **「测试绿 ≠ 代码活」假象**：多条死代码靠绕过路由的测试（ThreadLog report_id 直传 kwarg）、断言空桩的测试（agents==[]）、SimpleNamespace 伪造字段（agent_id=7）续命。退役清扫时代码与测试同删。
6. **本地孤儿 pyc**（卫生项，gitignore 覆盖非仓库债）：gateway/config/models/case_manager 等 __pycache__ 存有已删模块的 .pyc（internal_token、step_types、import_case_yaml 等 12+），本地清理防「已删除包复活」误判。

---

## 九、迁移层

- **ai_assistant 84 个迁移**：AIAgent 0001 建、0070 删，其间约 15 个 RunPython 全部作用于已删模型（新装库纯历史空转）；多组加删循环（0013→0019、0025→0027、0038→0051、0045→0054 含 DROP TABLE、0009→0043）。**squash 0001–0072 收益明确**，保留现存表回填语义，按 OpenSpec 立项、正反向各跑一遍。
- **report_generator 0001-0003 必须保留**（0003 是删表记录）；可选 squash。
- case_manager 迁移链收敛干净（0020→0022→0025），无残留。

---

## 十、建议执行顺序与立单（与前报告合并，避免重复立单）

| 批次 | 内容 | 流程 |
|---|---|---|
| ① P0 缺陷修复 | P0-1 费用清零、P0-3 伪造身份、P0-4 心跳停跳、P0-5 clear 收敛 | 缺陷修复（恢复正确行为，非口径变更）；P0-2/P0-7 按前报告 A2→A1→D2 顺序，不重复立单 |
| ② 钱口径变更申请（一份打包） | P0-6 评测 0 token + 前报告 A4 双模型错账 + 计价双轨事实（M1）+ cache_creation 死参数 | **必须先请示**：改什么/为什么/影响面/怎么回退 |
| ③ 退役清扫 OpenSpec 变更 | 第四节 D-1~D-43 纯删除（零口径变化）+ 消费测试同删 + 纯 docstring 修正（DOC-14）+ 枚举门禁联动 | 与并发会话协调 usage_ledger/* 文件后再动 |
| ④ 文档批（并入前报告 D-DOC） | DOC-1~DOC-13 + 前报告 B/C/S 组 | 一个 docs 变更 + 一份红线变更申请（WS、公开路径、device_pool 写库层、case_identity 例外、ai_assistant 写库表述） |
| ⑤ 结构重构 | R-3/R-4 编排下沉 api、超长函数拆分、N+1、result 列过滤、重复逻辑收敛、吞异常补日志 | 常规 OpenSpec；计价函数拆分须保口径不变 |
| ⑥ 疑似项裁决后处置 | 第五节 S-1~S-10 | 需求方逐项拍板 |
| ⑦ 门禁治理 + squash | 边界检查器补规则、CI 执行门禁（前报告 N2）、test_channels 重写、ai_assistant 迁移 squash | 与前报告 D-TEST 合并 |

---

## 十一、需要决策的内容

1. **device_pool 写库层定性（R-2）**：a) View 写操作收敛进 api.py；b) 承认 manager 即写库层、删死白名单并修订 AGENTS。两条路都涉红线表述，须变更申请。
2. **case_identity 例外（R-5）**：收进 task_list/api.py 导出，还是修订上级红线例外清单？
3. **钱口径变更申请是否批准打包**（批次②）：评测 0 token + A4 + 计价双轨登记。
4. **ops_console 三个无前端端点（S-3）**：补前端 UI 还是收编 Django Admin？
5. **疑似死端点消费方确认（S-1/S-2/D-23）**：upload-file、devices/current、observe 链是否有仓外消费者？确认后退役。
6. **BugTicket.agent_id 字段（D-38）**：废弃（迁移+前端 DTO 同步）还是保留恒 0 快照？
7. **AssistantEvalRun 表（D-25）**：删表还是归档保留？
8. **Node 数据契约（D-3）**：退役删除，还是在活跃规格重新立项保留？
9. **清空任务端点权限面（P0-5 附带）**：全平台删除是否符合预期？是否应按用户过滤或限超管？
10. **枚举清理与门禁联动（D-4）**：批准删 7 死枚举并同步下调 MIN_DISCOVERED_ENUMS？
11. **立单合并确认**：本报告批次④⑦与前报告 D-DOC/D-TEST 合并、P0-2/P0-7 沿用前报告 A2/A1/D2 不重复立单——是否认可？

---

## 附：审计覆盖声明

- 覆盖：backend/ 全部 12 app + shared/gateway/config/models（约 15k 行非迁移代码）+ 相邻 frontend/tests/engines 引用面 + utils 门禁工具实测。
- 分工：audit-ai（ai_assistant/dashboard）、audit-task（task_list/device_pool/serial_log）、audit-case（case_manager/report_generator/knowledge_search/bug_manager）、audit-infra（accounts/usage_ledger/ops_console/基础设施）；lead 全局扫描 + P0 全部亲验 + R-1/DOC-1/C1 亲验 + F02/F03 亲验。
- 未运行测试/lint/构建（只读审计）；未修改任何代码与规则文档。本报告是审计结论与处置建议，不是已实施的变更。
- 局限：疑似项（第五节）依赖仓外消费方确认；purge_disconnected_devices/success 历史口径依赖存量库查询；行号以审计时点为准，存在并发会话写入（见时效警示）。