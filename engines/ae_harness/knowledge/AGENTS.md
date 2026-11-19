# knowledge 模块 AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../AGENTS.md) → [`engines/ae_harness/AGENTS.md`](../AGENTS.md) → **本文件**。本文件只写知识库领域增量；冲突时本文件的领域规则优先。

## 职责

Harness 内的**独立知识库模块**：自带向量模型配置与库目录，按库增量索引，以只读工具形态提供检索。它不生成答案、不改写命中，也不决定结果给哪个角色——挂不挂、挂给谁由调用方决定。

| 文件 | 职责 |
| --- | --- |
| `config.py` | 读自带两份 yaml（向量模型、库目录），校验字段与资料目录隔离；密钥取值 |
| `models.py` | 按配置创建 DashScope 嵌入模型，交出密钥环境变量名 |
| `store.py` | `SQLiteVectorStore`：`VectorStoreBase` 的本地实现，余弦相似度 |
| `indexer.py` | 只扫 `.md/.txt`，按修改时间/大小/切块版本增量重建 |
| `service.py` | `KnowledgeRetriever.retrieve()`：懒初始化，失败降级为「检索不可用」；`usage_events()` 交出嵌入用量 |
| `usage.py` | `UsageRecordingEmbedding`：透传嵌入调用并记录 token 用量事件；零 token 不产事件 |
| `tool.py` | `build_knowledge_tools()`：产出只读 `search_knowledge` 工具 |
| `probe.py` / `__main__.py` | 命令行探针 `index` / `retrieve`，不创建智能体、不调聊天模型 |
| `config/models.yaml` | **只允许**向量模型条目 |
| `config/knowledge_bases.yaml` | `defaults` + 各库 `description` / `data_dir` / `enabled` |
| `index/` | 生成的索引（已 gitignore，可随时重建） |

## 红线（禁止）

1. **禁止被 ae_harness 内其它子包 import** —— 挂载到 Agent 的效果评测完成前，Harness 内部引用数为零，由 `tests/engines/ae_harness/unit/test_knowledge_independence.py` 守护。评测达标要接回角色时，只允许在目标入口加一处局部可选导入，并同一提交里更新该测试的期望引用清单。**平台 backend 例外**（2026-11-18 变更申请获批，见 `openspec/specs/knowledge-search-entry` 与 `harness-knowledge`）：backend 可经局部可选导入使用只读检索与用量出口，不计入 Harness 内部引用，不得使本模块反向依赖平台。
2. **禁止 import Harness 其它子包** —— 不 import `agents/`、`assistant/`、`event/`、`middleware/`、`workflow/`、`tools/`。本模块要能整目录删除而不牵连任何一处。
3. **禁止把知识库放进 `tools/`** —— `tools/` 只收 Python 内置函数工具、Skill、MCP；带配置与状态的模块一律留在根级子包。
4. **`config/models.yaml` 只允许向量模型** —— 出现 chat / realtime / tts 字段即视为配置非法；不得改成「共用 agents 的模型表」。
5. **禁止只读以外的动作** —— 不写资料目录、不落盘截图、不发文档上传或知识库写接口。
6. **禁止把检索改写成生成** —— 工具只回片段与相似度，不做总结、不改写正文。
7. **禁止静默失败** —— 「没命中」与「检索不可用」必须给出不同文案，不能都显示成「没查到」。

## 依赖边界的代价（有意为之）

密钥取值（仓库根 `.env` → 进程环境）与 `agents/config.load_secret` 重复约十余行。这是**故意**的：红线 2 要求本模块不依赖 `agents/`，用一份小重复换整目录可删。

`.env` 全仓只有仓库根一份，本模块只读不写，也不得新增第二份 `.env`。

## 当前状态：未挂角色，平台只读检索桥已放行

**不接到任何角色**：只验证了能跑通（索引成功、命中字段齐全、三种返回文案正确），**准确率与召回率没测**。挂载到 Agent 前必须先过评测（Recall@k / MRR / 误命中率，评测能力见 `openspec/changes/add-knowledge-auto-eval`）。

**平台 backend 只读检索桥已放行**（2026-11-18 变更申请获批）：`backend/apps/knowledge_search` 经局部可选导入直调 `KnowledgeRetriever`，返回检索原文并取 `usage_events()` 入账；不造 Agent、不生成答案。整目录删除后平台降级为「检索不可用」，不炸入口。

## 如何接回 Agent（评测通过后再做）

控制台入口已删除。接回时在 `backend_bridge` 的目标装配函数里加一处局部可选导入并挂载：

```python
try:  # 知识库可选：整目录删除后自动跳过
    from engines.ae_harness.knowledge import build_knowledge_tools
except ModuleNotFoundError as exc:  # 只吞本模块的缺失，内部写错仍要抛
    if not (exc.name or "").startswith("engines.ae_harness.knowledge"):
        raise
    build_knowledge_tools = None

if build_knowledge_tools is not None:
    for tool in build_knowledge_tools():
        await agent.toolkit.add_tool(tool)
```

同时把 `test_knowledge_independence.py` 的期望引用清单从 `[]` 改成该入口的相对路径——改动必须是**显式**的，不允许静默放开。

## 快速验证

```powershell
# 配置装载
python -c "from engines.ae_harness.knowledge import build_knowledge_tools; print(len(build_knowledge_tools()))"

# 建索引（会现算嵌入，首次较慢）
python -m engines.ae_harness.knowledge index product_manuals

# 检索并打印原始命中
python -m engines.ae_harness.knowledge retrieve product_manuals "指示灯"

# 单测
python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_*.py -q
```

## 相关路径

| 用途 | 路径 |
| --- | --- |
| 上层 Harness 约束 | [`../AGENTS.md`](../AGENTS.md) |
| 工具目录准入 | [`../tools/AGENTS.md`](../tools/AGENTS.md) |
| 接回时的落点（当前未挂载） | `engines/backend_bridge/` 的目标装配函数 |
| 风格规范 | [`.agents/rules/engines-code-style.md`](../../../.agents/rules/engines-code-style.md) |
