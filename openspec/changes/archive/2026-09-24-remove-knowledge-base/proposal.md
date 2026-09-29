## Why

知识库（RAG）在 AI 助手里是一个「界面做完了、但没接进运行时」的功能：设备执行链路的装配不读知识库开关与引用范围，全仓唯一的检索入口没有任何调用者；页面上却写着「开启后 AI 回答问题时自动检索」。它同时带来三个问题：索引只吃 `.md` 而上传支持 5 种后缀（能勾选、检不到）、状态数字是写死的占位值、以及**五个端点零权限校验**（任意登录用户可上传文档、触发同步全量重建索引）。

经确认：该能力不再需要，后续也不迭代，**整体下线**。

## What Changes

- 前端：删除「知识库」侧栏子项、路由与整个页面（页面 / 导入弹窗 / 预览抽屉 / 文档树 / 树构建工具）、对应 API 函数与 DTO、上传与 RAG 提示常量；模型调试页删除知识库展示位与相关文案。
- 后端：删除五个知识库端点与视图、RAG 服务（含 chromadb 向量库适配）、api 层四个知识库包装函数、智能体的「知识库开关」与「引用范围」字段及其全部读写点、模型调试响应里的知识库块、遗留工具网关里的知识库分支。
- **BREAKING**：数据库删除 `ai_agents.enable_knowledge_base` 与 `ai_agents.knowledge_sources` 两列（走迁移）。已确认两列只承载配置值，且知识库落盘目录与向量库当前均不存在（从未导入过文档）→ 无内容损失。
- **BREAKING**：`/api/ai/knowledge/*` 五个端点整体消失（对旧路径返回 404），平台配置读写下发不再含知识库字段。
- 依赖：移除 `chromadb`（已确认仅 RAG 使用）。
- 命名收敛：任务附件解析与知识库共用的 `kb_files.py` 重命名为 `attachments.py`，只保留任务附件解析，避免留下一个与知识库同名却已无知识库能力的模块。
- 非目标（一律不动）：任务附件上传与解析（docx / pdf → Markdown）行为不变；设备提示词、平台工具、Skill、任务链路与其它权限相关代码不变；`data/` 下其它内容不变；`dev_docs` 里的 AgentScope 框架笔记与归档历史不变。

## 关联文档

- PRD-08（AI 助手 · 任务发布与设备操控）
- 说明：知识库能力在需求文档中无独立条目，本次行为契约以 `openspec/specs/knowledge-base-retirement` 为准。
- **本变更不处理的既有规格冲突（登记备裁）**：`ai-model-debug` 的「单角色调试对话」要求写着「该对话 MUST NOT 挂载或调用任何工具，MUST NOT 触发真机操作」，而同一规格的「调试对话按该角色真实装配运行」与后端实现均为「挂载该角色真实工具子集、会真实操作所选设备」。两处相互矛盾，且前端调试页长期因此保留了一句错误提示。该矛盾与知识库无关，不在本单修复。

## Capabilities

### New Capabilities

- `knowledge-base-retirement`: 知识库能力从产品面、HTTP 面、数据面与依赖面整体下线的契约（无入口 / 无端点 / 无字段 / 无实现），并守住「任务附件能力不受影响」。

### Modified Capabilities

- `ai-model-debug`: 归属标注由「技能与知识库」收敛为「仅技能」；三层组织的计数与参考数据去掉知识库；调试对话的挂载说明去掉知识库。
- `ai-assistant/workbench-header-copy`: 入口页范围由「智能体看板 / 工具箱 / 知识库」收敛为「智能体看板 / 工具箱」，删除知识库页头场景。
- `evaluator-retirement`: 侧栏子项由「平台小助手 / AI工具箱 / 知识库」收敛为「平台小助手 / AI工具箱」。
- `frontend-doodle-subpage-nav`: 侧栏子项模版的「AI 助手三子路由」收敛为两子路由。

## Impact

- 前端：`frontend/src/modules/ai-assistant/**`（删除 `KnowledgeBase.vue` 与三个知识库私有组件、`helpers/kb-tree.ts`；同步 `index.vue` / `routes.ts` / `api/toolbox.ts` / `constants.ts` / `composables/usePlatformConfig.ts` / `AgentDetail.vue` / `ModelDebugPage.vue` / `index.logic.ts` / `helpers/toolbox-assembly.ts` / `AGENTS.md`）、`frontend/src/shared/components/sidebarNavConfig.ts`、`frontend/src/shared/types/ai.ts`、`frontend/tests/ai-assistant/**` 相关用例。
- 后端：`apps/ai_assistant/**`（删除 `views_knowledge_drf.py` 与 `rag_service.py`；同步 `urls.py` / `api.py` / `models.py` + 删列迁移 / `serializers.py` / `model_debug.py` / `views_model_debug_drf.py` / `views/tool_gateway.py` / `kb_files.py` 重命名为 `attachments.py`）、`requirements.txt`、`tests/graybox/unit/**`（删 `test_kb_files.py`，更新模型调试与附件用例）。
- 数据：删除两个配置列；**不删除任何文件**（`data/rag_datas` 与 `data/rag_vector` 当前均不存在）。
