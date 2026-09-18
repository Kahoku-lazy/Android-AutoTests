## 1. element_locator：别名 + 幂等建边

- [x] 1.1 在 `apps/element_locator/api_snapshot.py` 的 `import_snapshot_page` 中，alias 取值改为「显式 `e["alias"]` 优先，回退 text/resource_id」。验证：`ruff check apps/element_locator/api_snapshot.py && pytest tests/element_locator -k import`
- [x] 1.2 在 `apps/element_locator/api.py` 新增 `get_or_create_flow(from_page_id, to_page_id, trigger_element_id=None, trigger_action="click")`（按 from/to/trigger 去重，复用或新建），加入 `__all__`。验证：`ruff check apps/element_locator/api.py && python manage.py check`

## 2. device_inspector：别名透传

- [x] 2.1 在 `apps/device_inspector/api.py` 的 `save_snapshot_to_elements` 增 `aliases=None` 参数（`{resource_id: alias}`），选中的元素按 resource_id 回填 `alias` 后传给 `import_snapshot_page`。验证：`ruff check apps/device_inspector/api.py`

## 3. workflow：受控写图

- [x] 3.1 新增 `apps/workflow/page_flow_compiler.py` 纯函数 `compile_page_flow_document(title, start_package, pages, edges) -> dict`：生成 VueFlow `{nodes, links}`（StartNode 启动 App + PageNode 带跳转元素 navigation 输出口，仅跳转元素进输出口）。验证：`ruff check apps/workflow/page_flow_compiler.py && pytest tests/workflow -k compiler`
- [x] 3.2 在 `apps/workflow/api.py` 新增 `build_page_flow_document(*, title, start_package, pages, edges, directory_id=None) -> (ok, payload)`（compile + `upsert_document` 落库），加入 `__all__`。验证：`ruff check apps/workflow/api.py && python manage.py check`

## 4. ai_assistant：工具

- [x] 4.1 在 `tool_registry.py` 新增 `create_page_flow` schema（元素定位分类、`elements/upsert_flow`、read_only=False、参数 from_page_id/to_page_id/trigger_element_id/trigger_action）+ handler 调 `element_locator.api.get_or_create_flow`。验证：`ruff check apps/ai_assistant/agent_scope/tool_registry.py`
- [x] 4.2 在 `tool_registry.py` 新增 `save_page_flow` schema（工作流分类、`workflow/save_page_flow`、read_only=False、参数 title/start_package/pages/edges/directory_id）+ handler 调 `workflow.api.build_page_flow_document`。验证：`ruff check apps/ai_assistant/agent_scope/tool_registry.py`
- [x] 4.3 在 `tool_registry.py` 的 `save_page_to_elements` schema 增 `aliases` 参数，handler 透传到 `device_inspector.api.save_snapshot_to_elements`。验证：`ruff check apps/ai_assistant/agent_scope/tool_registry.py`

## 5. 测试与门禁

- [x] 5.1 单测：`import_snapshot_page` 显式 alias；`get_or_create_flow` 幂等；`compile_page_flow_document` 输出结构（start/page/navigation 输出口/仅跳转元素）；`build_page_flow_document` 落库 doc_id。验证：`pytest -m "unit or integration" -k "alias or flow or page_flow"`
- [x] 5.2 跨模块边界合规：`python tools/gen_arch_stats.py --check-boundaries` 通过（0 违规）
- [x] 5.3 全链路门禁：`python manage.py check && ruff check apps/element_locator apps/device_inspector apps/workflow apps/ai_assistant && pytest -m "unit or integration"` 通过
