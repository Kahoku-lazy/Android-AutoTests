## 1. workflow 侧出口：补层级 + 不限量

- [x] 1.1 `apps/workflow/api_digest.py::list_document_summaries`：`limit` 默认改为 `None`（不传即全量），每条补 `directory_path`（祖先名以 `/` 连接）与 `directory_depth`（根为 1，未归类为 0）；实现一次取目录 + 记忆化构链，含环/深度保护，验证：`python -m ruff check apps/workflow/api_digest.py` 通过，且新用例断言多级路径与深度

## 2. 工具层：签名与返回体收敛

- [x] 2.1 `apps/ai_assistant/tools.py::list_page_flows` 收敛为 `list_page_flows(query="")`，返回 `{"total": N, "documents": [...]}`，去掉 `limit` 与 `directory_id`（docstring 同步说明全量与层级语义），验证：`python -m ruff check apps/ai_assistant/tools.py` 通过

## 3. 文档同步

- [x] 3.1 `engines/ai/skills/platform-tools-manual/SKILL.md` 的 `list_page_flows` 行与「② 读页面流」推荐序列改为「一次列出全部文档并带目录路径」；`dev_docs/DEV_TEST/接口文档/API-工作流.md` 的「非 HTTP 数据出口」小节补新字段说明，验证：两处文档均描述全量与 `directory_path`/`directory_depth`

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_ai_page_flow_listing.py`：造 1 原型 + 三级目录 + 文档（含未归类、含超过 20 篇），断言 `total` 与条数一致（不截断）、`directory_path` 为 `默认目录/详情页/深一层` 形式、`directory_depth` 正确、未归类为 null/""/0、`query` 收窄生效，验证：`python -m pytest tests/graybox/unit/test_ai_page_flow_listing.py -q` 通过

## 5. 门禁与抽验

- [x] 5.1 后端门禁：`python manage.py check`、`python -m ruff check`（改动文件）、`python -m ruff format --check`（改动文件）、`python -m pytest tests/graybox/unit -q`、`python tools/gen_arch_stats.py --check-boundaries`，验证：全部通过、边界零违规
- [x] 5.2 现有库抽验：`list_page_flows()` 返回 `total=2`，其中未归类那篇 `directory_path=""`/`directory_depth=0`、另一篇为 `默认目录`/深度 1，验证：输出与库内数据一致，且不再有 20 条上限
