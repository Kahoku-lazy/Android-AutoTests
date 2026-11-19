## Why

`ae_harness` 已经只提供能力原语：调用方传入提示词正文与连接参数，角色、工具勾选和流程都在 `backend_bridge` 装配。6 份现行规格仍要求 `engines/agents/`、模型短名、提示词文件和 `AgentRoleFactory`，照着做会把已退役的入口加回来。

## What Changes

- **BREAKING** 删除「模型短名」创建方式。`create_model` / `create_agent` 只收调用方传入的 `provider`、`api_key_env`、`model_name`、`base_url`。
- **BREAKING** 删除引擎内的角色提示词文件与 token 解析。系统提示词由调用方传入正文。
- **BREAKING** 角色装配只经 `ae_harness.agents.create_agent`，落在 `backend_bridge`。`AgentRoleFactory`、`build_*`、`tools_config`、`role_sys_prompts` 不再是入口。
- 工具落点改为 `ae_harness/tools/<域>/`，目录由 `catalog.py` 列出；验收侧只取勾选与只读目录的交集。
- 平台 SOP 的步骤由调用方提供，不从引擎内置 YAML 取；验收日志关键词不再从引擎内的型号文件注入。
- 用量记录的口径不变：仍按密钥环境变量名归组，只改创建方式的场景描述。

## 关联文档

无关联 PRD。本变更只把现行规格对齐已经落地的代码，不新增产品能力。现行说明见 `engines/ae_harness/AGENTS.md`、`engines/backend_bridge/AGENTS.md` 与 `dev_docs/ARCH_PRD/ARCH-Engines架构.md`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-harness`: 装配入口、提示词来源、模型装载、工具分配从 `engines/agents` 改为 `ae_harness` 原语加 `backend_bridge` 装配。
- `agent-basic-role-create`: 删除 YAML 五段、`AgentRoleFactory`、`tools_config` 与提示词 token 解析。
- `agent-model-catalog`: 删除 `models.yaml` 唯一数据源与四族短名加载；连接参数由调用方传入。
- `backend-bridge-agent`: 角色不再装载 `UI_EXECUTOR_PROMPT`，入口不再收模型短名。
- `ae-harness-token-usage`: 创建场景从模型短名改为显式连接参数；用量口径不变。
- `agent-sop-workflow`: 删除按型号从引擎文件注入验收关键词目录。

## Impact

- 只改 `openspec/specs/` 下上述 6 份规格。不改代码、不改 API、不改前端。
- 受影响的实现落点（本次不改，只作为规格对照）：`engines/ae_harness/agents/`、`engines/ae_harness/tools/`、`engines/ae_harness/workflow/sop/`、`engines/backend_bridge/workflow/`。
- 归档目录 `openspec/changes/archive/` 保持原样。
