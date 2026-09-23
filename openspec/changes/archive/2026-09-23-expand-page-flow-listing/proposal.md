## Why

`list_page_flows` 现在默认只返回 **20 条**（`limit=20` 截断），且每条只有 `directory_name`（当前目录名）——**没有目录层级信息**。模型据此选测试点时，看不到「这篇流在目录树的哪一层、和哪些流同属一个目录」，也无法确认是否漏了第 21 篇之后的文档。需要一次拿全，并带上层级。

## What Changes

- `list_page_flows` 收敛为 `list_page_flows(query="")`：**返回全部页面流文档**（去掉 `limit` 截断与 `directory_id` 过滤；`query` 保留为可选收窄）。返回体由裸数组改为 `{"total": N, "documents": [...]}`。
- 每条文档增加**目录层级信息**：`directory_path`（祖先目录名以 `/` 连接，如 `默认目录/详情页`）与 `directory_depth`（根为 1）。
- **未归入目录**的文档 MUST 仍被列出，以 `directory_id: null`、`directory_path: ""`、`directory_depth: 0` 明确标示（不得静默丢弃）。
- 层级拼接落在 workflow 侧的既有 AI 数据出口 `api_digest.list_document_summaries`（其 `limit` 默认改为不限，并补 `directory_path`/`directory_depth`），一次构链、避免 N+1。
- 同步：仓库内工具手册的该工具说明与「读页面流」推荐序列、`API-工作流.md` 的「非 HTTP 数据出口」小节。
- **非目标**：不改 `get_page_flow`（仍按 doc_id 取语义摘要）；不新增「目录树」型返回（用户已在选项 A/B/C 中选定「文档列表为主 + 每条带路径」）；不改 `list_page_flows` 的分类归属（仍属「页面流工具」）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`split-device-action-tool`（工具面重构与分类改名）、`add-platform-tool-debug`（调试页）

## Capabilities

### New Capabilities

- `ai-page-flow-listing`: `list_page_flows` 的列表契约——全量返回、目录路径与深度、未归类文档的明确表示、可按关键词收窄。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/workflow/api_digest.py`（`list_document_summaries` 补层级与不限量）、`apps/ai_assistant/tools.py`（`list_page_flows` 签名与返回体）
- 测试：新增 `tests/graybox/unit/test_ai_page_flow_listing.py`（多级路径、未归类、超 20 篇不截断）
- 文档：`engines/ai/skills/platform-tools-manual/SKILL.md`、`dev_docs/DEV_TEST/接口文档/API-工作流.md`（非 HTTP 数据出口小节）
- 迁移 / 前端 / 引擎：无（`list_page_flows` 不在任何角色工具子集内：`DEVICE_PLANNER_TOOLS` 为空、`VISION_TOOLS` 不含它）
