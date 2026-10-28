## Context

用例编写角色当前使用空工具包（`build_case_authoring_toolkit()`），只有 GoalPipeline 在运行时额外挂 `save_case_module_document` / `read_case_module_document`。AgentScope 2.0.9 已内置计划模式四件套，且 `is_state_injected=True`，由 `Agent` 把 `AgentState.tasks_context` 注入每次调用；不需要自建任务表。

约束：角色工具必须经 `tools_config.py` 装配；自定义工具放 `tools/tool_*.py`；验收角色保持只读。

## Goals / Non-Goals

**Goals:**

- 编写角色（SOP 与 GoalPipeline 两种装配）拿到四个计划工具。
- 提示词要求先建计划、按阶段更新、交付前检查，避免五阶段漏做。
- 计划工具只在 writer 上，不泄露给 verifier / planner。
- 轮次预算足够覆盖计划创建与状态更新。

**Non-Goals:**

- 不把计划清单写入数据库、任务事件或报告；计划状态随角色实例存在。
- 不做计划模式的前端开关或 Agent 配置项；本轮固定开启。
- 不改变验收标准、用例字段、模块切分与截断策略。
- 不改 AgentScope 版本或引入新的依赖。

## Decisions

### 1. 使用 AgentScope 内置计划工具，不自建

四个工具直接实例化：

```python
TaskCreate()
TaskGet()
TaskList()
TaskUpdate()
```

理由：工具直接读写 `AgentState.tasks_context`，与 `Agent` 生命周期一致；自建工具需要复制任务模型、状态注入与权限逻辑。

备选：平台自建 `plan_case_writing` 工具写数据库。会把过程状态变成业务数据，且要处理清理与并发，本轮不需要。

### 2. 只给 writer，不给 planner / verifier

`tools_config.py` 增加 `build_case_writer_toolkit()`，`build_case_authoring_toolkit()` 保持空包给规划/验收。`case_roles._role_config` 增加 `plan_mode` 开关，`build_case_writer` 与 `build_case_writer_goal` 传 `True`。

理由：计划是写作者的过程管理；验收角色若也能改计划，会污染“只判卷”的职责边界。

### 3. 工具实现放在 `tools/tool_case_plan.py`

模块只负责构造四个内置工具，便于单测与后续替换；`tools_config` 只做装配，不直接 import AgentScope 的 Task 工具。

### 4. 提示词要求“先计划、后写作、交付前清账”

在五阶段工作流之前增加「计划模式」章节：

- 开始拆需求前先 `TaskCreate` 建 4~5 个阶段任务；
- 每进入阶段 `TaskUpdate -> in_progress`，完成 `-> completed`；
- 交付前 `TaskList` 检查，若有未完成项先补完；
- 计划不是交付物，七节文档仍必须完整保存/提交。

### 5. 轮次预算从 8 提到 20

计划创建/更新本身要占工具轮次。按 5 个阶段各 1 次创建 + 1 次完成更新，加一次列表检查约 11 轮，再留保存、结构化输出与推理余量，20 轮足够；不设更高避免失控循环。

### 6. 计划随角色实例重置

GoalPipeline 每轮新建 writer，因此驳回重写时计划重新开始；这是可接受的：新一轮的输入已带上一版文档与驳回意见，计划应针对新一轮重排。SOP 同理每次尝试新实例。

## 模块防火墙自检

- `tools/tool_case_plan.py` 只 import `agentscope.tool` 的内置工具，不依赖 App、数据库或引擎其他模块。
- `tools_config.py` 是唯一装配点；`case_roles.py` 只选择装配函数。
- 不新增跨 App 依赖，不写库，不改接口。
- 前端无改动。

## Risks / Trade-offs

- [计划工具占用轮次/Token] → 轮次提到 20；提示词限制“只建 4~5 个阶段任务”，不要求为每条用例建任务。
- [模型只建计划不写文档] → 提示词明确“计划不是交付”，验收仍按七节文档判卷；GoalPipeline 仍要求 `save_case_module_document`。
- [模型反复更新状态形成循环] → 提示词只要求阶段级更新；`max_iters=20` 兜底。
- [计划状态在驳回后丢失] → 可接受；新一轮计划按新输入重建，避免沿用过期进度。
- [AgentScope 版本差异] → 2.0.9 已提供同名工具；若升级到 2.0.11，API 不变。

## Migration Plan

1. 部署引擎代码；无需数据库迁移。
2. 新建的 Agent-02 任务自动带计划工具；历史任务重跑也走新配置。
3. 回滚：移除 `plan_mode=True` 与提示词章节即可，工具包为空，无数据残留。

## Open Questions

无。
