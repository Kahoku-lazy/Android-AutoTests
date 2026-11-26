## 1. 运行器出口与共享参数

- [x] 1.1 把图像保留数、工具结果上限、最大推理轮次抽成共享常量（新 `engines/backend_bridge/agents/run_params.py`），`session.open_session` 与 `build_bound_roles` 都引用同一组值；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过，且 `session.py` 里不再有这三个字面量。
- [x] 1.2 给 `engines/ae_harness/workflow/sop/runner.py` 的 `run_sop` 增加 `on_event` / `on_observation` 两个可选回调与 `render_report: bool = True`；默认值下行为与现状完全一致；验证：`goal` / `team` 两条路径不传新参数跑通现有用例，报告仍为四段式。
- [x] 1.3 契约守护：断言 `session`（单角色）与 `bound_roles`（SOP）都走同一组运行参数、`run_sop` 暴露两个出口与渲染开关；两条路径接线一致；验证：`tests/arch/unit` 新增守护通过（按 `tests/AGENTS.md` 口径，这里只做源码一致性断言，行为验证放 `temps/` 脚本）。

## 2. SOP 接线：设备契约与采集口径

- [x] 2.1 `engines/backend_bridge/workflow/bound_sop.py` 在装配角色之前校验设备：空序列号与未连接都拒绝运行，错误文案复用 `session.require_online` 的口径（含平台传入序列号与当前在线清单）；验证：传 `FAKE-SERIAL-123` 时抛错且日志目录里没有新的运行子目录（说明未发起任何模型调用）。
- [x] 2.2 用 `lock_serial` / `unlock_serial` 以 `try/finally` 包住整个 `run_sop`；验证：运行中调用工具层 `resolve_serial("OTHER-DEVICE")` 被拒绝，运行结束后锁已释放（再跑一次同设备成功）。
- [x] 2.3 `engines/backend_bridge/workflow/bound_roles.py` 的观测中间件改为采集全量上下文（`capture_messages=True`），执行者与验收者仍共用同一实例；验证：一次真实 SOP 运行的观测里 `model_call` 记录带 `messages` 字段，且两个角色的记录都能追到各自 `reply_id`。

## 3. 对齐记录与原始事件流

- [x] 3.1 `run_bound_sop` 在 `run_sop` 之前建 `RawEventDump` 与 `AlignedRun`（路径取过程日志的 stem 派生出 `.raw.jsonl` / `.aligned.json` / `.media`），订阅两个出口；验证：一次真实 SOP 运行后目录里同时存在四类文件，`.raw.jsonl` 在运行中即可 tail 到新行。
- [x] 3.2 记录头部补齐角色信息与步骤段：`run.roles`、`input.roles`（每角色系统提示与工具清单）、`steps[]`（名称 / 描述 / 通过 / 尝试次数 / 说明 / 期望 / `reply_ids`）、`replies[].role`；验证：读取生成的 `.aligned.json`，上述键齐全，`steps` 条数与 SOP 步骤数一致。
- [x] 3.3 媒体仍走旁路文件 + URL，事件仍可被官方 schema 重新校验；验证：`python -m temps.verify_aligned_render <aligned.json>` 通过，`events` 段里媒体字段是 URL 而不是 base64。

## 4. 渲染：按步阶段与双角色

- [x] 4.1 `AlignedReportRenderer` 支持步骤段：有 `steps` 时「阶段」页签按「准备卡 → 每步卡 → 收尾卡」渲染，无 `steps` 时保持按轮；验证：`python -m temps.check_tabs <aligned.json>` 全 OK，两份样例（有/无 steps）分别出步骤卡与轮次卡。
- [x] 4.2 每步卡内按角色分成两个块，块头显示角色（执行者 / 验收者）、角色名与模型；验收者块的工具清单只含只读工具；验证：真实 SOP 报告里每步出现两个角色块，验收者块无写操作工具。
- [x] 4.3 概览页新增步骤结论卡：通过/失败步数、失败步的名称与原因；验证：构造一份含失败步的记录渲染后，卡片数字与失败原因与记录一致。
- [x] 4.4 「原始记录」页签把 `steps` 段一起列出；验证：页签内可展开到 `steps` 原文。
- [x] 4.5 无步骤段记录回归：单角色对齐记录渲染结果与本次变更前逐段一致（页签、按轮阶段、用量卡）；验证：对既有 `ui_executor` 记录重渲染，与旧产物对比章节结构一致。

## 5. 测试与验收

- [x] 5.1 `tests/arch/unit` 增加契约守卫：`bound_sop` 必须先校验设备再装配角色、必须持锁、`bound_roles` 必须传 `capture_messages=True`、`run_sop` 必须暴露两个出口与渲染开关；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过。
- [x] 5.2 阶段切分的临时验证脚本放 `temps/`：有 `steps` 走步骤分组、无 `steps` 走轮次分组、步骤事件缺失时不抛错；验证：`python -m temps.check_sop_stages` 三项全 OK（按 `tests/AGENTS.md` 口径，函数级验证不入 `tests/`）。
- [ ] **skipped（2026-11-27 需求方决定：真机验证不做）** 5.3 一次真实 SOP 任务验收（真机 + 已发布 SOP 工作流）：确认报告五页签、阶段为步骤卡、每步两个角色块、步骤结论与平台任务结果里的 `completed` / `failed` 一致；验证：记录任务号与报告路径，逐项打勾。**当前阻塞**：库里唯一的 SOP 工作流 `UI执行`（id=9）仍是 `draft`（平台提交只接受 `published`），且其验收角色用 `openai` provider + `OPENAI_API_KEY`，本机未配置该密钥。已改用「直连 `run_bound_sop` + DB 解析出的两个角色（验收角色临时换成 deepseek 密钥）」跑真机一步 SOP 通过，剩平台提交链路待这段数据/密钥就绪后再验。
- [x] 5.4 单角色回归：跑一次真实 UI 执行任务，报告仍五页签、阶段仍按轮、`aligned.json` 里没有 `steps` 段；验证：报告与既有产物结构一致。
- [x] 5.5 门禁：`python -m run check` 27/29 通过——ruff（平台 + engines）、格式、Django 检查、迁移、OpenAPI、boundary、linting、silent-except、engines 风格全绿；失败的两项是 `vitest` / `vite-build`，原因为本机 `.vite-temp` 写权限 EPERM（环境问题，非代码）。`openspec validate --strict` 通过。既有与本变更无关的失败已在结果里注明：`tests/arch/unit` 5 项（api-docs、auth 403/401、前端调用路径、`engines/agents` 已退役、views 直写 ORM）、`tests/task` 3 项（`Workflow.release_state`）、`tests/ai_assistant` 16 项（401/403）。

## 6. 文档

- [x] 6.1 更新 `.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md`：SOP 对齐记录的增量字段（`steps` / `roles` / `replies[].role`）与阶段切分口径。
- [x] 6.2 更新 `.agents/docs/engines/ae_harness_workflow/ae_harness_workflow_sop_abstraction.md`：`run_sop` 的两个出口与 `render_report` 开关，以及「渲染由调用方决定」的原因。
- [x] 6.3 更新 `.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md`：SOP 设备契约（前置校验 + 全程独占）、运行参数与单角色共用一组常量、四类产物的命名规则。
