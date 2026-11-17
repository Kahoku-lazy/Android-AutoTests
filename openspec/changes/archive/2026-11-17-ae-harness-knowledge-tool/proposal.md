## Why

`engines/ae_harness/` 现在只有 adb 工具：模型看得到屏幕，却查不到资料。产品资料（按键含义、指示灯、固件与恢复出厂说明）只能由人贴进提示词，既占上下文也无法随资料更新。AgentScope 2.0.9 已提供 `KnowledgeBase` 句柄与向量库基类，向量能力不需要自研。

需要把「检索」做成 Harness 内的**独立模块**：自带配置、自带索引、只在 agent 调用时才工作；整目录删除后，adb 工具、角色创建、事件与 SOP 一律不受影响。

## What Changes

- 新增根级模块 `engines/ae_harness/knowledge/`：自带两份 yaml（只放向量模型的 `models.yaml`、库目录 `knowledge_bases.yaml`）、SQLite 向量库、增量索引、检索服务，以及一个 `search_knowledge` 工具实现。
- 新增 `build_knowledge_tools()`，形态与 `build_adb_tools()` 一致：返回 `FunctionTool` 列表，由调用方挂载。
- 执行者入口挂载该工具，且用**局部可选导入**：整目录删除后入口自动跳过，不抛异常。
- 收紧 `tools/` 目录准入：只允许 Python 内置函数工具、Skill、MCP 三类；知识库不属于这三类，因此放根级 `knowledge/` 而不是 `tools/`。
- 修改红线：`ae_harness/AGENTS.md`（第 11 条、目录结构与职责表）、`ae_harness/agents/AGENTS.md`（第 3、6 条）、`ae_harness/tools/AGENTS.md`（目录准入）。
- **不改** `agents/models.py`、`agents/config/`、`requirements.txt`。

## 关联文档

- 设计与红线变更见本变更 `design.md`。
- 同主题的历史规格 `openspec/specs/knowledge-index-and-retrieve`（`engines/agents/rag`）**不复用其实现**，本变更在 Harness 内独立实现。

## Capabilities

### New Capabilities

- `harness-knowledge`: 独立知识库模块——自带配置、按库增量索引、只读检索工具、可整目录删除

### Modified Capabilities

无。

## Impact

- 引擎：新增 `engines/ae_harness/knowledge/`；修改 `engines/ae_harness/assistant/agent_executor.py`；`.gitignore` 增加索引目录。
- 文档：`engines/ae_harness/AGENTS.md`、`engines/ae_harness/agents/AGENTS.md`、`engines/ae_harness/tools/AGENTS.md`、新增 `knowledge/AGENTS.md`。
- 测试：新增 `tests/engines/ae_harness/unit/` 下知识库用例。
- 不新增后端接口、不改前端、不动 `engines/agents/rag`。
