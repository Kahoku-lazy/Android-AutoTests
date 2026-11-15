## Context

`engines/ae_harness/` 是「手机 UI 执行 + 验收」的独立原型链路，当前只挂 adb 工具。产品资料检索需要向量能力，而 AgentScope 2.0.9 已提供 `KnowledgeBase`、`VectorStoreBase`、`TextParser`、`ApproxTokenChunker`，不需要自己写检索算法。

约束：

- 知识库必须**整目录可删除**：删掉后 adb 工具、角色创建、事件记录、SOP 全部照常。
- 向量模型配置属于知识库自己，不得进入 `agents/config/models.yaml`。
- 引擎不依赖 Django / `backend.apps`；知识库也不依赖 Harness 其它模块。
- 只在 agent 真正调用检索时才工作，import 不产生副作用。

## Goals / Non-Goals

**Goals:**

- 一个自带配置、自带索引、可独立删除的检索模块。
- 只读检索工具，输出结构化命中。
- 违反目录准入的知识库实现被挡在 `tools/` 之外。

**Non-Goals:**

- 不做文档上传、知识库写接口、知识库运营页面。
- 不做 metadata 字段过滤（只做 `top_k` 与相似度阈值）。
- 不做重排（`rerank_model`），不做 static 提示词注入。
- 不替换或复用 `engines/agents/rag` 的实现。
- 不支持 PDF / PPT / Word / Excel，只索引 `.md` / `.txt`。

## Decisions

### 1. 放根级 `knowledge/`，不进 `tools/`

`tools/` 的准入在本次收紧为三类工程形态：**Python 内置函数工具、Skill、MCP**。知识库不属于这三类（它自带配置、向量库与索引状态），放进 `tools/` 会让「工具目录」同时承担存储与配置职责。

备选是把知识库塞进 `tools/knowledge/` 并给配置读取开豁免。否决：那等于为一个个案在关键目录上开永久例外，后续任何带状态的模块都会援引同样的理由。

### 2. 自带两份 yaml，`models.yaml` 只允许向量模型

`config/models.yaml` 用 `extra="forbid"`，只认 `provider` / `api_key` / `model_name` / `dimensions`，且 `provider` 只允许 `dashscope`。出现 chat / realtime / tts 条目视为配置非法。

`config/knowledge_bases.yaml` 放 `defaults`（top_k、阈值、切块参数、引用哪条向量模型）与各库的 `description` / `data_dir` / `enabled`。

拆两个文件的理由：模型配置很少动，库目录经常增删；混在一起会让「加一个库」变成「改模型配置文件」。

备选是在 `agents/config/models.yaml` 加一条 embedding 条目并扩 `agents/models.py`。否决：那会把知识库的依赖反向插进角色层，删除知识库时必须在 `agents/` 上动刀，违反本变更的核心目标。

### 3. 零依赖 Harness 其它模块

`knowledge/` 不 import `agents/`、`assistant/`、`event/`、`middleware/`、`workflow/`、`tools/`。它只依赖 `agentscope`、`yaml`、`dotenv` 与标准库。

代价：密钥取值（仓库根 `.env` → 进程环境）与 `agents/config.load_secret` 重复约 15 行。接受，因为 `tools/`、`agents/` 都禁止被反向依赖；独立性优先于去重。

### 4. 懒加载：import 零副作用

`import engines.ae_harness.knowledge` 不读 yaml、不连 SQLite、不建索引。`build_knowledge_tools()` 只返回工具对象。第一次 `search_knowledge` 调用时才：读配置 → 造嵌入模型 → 开库 → 首次 `ensure_index`。

备选是入口启动预热。否决：预热会让「没配知识库」的环境也去连数据库，且入口要懂知识库内部。

### 5. 只读工具 + 结构化输出

工具标 `is_read_only=True`、`is_concurrency_safe=True`，权限固定 ALLOW。返回 JSON 文本，遵循 `tools/` 既有返回契约：成功带 `timestamp` / `status: true` / `hits`；失败带 `timestamp` / `status: false` / `error`。

「没命中」与「检索不可用」必须给出不同文案，否则嵌入服务故障会被伪装成「资料里没有」。

### 6. 只做 `top_k` 与相似度阈值

`KnowledgeBase.search(queries, top_k, score_threshold)` 每次只接受这两个筛选参数；`metadata_filter` 只能在构造句柄时固定。本期只用前两个。不传 `base` 时检索全部启用库，合并后按分数排序取 `top_k`。

### 7. 本期不挂载：引用数为零

效果没有测过——目前只验证了「能跑通」（索引成功、命中字段齐全、三种返回文案正确），**没有测准确率与召回率**。所以**不接到任何角色上**。

Harness 其余模块（`tools/__init__.py`、`assistant/`、`event/`、`workflow/`）一律不引用知识库，引用数由测试守成零；知识库只能经 `python -m engines.ae_harness.knowledge` 探针使用。

接回方式写在 `knowledge/AGENTS.md`：评测达标后，在目标入口加一处局部可选导入并挂载 `build_knowledge_tools()`；那一步本身也是一个独立变更。

## 红线变更

| # | 文件与条目 | 改什么 | 为什么必须改 | 影响面 | 怎么回退 |
| --- | --- | --- | --- | --- | --- |
| 1 | `ae_harness/AGENTS.md` 第 11 条 | 「禁止引入…向量、知识库」→ 允许**只读检索**；明确知识库在根级 `knowledge/`，禁止在 Harness 内做文档上传与知识库写接口 | 不放开则新模块一落地即违规 | 纯条文 | revert 条文 + 删 `knowledge/` |
| 2 | `ae_harness/AGENTS.md` 目录结构与职责表 | 增 `knowledge/` 一行 | 目录表是 Harness 的地图，缺行会让后来者找不到模块 | 纯文档 | revert |
| 3 | `ae_harness/agents/AGENTS.md` 第 6 条 | 「禁止引入…向量、知识库」→ 允许调用方挂知识库**检索工具**；工具仍不算角色第四要素 | 同上 | 纯条文 | revert |
| 4 | `ae_harness/agents/AGENTS.md` 第 3 条 | 「禁止在 `agents/` 以外读配置文件」收窄为**只禁止读 `agents/config/models.yaml` 与 `prompts/`**；其它模块自带配置由该模块自读 | 现条文按字面覆盖 `.env` 与「models.yaml」这两个通用名，会误伤知识库自带配置 | 纯条文，收窄而非放宽 | revert |
| 5 | `tools/AGENTS.md` 目录准入 | 新增约束：**只允许 Python 内置函数工具、Skill、MCP 三类**；知识库等带状态模块不属于本目录 | 需求方要求先把这个边界定下来 | 新增准入条款 | revert 该条 |

## 模块防火墙自检

- 知识库不 import `agents/` / `assistant/` / `event/` / `middleware/` / `workflow/` / `tools/`。
- Harness 其余模块不 import 知识库；唯一例外是执行者入口的可选导入。
- 不写业务数据库；索引只写 `knowledge/index/`（已 gitignore，可重建）。
- 前端不连接向量库，不新增页面。
- 引擎仍不 import `django` 或 `backend.apps`。

## Risks / Trade-offs

- [效果未知：可能命中不准，也可能该说「没有」时硬凑片段] → 本期不挂载任何角色；先补评测集与 Recall@k 基线（`tasks.md` 第 7 节），达标才接回。
- [删除知识库后 Harness 无任何变化] → 这正是本期目标：引用数为零。
- [首轮检索会现建索引，可能几十秒] → 用 `python -m engines.ae_harness.knowledge index <库名>` 预热；探针也是人工验收口。
- [SQLite 全表余弦扫描随资料增长变慢] → 当前资料 4 个文档、百级片段，够用；库边界已按 collection 分开，后续可换向量库。
- [与 `engines/agents/rag` 两份实现并存会漂移] → 明确记录为已知代价；差异只在配置来源与目录归属，算法链路两处都走 `KnowledgeBase`。

## Migration Plan

1. 改红线（先于代码），新增 `knowledge/` 目录与两份 yaml。
2. 实现配置 → 嵌入模型 → 向量库 → 索引 → 检索 → 工具，逐层可用。
3. 执行者入口加可选挂载。
4. 用探针跑通 `product_manuals`，确认命中后再跑真机会话。
5. 回退：删 `knowledge/` 目录 + revert 入口一处可选导入 + revert 条文；索引与配置随目录一起消失，无残留状态。

## Open Questions

无。
