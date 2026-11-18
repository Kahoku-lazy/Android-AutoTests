## Context

动机见 proposal.md - Why。方案需要的现状与约束：

- `engines/ae_harness/knowledge` 已具备：`load_config(bases_path=…)` 支持外部库目录文件并自带全部校验（库名正则、启用库目录隔离、defaults）；`KnowledgeRetriever.retrieve(query, base=…, top_k=…)` 返回 ok / no_hit / unavailable 三态与六字段命中；`base=None` 检索全部启用库，**没有"指定多个库"参数**；检索器内部有 `asyncio.Lock`，**不跨事件循环复用**；索引只扫 `.md/.txt`，按 mtime/大小/切块版本增量嵌入；`index/` 已 gitignore、可随时重建。
- agentscope 2.0.9（本机已核实源码）：`DashScopeEmbeddingModel._call_text` 返回 `usage.tokens = response.usage["total_tokens"]`；基类 `__call__` 分批并发并把各批 tokens 求和；`KnowledgeBase` 对嵌入模型只用 `__call__` / `.dimensions` / `.supports_multimodal`；knowledge 建模型未启用缓存，全部是真实 API 调用。
- backend 直调 ae_harness 原语已有先例（`ai_assistant` import `ae_harness.tools / event / middleware.control`）；异步引擎调用的现成写法是同步上下文内 `asyncio.run`（`assistant_threads.py`）。
- `usage_ledger`：`source` 为自由字符串、分类固定含 `Embedding`、`pricing.json` 已收录 `text-embedding-v4`（input_per_million 0.5，estimated）；红线要求跨 App 写走对方 `api.py`、入账失败不阻断主流程、不伪造金额。
- 前端：侧栏「数据」组现有设备（`--c-device`）/串口（`--c-workflow`），同组异色由 `sidebarNavConfig.spec.ts` 断言锁住；`book-open` 不在 lucide 运行时子集内，需登记。
- 规则冲突与批准记录见下方「变更申请记录」。

## Goals / Non-Goals

**Goals:**

- 平台侧模块登记（DB 真相源）与引擎检索能力之间建一条**只读、可降级、可记账**的桥。
- engines 改动收敛为一处加法（用量出口），检索行为与三态文案零变化。
- 多选模块检索、原文展示、超管管理面、嵌入 token 逐调用入账。

**Non-Goals:**

- 不做 Agent 挂载、生成式答案、文档上传/预览、提问历史落库、top_k 调节 UI（v1 用配置默认 4）。
- 不做自动评测（change `add-knowledge-auto-eval`）。
- 不改价目表、计费公式与账本表结构。
- 不重写引擎检索/索引实现，不在后端复制一套校验。

## Decisions

### D1 模块登记：DB 真相源 + 派生 yaml 适配器

`ks_modules` 表（name 唯一 slug / description / data_dir / enabled / 时间戳）是唯一写点 `api.py` 的对象。每次 CRUD 后由 `registry.py` 把 DB 全量重生成为**平台自有**的 `knowledge_bases.yaml`（settings 常量 `KNOWLEDGE_SEARCH_BASES_FILE`，默认 `logs/knowledge_search/knowledge_bases.yaml`，gitignore 覆盖）；检索时 `load_config(bases_path=该文件)`。

- 为什么：免费复用引擎全部校验（库名正则、目录隔离、defaults），后端不重写验证；engines 自带 yaml 保持只读，不违反 knowledge「禁止知识库写接口」红线（写的是平台自己的派生文件，不是引擎配置）。
- 备选①「平台直接改引擎 yaml」：把平台运营面写进 engines 配置，违反只读红线且 git  tracked 文件被运行时改写，弃。
- 备选②「后端直接构造 KnowledgeConfig dataclass」：绕过 yaml 校验、复制验证逻辑，弃。
- 嵌入模型配置仍用引擎自带 `config/models.yaml`（红线：只允许向量模型），平台不登记嵌入模型。
- 初始数据：数据迁移在表为空时读引擎自带 `knowledge_bases.yaml`（yaml.safe_load 直读，不 import engines）导入既有登记，幂等。

### D2 索引目录：与探针共享引擎默认 `index/`

`KnowledgeRetriever(config)` 不传 `index_dir`，平台与探针共用同一份 SQLite 索引与 `index_state.json`。

- 为什么：同一份资料避免双重嵌入花钱；索引可重建，整目录删除承诺不破。
- 备选「平台自有索引目录」：同库双份嵌入成本，且切块参数一致时毫无收益，弃。

### D3 依赖方向：backend 局部可选导入 knowledge（不经 backend_bridge）

`retrieval.py` 内 `try: from engines.ae_harness.knowledge… except ModuleNotFoundError`（只吞本模块缺失），照 knowledge AGENTS 的接回模板。

- 为什么：backend 直调 ae_harness 原语已有先例；backend_bridge 属 engines 内部，让它 import knowledge 会触碰「Harness 其它模块不得 import 知识库」守护措辞，且多一跳无收益。守护测试只扫 ae_harness 内部，backend 引用不破坏它（spec 已显式澄清）。
- 备选「backend_bridge 加门面」：需同步改守护测试期望清单，把平台装配塞进引擎层，弃。

### D4 检索执行：同步视图 + `asyncio.run` + 每请求新建检索器

View 只分发 → `retrieval.py`：请求内新建 `KnowledgeRetriever`，对每个勾选库 `retrieve(question, base=name)`，合并命中按 score 降序截断 top_k；逐库错误聚合进 `errors`。进程级 per-base `threading.Lock` 防并发首问重复建索引（检索器锁是实例级，挡不住跨请求）。

- 为什么：增量索引 + 小语料下同步最简；assistant 的后台线程 + 轮询模式留给大语料升级路径。
- 首问慢对策：超管「预建索引」端点（同步、返回重建数）+ 前端加载文案「首次检索会建立索引，可能较慢」+ 前端请求超时放宽（120s）。
- 备选「v1 即后台任务化」：多一套状态表与轮询，v1 语料规模不需要，弃。

### D5 用量出口：knowledge 内代理包装（唯一 engines 改动）

新增 `knowledge/usage.py`：`UsageEvent` 数据类（model / api_key_env / tokens / time / phase / base / occurred_at）+ 记录代理（透传 `__call__`，读 `response.usage`，委托 `.dimensions` / `.supports_multimodal`）。`service.py` 在 `_embedding_model()` 处包代理；`KnowledgeRetriever.usage_events()` 取出并清空事件，phase（index/retrieve）与 base 由 service 在调用处打标。只依赖 agentscope 与标准库。

- 为什么：`KnowledgeRetriever` 内部自建嵌入模型、无注入点；后端绕过 service 自拼 `KnowledgeBase` 等于复制检索实现。代理在 `__call__` 层拿到的是框架合并后的整次逻辑调用总量，天然满足「每次调用一条记录」。
- 备选「后端 monkeypatch create_embedding_model」：隐式全局副作用，弃。
- tokens 为 0/None 不产事件；密钥只出现环境变量名。

### D6 入账映射：经 usage_ledger.api 新增嵌入入账函数

`usage_ledger/api.py` 新增 `record_embedding_usages(events, execution_id, source="knowledge")`（内部走既有 `record_usage`）：provider=dashscope、model=事件模型名、category=Embedding、input_tokens=tokens、output_tokens=0、`event_id = knowledge:{execution_id}:{usage_id}`（幂等）、execution_id=请求 UUID（预建索引用索引批 UUID）。检索/索引结束后调用；失败只记日志。

- 为什么：跨 App 写必须走对方 api.py；价目与公式零改动（text-embedding-v4 已收录）。
- 备选「复用 record_voice_event」：语义是语音助手事件，命名与默认模型回落都不匹配，弃。

### D7 前端：新模块 + 数据组入口 + 分栏台

`modules/knowledge-search/`（routes / index.vue / api.ts / types / constants / components / composables / helpers）。侧栏数据组末尾加「知识库」，`MOD_COLORS["/knowledge-search"] = "var(--c-case)"`（入口级色，照 `--c-account`/`--c-task` 先例只用于侧栏图标底 + active 书签条，不扩散进页面）；lucide 子集登记 `book-open`。页面根 `.doc-page.wb-shell`，版式变体 C 分栏台：左「知识模块」面板（AppCard 壳 + 复选列表），右「提问」面板（输入 + DoodleBtn + 命中流）。命中条目用实线卡（DoodleNote 或 AppCard 内条目），逐字原文 + 库名标签 + 来源 + 片段序号 + 相似度；三态共享件；删除走 ConfirmButton；模块表单走 el-dialog，路径为**服务器绝对路径文本输入**（浏览器拿不到服务器路径，且红线禁上传）。管理按钮经 `useAuthUser().isSuperuser` 传 `can-manage`。合并排序等纯函数下沉 helpers；新 .vue ≤500 行。

### D8 契约与权限

`/api/knowledge-search/` 前缀（config/urls.py 一行 include）；全部尾斜杠；`{status, data}` / `{status, message}`；snake_case（前端侧转 camelCase）；超管判定 `shared.users.is_superuser`。端点：GET modules/（登录）、POST modules/（超管）、PATCH/DELETE modules/{id}/（超管）、POST query/（登录）、POST modules/{id}/index/（超管）。旧 `/api/ai/knowledge/*` 不复活。

## 变更申请记录（2026-11-18 需求方对话批准）

| # | 改什么 | 为什么必须改 | 影响面 | 怎么回退 |
| --- | --- | --- | --- | --- |
| 1 | `knowledge-base-retirement` 三条 requirement：全面禁止 → 旧 RAG 文档库保持下线 + 允许只读检索预览 | 新入口与现行 MUST NOT 直接矛盾，不改则无法合规落地 | 仅 spec 措辞；旧端点/上传/引用范围禁令全部保留 | 还原措辞、删除新入口 |
| 2 | `knowledge/AGENTS.md` 现状段「只能经探针使用」→ 允许 backend 只读检索桥；文件表加 usage.py | 平台入口不是探针，现行口径禁止 | 文档；不接任何 Agent、不生成 | 还原文档 |
| 3 | `harness-knowledge` 零引用条款澄清范围为 ae_harness 内部 + 新增用量出口 requirement | backend 引用与用量出口需要显式规范依据，不允许静默放开 | spec；守护测试不改 | 还原条款、删 usage.py |
| 4 | 计费口径：嵌入调用 token 入 `ai_usage_records`（Embedding / source=knowledge） | platform-usage-billing 要求每次模型调用入账，knowledge 原无用量出口 | 账本新增行；价目/公式/表结构零改动 | 停入账（历史行保留） |
| 5 | `frontend-doodle-subpage-nav`「侧栏不出现知识库」场景限定为 AI 助手组与旧 RAG 页 | 与数据组新入口字面冲突 | spec 措辞；AI 助手单入口不变量保留 | 还原措辞 |

## 模块防火墙自检

- 跨 App import：`knowledge_search` 只写自己的 `ks_modules`（经本 App api.py）；写账本只经 `usage_ledger.api.record_embedding_usages`；不 import 任何其它 App 的 service/runner/views；v1 不读 ai_assistant 模型配置（嵌入配置来自引擎 yaml）。
- 所有 INSERT/UPDATE/DELETE 收敛：`ks_modules` → `knowledge_search/api.py`；`ai_usage_records` → `usage_ledger/api.py`。View 只分发。
- 前端不直连数据库；仪表盘不做写操作（本变更不动仪表盘）。
- 新跨模块依赖清单：① `knowledge_search → usage_ledger.api`（规则允许的写路径）；② `knowledge_search → engines.ae_harness.knowledge`（backend→engines 注入方向，局部可选导入，先例见 D3）；③ 前端 `knowledge-search → shared/*` 共享件。无 engines 反向依赖、无跨 App 内部实现 import。
- engines 红线：knowledge 不 import 兄弟包（usage.py 只依赖 agentscope/标准库）；不新增自定义异常类；不造 Agent；资料目录只读；不新增第二份 .env。

## Risks / Trade-offs

- [首问大目录索引超时] → 超管预建索引按钮 + 加载文案 + 前端 120s 超时；语料变大再升级后台任务化（D4 备选路径）。
- [并发首问重复嵌入花钱] → 后端进程级 per-base 锁；最坏情况仍只是多一次嵌入，索引结果幂等。
- [SQLite 全表扫描余弦检索在大语料下慢] → v1 接受（小语料定位）；自动评测 change 会给出时延数据，作为优化依据。
- [准确率/召回率未评测] → UI 定位「检索原文预览」，展示相似度供人判断，不呈现为答案；评测能力另立 change。
- [平台 yaml 与 DB 漂移] → yaml 是派生产物：每次 CRUD 全量重生成，检索每请求重读，不做缓存。
- [资料目录校验后被删（TOCTOU）] → 索引器已对缺失目录降级为 unavailable，不炸请求。
- [引擎整目录删除] → 局部可选导入降级（spec R5），模块管理面不受影响。
- [入口级色 --c-case 与用例模块同色] → 规则只禁同组同色；数据组内绿/蓝/青绿互异，spec 测试覆盖。

## Migration Plan

1. 合入 engines 用量出口（usage.py + service 接线 + 单测），守护测试保持绿。
2. backend：新 App 迁移（建表 + 空表种子导入）→ INSTALLED_APPS / urls include → usage_ledger 入账函数。
3. frontend：新模块 + 侧栏入口 + 图标登记；`npm run lint:styles` + `vue-tsc` + sidebarNavConfig.spec。
4. 文档：knowledge/AGENTS.md 现状段与文件表、PRD 条目补写。
5. 验证：`python run.py check`；`python -m pytest -c tests/pytest.ini tests/knowledge_search tests/engines/ae_harness/unit -q`；手工演练（新增模块→预建索引→多选提问→改路径→删除模块→账本核对）。
6. 回退：移除 include / INSTALLED_APPS / 侧栏入口与模块目录，还原 spec 与 AGENTS 措辞；`ks_modules` 独立表可留可删；账本历史行保留不动。

## Open Questions

（无——图标具体选型、前端超时数值等实现细节可在 apply 阶段定，不影响 specs 与任务拆分。）