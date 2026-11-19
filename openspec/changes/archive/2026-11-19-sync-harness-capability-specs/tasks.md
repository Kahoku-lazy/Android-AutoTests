## 1. 规格同步

- [x] 1.1 将 `agent-harness` 的 delta 合入 `openspec/specs/agent-harness/spec.md`：删除 10 条旧需求，写入 6 条新需求。验证：`openspec validate --change sync-harness-capability-specs` 通过，且主规格不再出现 `AgentRoleFactory`、`engines/agents`、`tools_config`
- [x] 1.2 将 `agent-basic-role-create` 的 delta 合入主规格：删除 8 条旧需求，写入 3 条新需求。验证：主规格不再出现 `role_sys_prompts`、`UI_EXECUTOR_PROMPT`、`AgentRoleFactory`
- [x] 1.3 将 `agent-model-catalog` 的 delta 合入主规格：删除 9 条旧需求，写入 3 条新需求。验证：主规格不再要求 `engines/agents/config/data/models.yaml` 或四族短名加载
- [x] 1.4 将 `backend-bridge-agent` 的 3 条 MODIFIED 合入主规格，保留未改动的需求。验证：主规格的装配需求要求提示词正文与连接参数，不再要求模型短名
- [x] 1.5 将 `ae-harness-token-usage` 的 2 条 MODIFIED 合入主规格。验证：创建场景使用连接参数；归组、时间、缓存口径的原文保持不变
- [x] 1.6 将 `agent-sop-workflow` 的 REMOVED 合入主规格。验证：主规格不再要求从 `engines/agents/config/data/log_keywords/` 注入验收关键词

## 2. 校验

- [x] 2.1 归档前复查 6 份主规格与当前代码一致：`create_agent` 只收正文和连接参数，工具在 `ae_harness/tools/<域>/`，SOP 步骤由调用方提供。验证：`openspec validate --change sync-harness-capability-specs --strict` 通过
- [x] 2.2 确认本次 diff 不含 `engines/`、`backend/`、`frontend/` 与 `openspec/changes/archive/`。验证：`git diff --name-only` 只含 `openspec/specs/` 与本变更目录
