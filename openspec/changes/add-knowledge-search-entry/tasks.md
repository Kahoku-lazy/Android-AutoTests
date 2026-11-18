## 1. engines 用量出口（唯一 engines 改动）

- [x] 1.1 先读 `.agents/rules/engines-code-style.md` 相关章节；新增 `engines/ae_harness/knowledge/usage.py`（UsageEvent 数据类 + 嵌入记录代理：透传 `__call__`、委托 dimensions/supports_multimodal、读 response.usage、零 token 不产事件），新增 `tests/engines/ae_harness/unit/test_knowledge_usage.py` 并跑通（代理透传、事件字段齐全、零 token 不记、无兄弟包 import）
- [x] 1.2 `service.py` 接线：`_embedding_model()` 包代理、新增 `usage_events()` 出口、phase(index/retrieve)/base 打标；验证 `pytest -c tests/pytest.ini tests/engines/ae_harness/unit -q` 全绿（三态文案与命中字段不变、独立性守护不变）
- [x] 1.3 更新 `knowledge/AGENTS.md`：文件职责表加 usage.py、现状段改为「允许 backend 只读检索桥，仍不挂任何角色」；验证 `cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check` 与 `cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style` 无本次新增告警

## 2. backend 账本与模块登记

- [x] 2.1 `usage_ledger/api.py` 新增 `record_embedding_usages(events, execution_id, source)`：走既有 record_usage，event_id=`knowledge:{execution_id}:{usage_id}` 幂等、category=Embedding、失败只记日志；验证 `pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` + 新增嵌入入账单测（重复提交不翻倍、零 token 跳过、写失败不抛）
- [x] 2.2 新建 `backend/apps/knowledge_search` 骨架：apps.py、models.py（ks_modules：name 唯一 slug/description/data_dir/enabled/时间戳）、api.py 唯一写点（CRUD + 库名正则/路径存在可读/启用库目录隔离校验，校验失败不落库）；迁移建表 + 空表时读引擎自带 knowledge_bases.yaml 种子导入（幂等）；验证 `python manage.py check` + `makemigrations --check` + tests/knowledge_search/unit 校验规则用例

## 3. backend 检索桥与 HTTP 面

- [x] 3.1 `registry.py`：DB 全量派生平台 yaml（settings `KNOWLEDGE_SEARCH_BASES_FILE`，默认 logs/knowledge_search/，gitignore 覆盖），CRUD 后重生成；验证单测（yaml 与 DB 一致、load_config(bases_path=…) 装载成功、冲突目录被引擎校验拒绝）
- [x] 3.2 `retrieval.py`：局部可选导入 knowledge（ModuleNotFoundError 只吞本模块）、每请求新建 KnowledgeRetriever、多选逐库 retrieve 合并按 score 降序截断 top_k、逐库错误聚合、进程级 per-base 锁、结束后经 usage_ledger.api 入账；验证单测（合并排序、部分失败返回 hits+errors、三态区分、引擎目录缺失降级 unavailable、入账失败不阻断）
- [x] 3.3 views/urls/serializers：GET modules/（登录）、POST modules/（超管）、PATCH/DELETE modules/{id}/（超管）、POST query/（登录，bases 非空否则 400）、POST modules/{id}/index/（超管，返回重建数）；`config/urls.py` include `api/knowledge-search/` + INSTALLED_APPS 登记；信封 {status,data}、snake_case、尾斜杠、超管判定 shared.users.is_superuser；验证 `pytest -c tests/pytest.ini tests/knowledge_search/api -q` + `python manage.py spectacular --validate`

## 4. frontend 入口与检索页

- [x] 4.1 lucide 运行时子集登记 `book-open`；`sidebarNavConfig.ts` 数据组末尾加「知识库」(/knowledge-search) + `MOD_COLORS` 入口级色 `var(--c-case)`；验证 `frontend/tests/shared/p0/sidebarNavConfig.spec.ts` 同组异色断言通过
- [x] 4.2 新建 `modules/knowledge-search/` 骨架：routes.ts、api.ts（HTTP 唯一出口，走 shared/api-client，路径与后端逐条对齐）、types.ts、constants.ts、composables（useKnowledgeModules / useKnowledgeQuery）；验证 `npx vue-tsc --noEmit` + arch 契约守护（tests/arch/unit 路径 resolve 断言）通过
- [x] 4.3 左栏 ModulePanel：AppCard 壳 + 复选列表（名称/描述/路径/启用徽标）+ 超管管理（el-dialog 表单：库名/描述/服务器绝对路径文本输入，ConfirmButton 删除，启停，预建索引按钮）；can-manage 经 useAuthUser().isSuperuser；验证 `npm run lint:styles` + vue-tsc + 新 .vue ≤500 行
- [x] 4.4 右栏 QueryPanel：提问输入 + DoodleBtn（未勾选禁用）+ 命中流（实线条目卡：库名标签/来源文件/片段序号/相似度/逐字原文）+ 三态共享件（加载期不渲染空态，no_hit 与 unavailable 文案区分）+ 只索引 .md/.txt 与首问建索引提示；合并排序纯函数下沉 helpers；验证 lint:styles + vue-tsc
- [x] 4.5 index.vue 分栏台组装：`.doc-page.wb-shell` + WorkbenchHeader + `.doc-body` 滚动 + 两面板权限传递；验证 `npm run build` 通过

## 5. 测试、文档与门禁

- [x] 5.1 补齐 `tests/knowledge_search/{unit,integration,api}` 对照 spec 全场景（改路径后旧文件不再命中、增量跳过、种子导入、权限 403、信封与尾斜杠、嵌入入账逐调用一条）；验证 `pytest -c tests/pytest.ini -m "unit or integration"` 相关路径全绿 + api 套件通过
- [x] 5.2 PRD 条目补写：`dev_docs/ARCH_PRD/PRD-平台总需求.md` 增「数据组知识库只读检索入口」条目（编号沿用文档体例，注明 2026-11-18 需求方确认）；验证人工审阅与 proposal 关联文档编号一致
- [ ] 5.3 全链路人工验收：新增模块→预建索引→多选提问看原文→改路径→删除模块→账本核对 Embedding 行与 token 数；验证 `python run.py check` 退出码 0 + `python utils/gen_arch_stats.py --check-boundaries` 通过
- [x] 5.4 按 Conventional Commits 分提交（engines / backend / frontend / docs 各自逐文件暂存，禁 git add -A），推送 Kahoku；验证 ci-phase1.yml 6 个 job 全绿