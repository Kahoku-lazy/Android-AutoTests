## 1. 平台数据

- [x] 1.1 `ai_model_configs` 增加可空 `dimensions`，`model_kind` 接受 `embedding`；迁移在不存在 `DASHSCOPE_API_KEY + text-embedding-v4` 时插入一条向量模型（dashscope、维度 1024），已存在则不覆盖。验证：`python manage.py makemigrations --check` 无差异，临时库迁移后恰好一条该模型。
- [x] 1.2 新建 `ks_retrieval_settings`（`embedding_model_id`、`top_k`、`score_threshold`、`chunk_size`、`chunk_overlap`、`index_epoch`），种子为 4 / 0.45 / 400 / 60 / epoch 0，并指向 1.1 的向量模型。验证：`tests/knowledge_search` 断言种子值是 0.45 而不是 0.55。
- [x] 1.3 `knowledge_search/api.py` 增加检索配置的读取与保存：校验阈值 0~1、切块大小大于重叠、引用模型存在且 `model_kind=embedding`；切块参数变化时 `index_epoch` 加一，其余修改不加。验证：`tests/knowledge_search/unit` 覆盖合法保存、非法阈值、引用聊天模型、只改阈值 epoch 不变。
- [x] 1.4 `ai_assistant` 删除模型配置前只读检查 `RetrievalSettings` 引用，被引用时拒绝并给出可读原因。验证：`tests/ai_assistant` 删除被引用向量模型失败且行仍在，删除未被引用的模型成功。

## 2. 引擎改为接收参数

- [x] 2.1 `knowledge/config.py` 的 `load_config` 改为 `build_config(embedding, bases, **检索参数)`，保留向量模型字段白名单、库名正则与启用库目录隔离；删除 `MODELS_PATH`、`BASES_PATH` 与读 yaml。验证：`tests/engines/ae_harness/unit/test_knowledge_config.py` 改为传参，混入 chat 字段与目录冲突仍失败。
- [x] 2.2 检索服务、索引器与探针改为使用 `build_config`；探针必填模型名、维度、密钥环境变量名、库名、资料目录，缺参非零退出，无命中仍为零退出。验证：`tests/engines/ae_harness/unit/test_knowledge_*.py` 通过，且 `knowledge/` 下不再出现 `models.yaml` / `knowledge_bases.yaml` 路径字面量。
- [x] 2.3 删除 `engines/ae_harness/knowledge/config/models.yaml` 与 `knowledge_bases.yaml`。验证：两文件不存在，`python -c "import engines.ae_harness.knowledge"` 不读任何 yaml。

## 3. 平台链路改读平台配置

- [x] 3.1 `retrieval.py` 停止调用 `registry.sync_yaml()`，改为读取检索配置与模块行，组装参数传给 `build_config`；检索前比对每库索引标记与 `index_epoch`，不一致时该库返回「需重建索引」。验证：`tests/knowledge_search/unit/test_retrieval.py` 在无引擎 yaml 时仍能检索，epoch 变化后返回不可用文案。
- [x] 3.2 预建索引成功后写入当前 `index_epoch`；评测触发改为冻结模块行与检索配置 JSON，不再冻结 yaml。验证：`tests/knowledge_search/integration` 重建后标记等于当前 epoch，评测运行不依赖 `KNOWLEDGE_SEARCH_BASES_FILE`。
- [x] 3.3 删除 `registry.py` 的 yaml 派生、`KNOWLEDGE_SEARCH_BASES_FILE` 与 `engine_bases_file`。验证：`grep -rn "knowledge_bases.yaml" backend engines` 无输出，`python manage.py check` 通过。
- [x] 3.4 Agent 配置保存与评测触发拒绝非 `chat` 模型；模型列表增加按 `model_kind` 过滤，对话可选列表只返回 `chat`。验证：`tests/ai_assistant` 绑定向量模型返回可读错误且原绑定不变。

## 4. 前端

- [x] 4.1 运营模型配置页增加「向量」类型：厂商仅 dashscope，显示维度、隐藏地址与音色，列表 chip 与副行展示维度。验证：`cd frontend && npx vitest run tests/ops-console` 与 `npm run typecheck` 通过。
- [x] 4.2 知识库页增加检索配置（仅超管可改）：向量模型下拉只含 `embedding`、四个检索参数、保存后展示是否需要重建。验证：`cd frontend && npx vitest run tests/knowledge-search` 与 `npm run typecheck` 通过。

## 5. 日志关键词退役

- [x] 5.1 删除 `engines/ae_harness/agents/config/log_keywords/`、`agents/config.py` 与 `tests/engines/ae_harness/unit/test_agents_config.py`。验证：`grep -rn "load_log_keywords" engines tests` 无输出，`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit -q` 通过。

## 6. 规则与收尾

- [x] 6.1 同一提交更新 `knowledge/AGENTS.md` 红线 4、`agents/AGENTS.md` 的日志关键词职责、`ae_harness/AGENTS.md` 里 `knowledge/config/` 豁免句，范围只限 design.md 决策 6 点名的句子。验证：`git diff` 中这三份文件没有决策 6 之外的条款改动。
- [x] 6.2 跑本地门禁 `python run.py check`，并 `python utils/gen_arch_stats.py --check-boundaries`。验证：两条命令退出码均为 0。
  **2026-11-23 实测**：`--check-boundaries` **退出码 0，零违规**；`run.py check` **28/30 通过**（告警项 3/3）。
  - 本变更为其转绿而修的四项：`ruff-engines-format`（`engines/ae_harness/knowledge/models.py` 格式化）、`openapi-schema` + `openapi-coverage`（基线补 `/api/knowledge-search/settings/`，+88/−0 行）、`vue-tsc` + `prettier`（`RetrievalSettingsCard.vue` 导入路径 `@/shared/utils/api-error` → `@/shared/types/api-error`、`save()` 按信封取 `saved.status/saved.data`；两文件 `prettier --write`）。
  - **仍红 2 项，均为本机环境 EPERM，非代码**：`vitest`（`EPERM mkdir C:\Users\...\Temp\...\client`）、`vite-build`（`EPERM copyfile frontend\public\brand\ai-mark.png -> frontend\dist\brand\ai-mark.png`）；`frontend/dist` 根目录实测可写，失败点在临时目录与静态资源拷贝，属本机沙箱限制，CI 上不复现。
  - 需求方 2026-11-23 决定：外部 6 处（4 个未跟踪测试文件的 I001 + `task_runner.py`、`test_bound_team.py` 的格式）修掉后直接关单。
