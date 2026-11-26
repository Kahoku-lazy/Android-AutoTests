> 状态：打分实现已被 `add-engines-eval-layer` 取代。本单只保留「发布不看评分」与两张评分表（`ai_eval_scores` / `ai_eval_score_items`）。裁判、方法目录、`evaluate()`、官方看板、独立题库一律以那张单为准，本单不再描述另一套实现。

## Why

现在的评测是自研的「发布闸门」：真模型跑假世界 + 4 条手写规则，不通过就不许发布。它只回答「合规不合规」，不回答「好不好」——而作者改提示词、换模型时真正要的是**质量分**。这套自研实现还已经把自己锁死：样本集比较口径不一致、尺子把「守卫拦住」当违规，导致任何草稿都发不出去（实测 workflow 自测 `fingerprint` 完全一致仍判未通过）。

方向改为：**评测只打分，发布由人决定**。评分用 DeepEval 的 LLM 裁判，测两件事——提示词质量、交接文本质量；结果落库，供以后对比历史。

## What Changes

- **BREAKING**：发布不再依赖评测。名片与工作流的发布只校验「草稿 + 编辑权」；评测结果只作参考，MUST NOT 阻断发布。
- 删除自研评测：`ai_assistant_live_runs` / `ai_assistant_live_samples` / `ai_assistant_eval_runs` 三张表迁移删除；`live_runner` / `live_rulers` / `eval_rulers` / `eval_samples` / `eval_probe` / `fake_world` / `scripted` 一并移除；`POST /api/ai/evals/run/` 与 `GET /api/ai/evals/runs/{id}/` 下架。
- 引入 `deepeval`（4.3.5）作为评分框架，只做两件事：
  - 对草稿的**系统提示词**打质量分（0–1 + 理由）
  - 对一条**历史运行产物的交接文本**打质量分（0–1 + 理由）
- 判分模型用 DeepSeek：以 `DeepEvalBaseLLM` 子类接入（`deepseek-chat` + `DEEPSEEK_API_KEY`），并关闭 PostHog 遥测（`DEEPEVAL_TELEMETRY_OPT_OUT=1`）。
- 评分落库：新增 `ai_eval_scores`（一次评测一行）与 `ai_eval_score_items`（每指标一行），支持按目标查历史、按时间对比。
- 交接文本来源：从**已归档的运行产物**里选一条（助手取对话栏日志、工作流取任务报告），MUST NOT 为评分再跑一次真机。
- 前端：评测页从「通过/未通过」改为「评分卡 + 历史对比」；发布按钮旁显示最近评分，不阻断。
- 非目标：不做轨迹级指标（`ToolCorrectness` / `StepEfficiency`）、不接 Confident AI 云、不把评分写进 CI 闸门。

## 关联文档

无关联 PRD 编号：本变更是 AI 助手评测机制与发布流程的改造，不新增产品功能页，只替换评测实现与发布判定口径。

## Capabilities

### New Capabilities

- `assistant-eval-score`: 评测只产评分的契约——两项指标的判分口径（提示词质量、交接文本质量）、评分落库与历史对比、判分用量入账、以及「评分不阻断发布」。

### Modified Capabilities

- `assistant-eval`: 六条自测要求整条退役，改为一条「发布只校验草稿与编辑权」。
- `assistant-live-eval`: 真模型自测链路（假世界 + 四把尺子 + 逐样本过程 + 发布门禁）整体退役。

## Impact

- 代码：`backend/apps/ai_assistant/{models,api,views_drf,urls,services/*}.py`、`engines/backend_bridge/workflow/{eval_probe,fake_world}.py`、`engines/ae_harness/tools/scripted/`、`frontend/src/modules/ai-assistant/{evals.vue,api/assistants.ts,helpers/eval-view.ts,constants.ts}`。
- 数据库：删 3 张表（含历史自测记录）、新增 2 张评分表。
- 依赖：`requirements.txt` 新增 `deepeval>=4.3.5`（带 grpcio / opentelemetry / pytest 插件族，需评估安装体积）。
- 用量账本：判分调用单独来源标签入账（沿用 `usage_ledger.record_usage`）。
- 测试：`tests/ai_assistant/api/test_eval_run.py`、`test_release.py` 需按新口径重写；评测评分流程以灰盒用例覆盖。
