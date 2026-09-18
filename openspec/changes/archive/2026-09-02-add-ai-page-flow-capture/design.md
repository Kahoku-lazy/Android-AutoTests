## Context

- 已具备：`device_action` 控制手机、`capture_page`/`analyze_page` 抓屏与结构分区；`element_locator.api.import_snapshot_page` 已能 upsert 页面/元素（但 alias 写死回退 text/resource_id）；`element_locator.api.create_flow` 已能建 `el_page_flows`（但无去重）；`workflow.api.upsert_document` 已能写 `wf_documents`（但「AI 无写图工具」）。
- 前端 `workflow` 的 `config_json` 节点结构（`frontend/src/modules/workflow/types/workflow.ts` + `stores/workflowStore.ts`）与 `workflow/semantics.py` 的解析口径已固定：`StartNode(start_kind=app, package_name)`、`PageNode(properties.linked_page_id/linked_page_name/linked_elements, outputs 端口带 el {id,label,type,xpath} type=navigation)`、`links(type=navigation)`。
- 约束：AI 工具只 import 各模块 `api.py`；写库走 api；`workflow` 素材只读引用 `el_` 表。

## Goals / Non-Goals

**Goals:**

- 元素别名持久化 + 跳转关系幂等建边 + 受控生成工作流页面流文档。
- AI 工具 `create_page_flow`（写 `el_page_flows`）与 `save_page_flow`（写 `wf_documents`）。

**Non-Goals:**

- 不做「AI 全自动爬完整 App」的多层 BFS/DFS 编排（本轮只提供原子能力 + 生成器，爬取深度由 AI ReAct 自己控制）。
- 不改前端 VueFlow 画布/节点注册（生成的 config_json 直接兼容现有画布）。
- 不改 `workflow.semantics.py`（只消费其解析口径）。

## Decisions

**D1：别名在 `import_snapshot_page` 层支持「显式 alias 优先，回退 text/resource_id」。**
`device_inspector.save_snapshot_to_elements` 透传 `aliases`（`{resource_id: alias}`），`import_snapshot_page` 读 `e["alias"]`。备选：在 ai_assistant 层拼 alias —— 被否（跨模块写收敛在 element_locator.api，别名字段归属 el_elements）。

**D2：`get_or_create_flow` 按 `(from_page_id, to_page_id, trigger_element_id)` 去重，幂等复用。**
`trigger_action` 默认 click，去重不含 action（同一条边动作变体视为同一关系）。备选：复用 `create_flow` 每次新建 —— 被否（重复抓取产生重复边，污染 `el_page_flows`）。

**D3：`page_flow_compiler.py` 为纯函数（零 apps 依赖），输出严格对齐前端节点结构。**
输入结构化 `pages/edges`，输出 `{nodes, links}`；元素输出口仅给「有跳转边」的元素（`navigation` 类型），无跳转元素只进 `linked_elements` 不进输出口。备选：在 ai_assistant 层拼图 JSON —— 被否（图结构复杂、易幻觉破坏，收敛为 workflow 纯函数 + 校验）。

**D4：`build_page_flow_document` 走 `workflow.api.upsert_document` 落库，打破「AI 无写图工具」但收敛在 workflow.api。**
AI 只传结构化「页面关系」，不手写图 JSON；编译 + 落库都在 workflow.api。备选：AI 直调 `upsert_document` 传手写 config —— 被否（违反受控写图、易产生非法图）。

**D5：元素输出口只给「有跳转边」的元素。**
编译时按 `edges` 的 `trigger_element_id` 反查，只给这些元素建 `navigation` 输出口；其余元素仅进 `linked_elements`（供前端「关联页面→添加元素」复选）。符合需求「有页面跳转的添加工作流节点，没有的不添加」。

## 模块防火墙自检

- `element_locator.api_snapshot/api.py` 写库收敛本模块 ✅；`get_or_create_flow` 属本模块 api ✅。
- `workflow.page_flow_compiler` 零跨 App import（纯函数）✅；`build_page_flow_document` 走本模块 `upsert_document`，不 import 其它 App ✅。
- `ai_assistant.tool_registry` 新增 handler 只 import `element_locator.api` / `workflow.api` / `device_inspector.api`（白名单）✅，不 import 内部实现 ✅。
- `device_inspector.api.save_snapshot_to_elements` 透传 aliases 到 `element_locator.api.import_snapshot_page`（既有白名单链路）✅。
- 无新增 WS/SSE ✅。

## Risks / Trade-offs

- [生成的 config_json 与前端节点结构不匹配 → 画布渲染异常] → 编译器严格对齐 `types/workflow.ts`/`workflowStore.ts`，实现后用 `workflow.semantics.build_graph_digest` 校验解析出正确的 start/page/navigation_entries。
- [「AI 无写图工具」边界被打破] → 收敛在 `workflow.api.build_page_flow_document` + 纯函数编译器，AI 不直接拼图 JSON；需在 ARCH-09 登记该边界变更。
- [别名映射经 resource_id 可能重复（同页多个同 rid 元素）] → 别名只作展示/引用标签，元素唯一性仍由 `(page, resource_id, bounds)` 保证，不受影响。
- [BFS 爬取导致大量页面/元素入库] → 本轮不内置自动爬取，深度由 AI ReAct 控制；去重由 import upsert + get_or_create_flow 兜底。
