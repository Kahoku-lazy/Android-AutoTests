## 1. 改动

- [x] 1.1 `engines/agents/middleware/assembly.py`：`build_agent_middlewares()` 增 `with_rag: bool = False`，只有显式为 True 才尝试装配 RAG（仍需全局开关 + 索引可用）
- [x] 1.2 `engines/agents/role/base.py` 不传该参数 → SOP 执行／验收角色在任何配置下都不装 RAG
- [x] 1.3 文档：`assembly.py` docstring 写明「`data/rag_index` 是产品资料，设备控制角色拿到只会被带偏」

## 2. 验证

- [x] 2.1 `test_sop_roles_never_get_rag`：`AGENT_RAG_ENABLED=1` + 索引可用时，`build_agent_middlewares()` 仍不含 `RagContextMiddleware`
- [x] 2.2 `test_knowledge_roles_get_rag`：同样环境 + `with_rag=True` 时包含 `RagContextMiddleware`
- [x] 2.3 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_agent_middleware_assembly.py -q` → **20 passed**
- [x] 2.4 `ruff format --check` / `ruff check` 对改动文件 → 通过
- [x] 2.5 `npx openspec validate scope-rag-middleware-by-role --strict` 通过
