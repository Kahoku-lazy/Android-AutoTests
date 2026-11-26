# ai_assistant · Agent 配置与助手名片

> 归属模块：`backend/apps/ai_assistant` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/ai_assistant/models.py`、`api.py`、`views_drf.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

用 **Agent 配置** 和 **模型配置** 创建 Agent 角色。模型配置只登记创建模型需要的连接参数，
不在这里造模型实例；Agent 配置登记名称、一条模型配置和系统提示词。

## 助手名片

名片是另一张表 `ai_assistants`：显示名、压缩头像、笔色、对 `role_id` 的引用、工具勾选。
**不复制提示词和模型参数。** 编号是 `YYYYMMDD_XXX`（大写），与 `role_id` 分开。

## 对话与快照

- 测试对话在 `ai_assistant_threads` / `ai_assistant_messages`。
- 打开对话**不跑模型**；首次发送才把当时名片冻成 snapshot，交给 `backend_bridge`。
- 改名片**不改**已经发送过的栏。
- **SOP 不读这些对话栏。**

## 评测：只评分，不闸门

评测用 DeepEval 的 LLM 裁判（`GEval` + `deepseek-chat`）给两件事打分，各 0–1 分并附理由：

| 指标 | 评什么 | 输入 |
| --- | --- | --- |
| `prompt_quality` | 角色是否清楚、流程是否可执行、工具与约束是否明确、异常与收尾是否交代 | 执行角色的系统提示词正文 |
| `handover_quality` | 做了什么、停在哪、下一步从哪开始、有无臆造 | 一条历史运行产物的 `summary.final_text` |

- 落库两张表：`ai_eval_scores`（一次评测一行：目标、提示词指纹、来源运行、判分模型、时刻）与 `ai_eval_score_items`（每指标一行：分数、理由、阈值）。**历史按目标可查，供改提示词前后对比。**
- 交接文本来自**已归档运行产物**（助手取 `logs/agents/assistants/**`、工作流取 `logs/agents/backend_bridge/**`），评测本身不跑真机。
- 判分调用单独入账：`usage_ledger` 的 `source="assistant_eval_judge"`，`event_id` 带评分行 id 与序号做幂等。
- **发布不看评分**：名片与工作流只校验「草稿 + 编辑权」；评分只作参考。旧的自研自测（固定剧本 + 四把尺子 + 假世界）与三张表已删除。
- 接口：`POST /api/ai/eval-scores/`（发起评分，同步返回）、`GET /api/ai/eval-scores/`（历史）、`GET /api/ai/eval-candidates/`（可选运行产物）。
- 依赖：`deepeval>=4.3.5` 只在评分服务里延迟 import，并设 `DEEPEVAL_TELEMETRY_OPT_OUT=1`；它把 `click` 钉在 `<8.4.0`，与 `huggingface-hub`（cnstd→OCR）的下限冲突，属已知代价。

## 分层纪律

**写库入口只在 `api.py`** —— View / Tool 一律经 `api.py` 落库，View 直写 ORM 属违规。
落库的**实现层在 `services/`**（`agent_configs.py` / `assistant_cards.py` / `assistant_threads.py` 等），
由 `api.py` 调用，不直接对外。
全局的写库路径与信封规则见 `backend/AGENTS.md` §1.1、§1.3。
