## Context

- `_do_start_app` 语义（`executors/ui/executor.py:224-235`）：`pkg = s.xpath if s.xpath else 用例 package_name`——xpath 字段承载"包名或空（回退用例包名）"。
- v6.10 写侧校验（`case_manager/api_ai.py` `_REQUIRED_FIELDS`）把 `adb_start_app`/`adb_kill_app` 与 click/wait 类同等对待强制 xpath 非空——与执行器语义冲突，AI 被迫伪造 `"/"`。
- AI 轮询行为（对话 211 msg 407）：无等待工具 → 密集 `get_run_status` + 自行重跑用例两次。动机与证据见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- `adb_start_app`/`adb_kill_app` 允许空 xpath（回退用例包名），校验与执行器一致。
- 修复 TC-NAV-004 数据后，真实设备执行可达 **pass**。
- AI 拥有 `sleep` 工具与明确的轮询间隔指引，显著降低查询频率。

**Non-Goals:**

- 不改执行器 `_do_start_app` 逻辑（其语义本就支持空 xpath 回退）。
- 不新增分类（sleep 归入既有「测试执行」），不动前端。
- 不做本地执行器 `step_details` 持久化（独立缺口，另开 change）。

## Decisions

**D1：修校验而非修执行器。**
执行器"xpath 可空、回退用例包名"是既定契约（其错误日志文案即如此表述），校验才是偏离方；删两条约束即恢复一致，diff 最小。

**D2：sleep 工具参数封顶 30 秒、read_only=True。**
封顶防滥用（SSE 心跳 2 分钟，30s 阻塞安全）；read_only 使其进入只读兜底集合，无需 HITL、无需逐智能体启用记录（与"只读工具默认可用"口径一致）。

**D3：TC-NAV-004 数据经 `save_ai_definition` 修正（不改库直写）。**
走 AI 写用例入口（含校验），保证修正后的数据与合法写路径完全一致。

## 模块防火墙自检

- 写库收敛：数据修正走 `apps.case_manager.api_ai.save_ai_definition`（api 出口）；无新跨模块 import。✅
- Tool 只调模块 api：sleep 无外部依赖；get_run_status 描述仅为文案。✅
- 前端/通道：无变更。✅

## Risks / Trade-offs

- [sleep 被模型滥用（如重复长睡）] → 30s 封顶 + 描述强调用途（等待异步任务），风险可控。
- [移除 xpath 必填后，包名既不在步骤也不在用例的启动步骤会 fail] → 执行器已有明确 fail 分支与中文报错（"未指定包名"），失败可见而非静默。
- [TC-NAV-004 修改后若设备侧 Govee Home 状态异常（登录弹窗等）仍可能 fail] → 属用例内容问题，非本 change 范围；验证时若出现会在报告中注明。
