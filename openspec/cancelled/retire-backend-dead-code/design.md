# Design: retire-backend-dead-code

## Context

动机与完整清单见 proposal.md；逐项证据（全仓交叉搜索）见审计报告第四节 D-1~D-43。约束：本变更只做「确认死代码的纯删除 + 消费测试同删/改 + 受影响 docstring/__all__ 同步」，零计费口径变化、零表结构迁移、零 AGENTS 红线改动。

## Goals / Non-Goals

**Goals**
- 删除后全仓无悬空引用：import、`__all__`、字符串路由、测试、docstring 清单全部同步。
- 每个删除项在动手前复核一次引用（审计时点距今可能有并发提交），复核命中生产消费者即停手并上报，不静默扩删。

**Non-Goals**
- 不删任何模型/表/字段（TaskEvent、TaskMedia、TaskUsageHourly、AssistantEvalRun、BugTicket.agent_id、ModelUsage.metadata、attachment_filename 全部保留）。
- 不动 device_pool api 白名单与写路径（变更④）、计价双轨与 cache_creation（变更⑥）、AGENTS/ARCH/PRD 红线文档（变更⑤）。
- 不处置疑似项（observe 链、upload-file、devices/current、ops 三端点、purge_disconnected_devices、RETIRED_AUTH_PATHS、success 历史口径、usage_summary 本体）。

## Decisions

### D1 删除顺序：基础设施 → 各 app → 前端 → 测试收口
先删被依赖最少的（空壳包、死常量），再删 app 内死函数，最后前端与测试。每步跑 `python run.py check` 快速反馈。理由：避免中途出现跨文件悬空 import 的长窗口。

### D2 枚举删除与门禁联动在同一提交
constants.py 删 7 枚举 + ALL_STATUS_ENUMS + 2 死值，与 test_ssot_enum_strenum.py 的 MIN_DISCOVERED_ENUMS 下调（14→7，注释同步）必须同一提交，保证任一提交点上 `pytest tests/arch/unit` 可过。备选：分两提交——中间态门禁必红，弃。

### D3 「测试续命」项的测试处置口径
- 绕路由直传 kwarg 的用例（ThreadLog report_id）：改打真实 URL 或改测 LogFileView，保留其有效断言。
- 断言空桩的用例（agents==[]、by_role 空）：随字段删除而删除断言/用例。
- 仅消费死函数的用例（test_eval_rulers、record_eval 段、voice 段、write_stop_timeout_ids 段）：整段/整文件删除。
- SimpleNamespace 伪造 agent_id 的 bug 用例：去掉伪造字段，断言改按真实 Task 形状。
原则：删测试不是降覆盖——被删行为已不存在；有效断言迁移到活路径。

### D4 agent_id 参数链整体移除
`run_task_async(task_id, agent_id)` → `run_task_async(task_id)`；三个派发点（api.py:495,522,684）同步；TaskUsageHourly 写入侧的 agent_id 槽位恒 0 属**保留字段**（表不动），只删 task_runner 内无意义的透传。备选：保留参数恒 0——残迹继续误导，弃。

### D5 前端删除与文档批的时序
frontend ai-assistant/AGENTS.md 红线声称 agents.ts 被 task-list 引用（审计证实失实）。该红线的修订属变更⑤（已批准）；本变更删除 agents.ts 的任务前置检查「⑤ 的对应修订已合并」。若⑤未合并，本项跳过并上报，不先删后报。

### D6 settings 删除与 .env 核对
删 14 项前 grep `.env.example` 与 run.py/vite.config.js 的 env 读取：SERVER_PORT 的 **env 变量本身存活**（run.py 直读），只删 settings 死项，不动 env 契约。test_eval_runner 的 `settings.LOG_DIR = tmp_path` 无效 override 改为 monkeypatch 真实消费路径或删除。

## Risks / Trade-offs

- [审计后并发提交可能复活引用] → 每项删除前即时复核 grep；命中即停手上报（D1 原则）。
- [删除面大，review 困难] → 按 app 分提交（Conventional Commits，chore/refactor 逐域），每提交自含测试同步，PR 内按提交审。
- [枚举门禁下调被误读为放松质量] → 门禁注释写明「常量清单收敛后同步下限」，删除项逐一列在提交信息。
- [前端死 UI 删除牵连样式门禁] → 删后跑 `node tests/check-style-gates.mjs` 与 vitest、vue-tsc 全量核对。

## Migration Plan

无数据迁移。部署即生效；回退 = 还原对应提交（纯删除，无状态残留）。历史 voice/事件数据保留在表中不受影响。

## Open Questions

无。所有需裁决项已明确排除（见 Non-Goals 与 proposal Impact），不影响本变更的规格与任务拆分。