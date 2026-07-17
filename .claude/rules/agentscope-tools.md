# AgentScope Tools — Android-AutoTests

> **规则**：开发新的 AgentScope 功能前，必须先阅读 [AgentScope 2.0.3 开发者文档](https://docs.agentscope.io/versions/2.0.3/zh)，理解 API 使用方法后再设计执行方案。建议从 [Message & Event](https://docs.agentscope.io/versions/2.0.3/zh/building-blocks/message-and-event.md) 开始。
>
> **文档地址**：https://docs.agentscope.io/versions/2.0.3/zh

## 项目已使用的 AgentScope 功能

| 模块 | API | 用途 |
|------|-----|------|
| **应用框架** | `create_app()` `RedisStorage` `RedisMessageBus` `LocalWorkspaceManager` | FastAPI 应用工厂 + Redis 会话存储/消息总线 + 本地工作区 |
| **Agent** | `Agent(name, system_prompt, model, toolkit)` + `reply_stream()` | 构建对话 Agent，通过 SSE 事件流返回响应 |
| **模型** | `DashScopeChatModel` `OpenAIChatModel` | 阿里百炼 / OpenAI / Anthropic / 自定义兼容提供商 |
| **凭证** | `DashScopeCredential` `OpenAICredential` | API Key 管理，加密存储于 Django DB |
| **Tool 基类** | `ToolBase` `ToolChunk` | 所有 22 个业务 Tool 继承 `ToolBase`，流式输出用 `ToolChunk` |
| **Plan 工具** | `TaskCreate` `TaskGet` `TaskList` `TaskUpdate` | AgentScope 内置子任务追踪，基于 `agent.state.tasks_context` 跨 ReAct 轮次保持 |
| **消息** | `TextBlock` `HintBlock` | Tool 返回值中构造结构化文本/提示消息 |
| **权限** | `PermissionDecision` `PermissionBehavior` `PermissionContext` | Tool 执行前后的权限决策（允许/拒绝/需确认） |
| **Agent Team** | `SubAgentTemplate` | 5 个角色模板（element-inspector / case-writer / device-operator / test-executor / report-writer） |
| **鉴权** | `dependency_overrides[get_current_user_id]` | 用项目 JWT 验证替换 AgentScope 默认 X-User-ID |
| **知识库** | ChromaDB（自建，非 AgentScope 内置） | 32 篇文档的向量检索 RAG，通过自定义 Tool 接入 |

> **核心模式**：项目通过 `extra_agent_tools=build_business_tools` 将 Django ORM 操作封装为 AgentScope Tool，LLM 通过 Function Calling 自动选择工具。Agent 本身不直接访问数据库，所有平台操作必经 Tool 层。

## 自定义 Tool 清单 (25 个：21 业务 + 4 Plan)

### 业务 Tool (21 个)

| Tool | 模块 | 只读 | 说明 |
|------|------|:--:|------|
| `get_test_points` | element-locator | ✅ | 获取测试点元素 |
| `search_elements` | element-locator | ✅ | 搜索 UI 元素 |
| `fetch_page_elements` | element-locator | ✅ | 按页面批量拉取元素列表 |
| `save_test_case` | case-manager | ❌ | 创建/更新用例 (含 14 种步骤) |
| `get_test_case` | case-manager | ✅ | 获取用例详情 |
| `list_test_cases` | case-manager | ✅ | 列出已启用用例 |
| `debug_test_case` | case-manager | ❌ | 单用例调试执行 |
| `create_test_sop` | case-manager | ❌ | 创建 SOP 上下文，推进到阶段 2 |
| `update_test_sop` | case-manager | ❌ | 更新 SOP 状态/产出，推进阶段 |
| `create_runner_task` | test-runner | ❌ | 创建执行任务卡片 |
| `list_ai_tasks` | test-runner | ✅ | 列出 AI 创建的任务 |
| `update_ai_task` | test-runner | ❌ | 更新任务卡片 |
| `get_online_devices` | device-pool | ✅ | 在线设备列表 |
| `acquire_device` | device-pool | ❌ | 锁定设备 |
| `release_device` | device-pool | ❌ | 释放设备 |
| `run_test` | test-runner | ❌ | 执行测试 (支持循环) |
| `get_run_results` | test-runner | ✅ | 查询执行结果 |
| `stop_run` | test-runner | ❌ | 停止执行 |
| `save_report` | report-generator | ❌ | 保存报告 |
| `list_reports` | report-generator | ✅ | 列出报告 |
| `search_knowledge_base` | ChromaDB | ✅ | 知识库向量检索 |

### AgentScope 内置 Plan Tool (4 个)

| Tool | 说明 |
|------|------|
| `TaskCreate` | 创建子任务，支持依赖关系 (blocks/blockedBy) |
| `TaskGet` | 获取单个子任务详情 |
| `TaskList` | 列出当前所有子任务及状态 |
| `TaskUpdate` | 更新子任务状态 (pending→in_progress→completed) |

> Plan Tool 基于 `agent.state.tasks_context` 内存态存储，跨 ReAct 推理轮次自动保持。<br>
> 业务 Tool 在 `agentscope_service/tools/`，直接调用 Django ORM/API（同进程，不走 HTTP）。

## 新增 Tool 流程

在 `agentscope_service/tools/{domain}_tools.py` 新增 ToolBase 子类 → 在 `factory.py` 注册。

## 文件结构

```
agentscope_service/tools/
├── element_tools.py   # get_test_points, search_elements, fetch_page_elements
├── case_tools.py      # save_test_case, get_test_case, list_test_cases, debug_test_case
├── task_tools.py      # create_test_sop, update_test_sop, create_runner_task, list_ai_tasks, update_ai_task
├── device_tools.py    # get_online_devices, acquire_device, release_device
├── runner_tools.py    # run_test, get_run_results, stop_run
├── report_tools.py    # save_report, list_reports
├── rag_tool.py        # search_knowledge_base
└── factory.py         # 工具注册工厂 (build_business_tools)
```
