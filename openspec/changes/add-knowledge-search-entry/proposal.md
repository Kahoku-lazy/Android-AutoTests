## Why

平台「数据」分组缺少知识库检索入口：`engines/ae_harness/knowledge` 的只读检索能力已建成，但目前只能经命令行探针使用，业务人员无法在平台上检索产品资料。需求方要求一个轻量入口：勾选模块（可多选）→ 提问 → 返回检索原文，且模块的文档路径要能在平台上维护。

## What Changes

- 新增后端 App `knowledge_search`：模块登记表 `ks_modules`（DB 为平台侧真相源，增删改仅超管）；由 DB 生成平台自有 `knowledge_bases.yaml`，经 `load_config(bases_path=…)` 复用引擎全部校验（库名正则、启用库目录隔离）；只读检索桥每请求新建 `KnowledgeRetriever`，多选模块逐库检索后按相似度合并排序；提供超管预建索引端点。
- 新增前端模块 `knowledge-search`：侧栏「数据」组末尾「知识库」入口（入口级色 `--c-case`，与组内设备/串口异色）；分栏台版式——左栏模块勾选与路径管理（超管），右栏提问与检索原文展示；三态用共享件，no_hit 与 unavailable 文案分开。
- engines `knowledge/` 新增**用量出口**（本变更唯一 engines 改动，加法不改检索行为）：`usage.py` 以代理记录嵌入调用 token，`KnowledgeRetriever.usage_events()` 导出；后端经 `usage_ledger.api` 逐调用写入 `ai_usage_records`（category=Embedding、source=knowledge），入账失败不阻断检索。
- 新增 HTTP 面 `/api/knowledge-search/*`（尾斜杠、`{status, data}`、snake_case）；旧退役路径 `/api/ai/knowledge/*` 保持 404，不复活文档上传与引用范围。
- **BREAKING**（spec 口径）：修订 `knowledge-base-retirement`「不得暴露知识库入口与检索结果」条款为「旧 RAG 文档库保持下线，允许本地只读检索预览」；`frontend-doodle-subpage-nav` 中「侧栏不出现知识库」场景限定为 AI 助手分组与旧 RAG 页。
- 变更申请已于 2026-11-18 经需求方对话确认批准（四要素详见 design.md）：上述两条 spec 修订、`knowledge/AGENTS.md` 现状段更新、`harness-knowledge` 零引用范围澄清（限 ae_harness 内部）、嵌入 token 入账口径。
- v1 明确不做：提问历史落库、top_k 调节 UI、文档上传/预览、Agent 挂载、检索结果生成总结；自动评测另立 change `add-knowledge-auto-eval`。

## 关联文档

PRD-08（知识库助手与 RAG 运营边界条款）。「数据组知识库检索入口」为需求方 2026-11-18 新增需求（对话确认），PRD 条目在 apply 阶段同步补写。

## Capabilities

### New Capabilities

- `knowledge-search-entry`: 平台知识库检索入口——模块登记与路径维护、多模块勾选检索、原文命中展示、预建索引、嵌入用量入账、前端入口与页面行为。

### Modified Capabilities

- `knowledge-base-retirement`: 产品面 / HTTP 面 / 实现面三条 requirement 由「全面禁止知识库入口与检索结果」改为「旧 RAG 文档库（上传/引用范围/chromadb/旧端点）保持下线，允许基于 harness knowledge 的本地只读检索预览」。
- `harness-knowledge`: 「零依赖独立模块」requirement 澄清零引用范围为 ae_harness 内部（允许 backend 只读检索桥局部可选导入）；新增「嵌入用量出口」requirement。
- `frontend-doodle-subpage-nav`: 「AI has a single entry」场景的「侧栏与路由不出现知识库」限定为 AI 助手分组与旧 RAG 页；数据组新入口不受该句约束。

## Impact

- engines：`ae_harness/knowledge/` 新增 `usage.py`，`service.py` 接线与出口；独立性守护测试不改（backend 引用不在其扫描面）；docstring / 风格自检随改动跑。
- backend：新增 `apps/knowledge_search`（models / api / registry / retrieval / views / urls / migrations）；`config/urls.py` 一行 include；`usage_ledger/api.py` 新增嵌入入账入口；`INSTALLED_APPS` 登记。
- frontend：新增 `modules/knowledge-search`；`sidebarNavConfig.ts` 加入口与 `MOD_COLORS`；lucide 图标子集登记一枚；`sidebarNavConfig.spec.ts` 同组异色断言覆盖新入口。
- 文档：`knowledge/AGENTS.md` 现状段与文件职责表；PRD 条目补写。
- 测试：`tests/knowledge_search/{unit,integration,api}`；`tests/engines/ae_harness/unit/test_knowledge_usage.py`；arch 契约守护自动覆盖新端点与前端调用面。
- 计费：`ai_usage_records` 新增 source=knowledge、category=Embedding 行；价目表已收录 `text-embedding-v4`，不改价目与公式。
- 回退：删除新 App 与前端入口、还原 spec / AGENTS 措辞即可；`ks_modules` 为独立新表，无跨表残留。