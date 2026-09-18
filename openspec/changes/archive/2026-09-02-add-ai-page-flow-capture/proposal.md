## Why

AI 智能体已能经 `device_action` 控制手机、`capture_page/analyze_page` 抓取页面结构，但「抓到的页面」只能停留在快照，无法沉淀为平台资产：元素无法带中文别名保存到元素定位、页面之间的跳转关系无法落库、更无法生成工作流页面流图。要完成「AI 抓页面关系 → 元素管理 + 工作流」闭环，需补齐"元素别名持久化 + 跳转关系幂等建边 + 受控写工作流图"三个能力。

## What Changes

1. `apps/element_locator`：
   - `import_snapshot_page` 支持元素显式 `alias`（优先用别名，回退 text/resource_id）。
   - `api.py` 新增幂等建边 `get_or_create_flow`（按 from/to/trigger 去重，防重复抓取产生重复边）。
2. `apps/workflow`：
   - 新增 `page_flow_compiler.py` 纯函数：结构化「页面 + 跳转边」→ VueFlow `config_json`（StartNode 启动APP + PageNode 带元素输出口 + navigation 连线）。
   - 新增 `build_page_flow_document` 白名单函数（编译 + 经 `upsert_document` 落库 `wf_documents`），打破「AI 无写图工具」边界——受控写图，AI 只传页面关系结构化数据、不手写图 JSON。
3. `apps/ai_assistant`：
   - 新增写工具 `create_page_flow`（`elements/upsert_flow`，幂等写 `el_page_flows`）。
   - 新增写工具 `save_page_flow`（`workflow/save_page_flow`，生成 `wf_documents` 页面流）。
   - `save_page_to_elements` 工具增补 `aliases` 参数，透传中文别名到元素定位。

无 **BREAKING** 变更（新增能力，现有契约不变）。

## 关联文档

- `dev_docs/02-PRD需求/PRD-04-元素定位.md`（元素资产 + 跳转流 PageFlow）
- `dev_docs/03-设计与架构/ARCH-04-元素定位.md` §5.1/§6.2（`el_page_flows` / `import_snapshot_page` / `create_flow`）
- `dev_docs/02-PRD需求/PRD-09-工作流工作台.md`（页面流编排）
- `dev_docs/03-设计与架构/ARCH-09-工作流工作台.md` §5/§6/§7（`wf_documents.config_json` / `semantics.py` / 「AI 无写图工具」边界）
- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §4.1（平台业务工具）

## Capabilities

### New Capabilities

- `ai-page-flow-capture`: AI 智能体可把抓取的页面元素（带中文别名）保存到元素定位、建立页面跳转关系，并生成工作流页面流文档（启动 App → 主页 → 跳转页面节点 + 元素输出口）。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/element_locator/api_snapshot.py`（alias）、`apps/element_locator/api.py`（`get_or_create_flow`）、`apps/workflow/page_flow_compiler.py`（新增）、`apps/workflow/api.py`（`build_page_flow_document` 再导出）、`apps/device_inspector/api.py`（`save_snapshot_to_elements` 别名透传）、`apps/ai_assistant/agent_scope/tool_registry.py`（2 个新工具 + save 工具增参）
- 测试：`manage.py check` + `ruff check` + `pytest`；`python tools/gen_arch_stats.py --check-boundaries`
