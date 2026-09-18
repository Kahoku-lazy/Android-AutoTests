## Why

平台 AI 助手（智能体 04，对话 211）在用户要求"编写 Android 用例"时只能输出 JSON 用例文本，并明确表示"当前环境中我没有可用的'创建用例'工具"。而平台代码中 `save_case` 写工具早已存在（PRD-08 v6.10）。根因是**编辑智能体时勾选的"平台业务工具"模块从不落库**：前端编辑模式保存时删除 `payload.tools`（注释声称"经独立 API 管理"，但该 API 并不存在），后端在无任何 AITool(platform) 记录时按安全兜底只注入只读工具，`save_case` 等写工具因此从未注入。

## What Changes

1. **后端**：`AgentInputSerializer` 新增 `platform_tools` 字段（字符串数组，可空）；`api.update_agent` 接入新函数 `sync_platform_tools`——仅同步 `tool_type='platform'` 记录（删除未勾选、补齐新勾选、确保启用），MCP/Skill 副本不受影响。
2. **前端**：`AgentDetail.vue` 编辑模式保存时把勾选结果 `selectedPlatformTools` 写入 `payload.platform_tools`，兑现注释中承诺的"独立 API 管理"。
3. **数据回填**：执行仓库自带命令 `python manage.py migrate_platform_tools`，为 active 且缺平台工具记录的智能体补全 26 个工具（enabled=True）——智能体 04 立即获得 `save_case` 等写工具（写工具执行仍受 HITL 确认保护）。
4. **验证数据**：经 `save_case` 路径创建真实用例 **TC-NAV-004** 并保留，归档到目录「测试【平台用例功能】用例」（id=1）。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.5（F-01-05 能力开关）、§4.1（`save_case` 工具）、§5.2（智能体详情 `tools[]`）
- `dev_docs/02-PRD需求/PRD-05-用例管理.md` §2.2/§5（用例结构与写入口径）
- `apps/ai_assistant/AGENTS.md`（写库走 api、无尾斜杠路由约定）
- 现场证据：`ai_messages` 对话 211（msg 395）、`ai_agents` #10（biz=True 且 0 条 `ai_tools` 平台记录）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯 Bug 修复：恢复到 PRD-08 F-01-05 已定义行为（平台工具勾选生效），无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`apps/ai_assistant/serializers.py`、`apps/ai_assistant/api.py`（新增 1 个契约字段 + 1 个同步函数，约 +45 行）
- 前端：`frontend/src/modules/ai-assistant/AgentDetail.vue`（约 4 行）
- 数据：`ai_tools` 表回填（migrate_platform_tools）；`cm_test_definitions` 新增 TC-NAV-004
- 测试范围：`manage.py check` + `ruff check` + `gen_arch_stats.py --check-boundaries` + 前端 `npm run build` + 端到端用例写入验证
