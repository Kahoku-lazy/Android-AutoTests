## Context

- 现实现：`apps/ai_assistant/tools.py::list_page_flows(query, directory_id, limit=20)` → `apps/workflow/api.py` re-export 的 `api_digest.list_document_summaries(...)`，后者按 `doc_type__in=SUPPORTED_TYPES` 取数、`order_by("-updated_at")[:limit]` 截断，每行给 `{doc_id,title,prototype_id,prototype_name,directory_id,directory_name,node_count,link_count,updated_at}`——**只有当前目录名，没有祖先链**。
- 出口归属：`api_digest.py` 自述「AI 列表工具数据出口」，`__all__` 导出并经 `workflow/api.py` 转发；全仓**唯一消费方**就是 `tools.py::list_page_flows`（已 grep 核）。
- 文档类型：`WorkflowDocument.SUPPORTED_TYPES == {TYPE_PAGE_FLOW}`（`"page_flow"`，中文名「页面流」），因此「全部页面流文档」= 全部受支持文档；文档可 `directory_id=None`（未归类）。
- 目录模型：`WorkflowDirectory.parent_id`（`serialize_directory` 已含 `parent_id`）；`get_directory_tree()` 能给出嵌套树。
- 真实数据（本机库）：2 篇文档（1 篇未归类 + 1 篇在根级「默认目录」）、2 个目录、最大深度 1、2 个原型。
- 角色装配：`DEVICE_PLANNER_TOOLS = []`、`VISION_TOOLS` 不含 `list_page_flows`/`get_page_flow` → 本变更**不落在任何 Agent 角色的工具子集里**，故无提示词需要同步。
- 动机见 proposal.md - Why；条款见 specs/ai-page-flow-listing。

## Goals / Non-Goals

**Goals:**

- 一次调用拿到**全部**页面流文档，不再被 20 条截断。
- 每条文档带完整目录路径与深度，未归类文档有明确表示且不被丢弃。
- 层级拼接只有一份实现，且不产生 N+1 查询。

**Non-Goals:**

- 不改 `get_page_flow`（按 doc_id 取语义摘要）。
- 不返回「目录树」型结构（用户已在 A/B/C 中选择「文档列表为主 + 每条带路径」）。
- 不改该工具的分类归属（仍属「页面流工具」）、不改 `TOOL_META` 的 module/action。
- 不新增分页/游标（真实规模个位数；见 Open Questions）。

## Decisions

**D1 扩展既有 AI 出口 `api_digest.list_document_summaries`，不新建函数。** 它已被文档标注为「AI 列表工具数据出口」且只有这一个消费方；新建 `list_document_tree` 之类会造成两个近义出口。备选：新建独立函数 → 否决（两份真相源）。

**D2 一次构链，避免 N+1。** 先一次取出全部目录建 `id → (name, parent_id)`，再对每个目录做记忆化解析得到 `(path, depth)`；带**环保护与深度上限**，异常数据不会导致无限递归。文档侧按 `directory_id` 查表，未归类走固定值。

**D3 工具签名收敛为 `list_page_flows(query="")`，返回 `{"total": N, "documents": [...]}`。** 去掉 `limit`（它就是要消除的截断）与 `directory_id`（每条已带路径，按目录收窄可由模型自行判断）；`query` 保留，因为全量输出在文档变多时需要收窄手段。返回体由裸数组改为对象，是为了把「一共几篇」显式给模型（它能据此判断是否还需要收窄）。

**D4 workflow 出口保留 `query` / `directory_id` / `prototype_id`，`limit` 默认改为 `None`（不限）。** 它是通用的 AI 数据出口，参数面不必跟着工具收敛；默认不限量保证「不传即全量」，显式传 `limit` 仍可截断。

**D5 未归类文档的表示：`directory_id: null`、`directory_path: ""`、`directory_depth: 0`。** 三者同时给出，避免模型把「路径为空」误读成「错误」；深度 0 与根目录文档的深度 1 形成清晰区分。

## 模块防火墙自检

- **跨 App import**：`ai_assistant` 仍只经 `apps.workflow.api`（其中 re-export `api_digest` 的函数）只读取数，未新增对 `workflow.models` / `serializers` / `views` 的 import；路径拼接实现在 `workflow` 自己的模块内。
- **写操作收敛**：本变更纯读，无 INSERT/UPDATE/DELETE。
- **前端 HTTP 出口**：不涉及（前端不经此工具取数）。
- **数据库**：无 schema 变更、无迁移。
- **内部网关**：不涉及。

## Risks / Trade-offs

- [全量输出在文档变多时撑大上下文] → 当前真实规模 2 篇；`query` 提供收窄；过千篇时需再评估分页（Open Question）。
- [目录链成环导致拼接死循环] → 记忆化 + 深度上限 + 环检测，异常时降级为该目录自身的名字而不是抛错。
- [未归类文档被漏列或误表示] → 明确 null/""/0 三元表示，并有专门用例。
- [改了 AI 出口形状影响其它调用方] → 已核全仓唯一消费方；`API-工作流.md` 的「非 HTTP 数据出口」小节同步说明新字段。
- [去掉 `limit`/`directory_id` 属契约缩窄] → 该工具不在任何角色子集内（无提示词依赖），且调试页按 schema 数据驱动会自动反映新参数。

## Migration Plan

- 纯代码改动，无数据库迁移。两处文件（workflow 出口、工具层）同版本发布。
- 回滚：回退这两处即可；旧调用方（若外部有）传 `limit` 仍被接受。

## Open Questions

- 文档规模达到数百/上千时，是否需要分页参数或「按目录收窄」的二次入口？本单按当前规模（个位数）不做。
- 是否最终需要「目录树」型返回（带空目录）？本单按用户选择只给「文档列表 + 路径」。
