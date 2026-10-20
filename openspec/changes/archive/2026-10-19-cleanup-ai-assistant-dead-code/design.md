## Context

`apps/ai_assistant` 已完成从「规划工作流引擎」到「平台 SOP」的切换，但旧链路的读接口、异常类与适配别名仍留在代码里。判定依据不是人工目测：用 AST 统计 `apps/ai_assistant` 每个顶层符号在 `apps/ engines/ gateway/ shared/ utils/ tests/ tools/ config/` 中的真实引用次数（`Name`/`Attribute` 用法，天然排除 `__all__` 字符串与定义本身），再对候选逐个 grep 复核。

结论：11 个符号/片段仓内零引用；`persist_task_progress_safe` → `patch_task_progress` 构成一条只在单测里活着的调用链。路由、序列化器、响应形状均不受影响。

## Goals / Non-Goals

**Goals:**

- 删除仓内零引用的符号与死片段，让 `api.__all__` 重新等于真实跨模块契约。
- 删除生产零调用的进度写库链，避免「看起来在写过程记录、实际没人调用」的假象。
- 保持 `python manage.py check`、`ruff check`、`ruff format --check` 全绿。

**Non-Goals:**

- 不修 P0/P1 功能缺口（过程记录、token 费用、Skill 目录）。
- 不删 `AIExecutionLog` 表（删表要迁移，另行立项）。
- 不动 `/api/ai/tools/*` 内部令牌网关（有鉴权单测与接口文档，属既有对外通道）。
- 不动会话/聊天整栈与僵尸端点（改 API 面，另行立项）。
- 不改前端。

## Decisions

**D1 只删「仓内零引用」，不按主观判断删「看起来没用」。**
备选：按功能模块整块删（如整个会话子系统）。否决理由：会话仍被 `AIConversation/AIMessage` 表与序列化器承载，删它属能力下架，需要产品决策与迁移，不是清理。

**D2 进度写库链整体删除（含测试）。**
`persist_task_progress_safe`（[task_runner.py](apps/ai_assistant/task_runner.py)）、`patch_task_progress`（[api.py](apps/ai_assistant/api.py)）、`views_drf` 的 `noqa: F401` 再导出一次删净，`test_task_progress_persist.py` 同步删除。备选：保留待 P0 复用。否决理由：保留即留下「无人调用但被测试守护」的代码，正是本单要消除的形态；P0 修复应在新契约下重写，不背旧实现。`api.dump_task_run_payload` 仍被 `task_runner` 终态写库使用，保留。

**D3 `log_confirm_result` 删除后，`AIExecutionLog` 只保留表与 admin 只读入口。**
删表需要迁移与数据处置决策；本单只删写入方，避免把「清理」扩大成「数据删除」。

**D4 参数标签只删「已无对应工具」的条目。**
`PARAM_LABELS` 是跨工具共享表，保留仍可能被未来工具复用的键会制造死数据；按当前 `TOOLS` 实际入参集合收窄。

## 模块防火墙自检

- 跨 App import：本单无新增；删除项均在 `apps/ai_assistant` 内部。
- 禁止跨 App import service/runner：未触碰。
- 写库收敛：未改任何写路径；删掉的是无人调用的写函数，实际写库仍全部经 `api.py`。
- 前端不直连数据库、仪表盘不写：未触碰。
- 外部依赖：无新增；`requests`、`Fernet` 等用法不变。

## Risks / Trade-offs

- [删 `api.__all__` 条目可能影响仓外调用方] → 仓内全量 grep 为零引用；`dashboard`、`report_generator`、`tools/register_agentscope_agents.py` 实际依赖的 `filter_agents_for_user`、`task_deepseek_cost`、`resolve_assistant_name`、`decrypt_key` 全部保留，并跑一次 import 冒烟确认。
- [删 `persist_task_progress_safe` 会让既有单测失败] → 同单删除该测试文件，属预期；其余 AI 单测回归通过。
- [进度链删除后 P0 修复需重写] → 已在 proposal 明确「另行立项」，届时按新 SOP 契约实现回调。
- [死片段误删导致运行期行为变化] → 删除项均为不可达分支（`pass` 空块、重复 import、未 raise 的异常类、未调用的函数），不存在运行期路径。

## Migration Plan

无数据迁移、无部署顺序要求。回滚方式：`git revert` 本单提交即可恢复全部符号。

## Open Questions

无。
