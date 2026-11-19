## Context

见 proposal.md 的 Why。代码与现行 AGENTS 已经是「`ae_harness` 出原语，`backend_bridge` 装配」。本设计只处理规格文本怎么改，不改运行时代码。

对照结果：

| 规格 | 仍要求 | 代码现状 |
| --- | --- | --- |
| `agent-harness` | `AgentRoleFactory`、`engines/agents`、短名、`tools_config` | `create_agent` + `tools/<域>/` + `catalog.py` |
| `agent-basic-role-create` | YAML 五段、提示词 token | 三要素：名称、正文、连接参数 |
| `agent-model-catalog` | `models.yaml`、四族短名 | 聊天无表；嵌入只在 `knowledge/config/models.yaml` |
| `backend-bridge-agent` | `UI_EXECUTOR_PROMPT`、模型短名 | 运营库正文 + 显式连接参数 |
| `ae-harness-token-usage` | 用短名创建 | 用连接参数创建；用量口径未变 |
| `agent-sop-workflow` | 从引擎型号文件注入关键词 | 抽象层不读型号目录 |

## Goals / Non-Goals

**Goals:**

- 6 份规格的需求与场景改到能被当前代码满足。
- 删除指向已不存在模块的路径，避免后续实现把它们加回来。

**Non-Goals:**

- 不改 `engines/` 或 `backend/` 的代码。
- 不改 `openspec/changes/archive/`。
- 不处理 H6810 关键词文件、`ui_task.yaml`、知识库资料路径这三处代码残留。
- 不新增能力，不调整用量统计口径。

## Decisions

### 1. 用 REMOVED 而不是改写旧需求

`agent-harness`、`agent-basic-role-create`、`agent-model-catalog` 的多数需求整条依赖已删除的模块。逐条 MODIFIED 会把旧结构留在正文里。改为 REMOVED，再按现在的行为 ADDED。

备选是保留标题只改正文。否决：标题仍写着 `AgentRoleFactory`、`models.yaml`，读规格的人会以为这些入口还在。

### 2. 用量与平台入口用 MODIFIED

`ae-harness-token-usage` 的归组、时间、缓存不重复计入都没变，只改两个创建场景。`backend-bridge-agent` 的报告目录、账本、对话页没变，只改装配与入口参数。这两处用 MODIFIED，保留未改动的需求。

### 3. 关键词目录整条删除

`agent-sop-workflow` 里「验收步骤带型号关键词目录」的来源路径已经不存在，行为也没有等价实现。不改写成「调用方可选注入」，因为那不是当前代码的保证。

### 4. 规格正文不写内部函数名清单

新增需求只写调用方能观察到的契约：传入什么、返回什么、什么情况下失败。`create_agent`、`create_model`、`catalog.py` 作为唯一入口写明，其余实现细节留在 AGENTS。

## 模块防火墙自检

- 不新增跨 App import。本变更只改 `openspec/specs/`。
- 不新增写库路径。
- 不改前端。
- `engines` 继续零 `django` / `apps.*`，本变更不触碰该边界。

## Risks / Trade-offs

- [规格删得多，归档时主规格变短] → REMOVED 带 Reason 与 Migration，归档后仍能看出旧入口为什么消失。
- [代码里还有三处业务残留，规格却说引擎不保存流程] → 已在 Non-Goals 标明。残留不作为本变更的验收项，避免把文档同步扩大成代码搬迁。
- [旧测试仍引用短名或 `OpenAIChatModel`] → 本变更不改测试。若校验只看规格，不受影响；测试失败另立变更。
