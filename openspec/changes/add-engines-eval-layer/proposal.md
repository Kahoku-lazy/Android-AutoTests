## Why

评测能力此前被写进 `backend/apps/ai_assistant/services/`（直接 import deepeval、自己算分、自己跑 SOP），违反分层：AI 助手只应调用功能。同时评测题错挂在 `case_manager` 用例库上（评测题不该被任务引用），可视化靠自研，而官方已提供评测看板 HTML 导出。

## What Changes

- 新增**独立引擎层** `engines/eval/`：与 `ae_harness` 同级、互不 import，专门封装 deepeval——用官方 `DeepSeekModel` / `OpenAIModel` 做裁判、方法目录、`evaluate()` 运行与官方看板导出。**全仓只有这一层 import deepeval**。
- 新增业务合成层 `engines/backend_bridge/eval/`：评测题 → SOP 编译、真机执行、组 `LLMTestCase`、调 `engines.eval` 打分。
- 评测题库改为**独立两张表**（`ai_eval_cases` / `ai_eval_case_steps`），只服务 UI 执行类评测，**不与用例库共享**、可编辑、数据独立。
- 评测裁判由平台选：从「模型配置」里挑，运行时交给 `engines.eval` 构造 `DeepEvalBaseLLM`。
- 可视化以**官方看板 HTML** 为主（`DisplayConfig(results_folder, file_type="html")`），平台 iframe 展示；平台只自研「跨次趋势」。
- 前端补「发布」入口（名片与工作流），评测页顶部显示最近分数并可发布；发布仍不看评分。
- 删除：`services/score_judge.py`（上移引擎）、`services/eval_suite.py` 的 `case_manager` 依赖、`case_manager` 里的临时题库项目。
- 非目标：轨迹级指标（`@observe` 埋点）、Confident AI 云端、CI 闸门。

## 关联文档

无关联 PRD 编号：本变更是引擎分层与评测实现的收敛，不新增产品页面之外的功能。

## Capabilities

### New Capabilities

- `engines-eval-dashboard`: 引擎侧评测能力契约——裁判适配、方法目录（含判定点文本）、一次运行产出一个官方看板与结构化结果。

### Modified Capabilities

- `assistant-eval-score`: 题库改为独立表（不复用用例库）、评测方法/裁判由平台选、看板与趋势展示、发布入口。

## Impact

- 代码：`engines/eval/**`（新）、`engines/backend_bridge/eval/**`（新）、`backend/apps/ai_assistant/{models,api,views_drf,urls,services}`、`frontend/src/modules/ai-assistant/**`。
- 依赖：`deepeval>=4.3.5` 只允许在 `engines/eval` 内 import；`.linting` 新增 `engines.eval` 模块，`depends_on` 为空（不依赖 `engines.ae_harness`）。密钥在本包内用 `dotenv` + 环境变量读取。
- 数据库：沿用已建表（`ai_eval_cases`/`ai_eval_case_steps`/`ai_eval_scores`/`ai_eval_score_items`/`ai_eval_case_results`），本次只补字段与数据迁移。
- 产物：`logs/agents/eval_scores/<目标>/<时间戳>/` 下的官方看板 HTML 与 `test_run_*.json`。
