## 1. 依赖与判分模型接入

- [x] 1.1 `requirements.txt` 加入 `deepeval>=4.3.5`；安装后确认 `python -c "import deepeval"` 可用，并确认 `python -m pytest -c tests/pytest.ini --collect-only -q` 的收集结果与安装前一致（DeepEval 自带 pytest 插件）。验证：两次收集条数相同。
- [x] 1.2 在评分服务里设 `DEEPEVAL_TELEMETRY_OPT_OUT=1` 并延迟 import `deepeval`（只在函数内 import）。验证：`python -m run check` 的 `django-check` 与 `pytest-collect` 仍通过，导入 `backend.apps.ai_assistant.api` 不触发 deepeval。
- [x] 1.3 实现 `DeepEvalBaseLLM` 子类接 DeepSeek：`get_model_name` / `load_model` / `generate(prompt, schema=None)` / `a_generate`，`schema` 存在时用 `response_format={"type":"json_object"}` 并由调用方校验成 Pydantic 实例。验证：一次性脚本对一句中文打分返回 0–1 分与理由。

## 2. 评分服务与两张表

- [x] 2.1 新增模型 `AssistantEvalScore` 与 `AssistantEvalScoreItem`（表名 `ai_eval_scores` / `ai_eval_score_items`，字段见 design），写迁移。验证：`python manage.py makemigrations --check` 无残留。
- [x] 2.2 实现两项指标的 `GEval` 定义：`prompt_quality`（角色清晰度 / 流程可执行 / 工具与约束明确 / 异常与收尾）与 `handover_quality`（做了什么 / 停在哪 / 下一步 / 有无臆造），`criteria` 用中文写、`evaluation_params` 取 `INPUT` + `ACTUAL_OUTPUT`。验证：对同一条历史交接文本连打两次分，两次都有分数与理由。
- [x] 2.3 评分主流程：取草稿 → 算 `prompt_fingerprint` → 打分 → 落 run + item 两表；任一指标失败时该指标记缺失与原因，另一项照常落库。验证：伪造一次判分异常，评分接口仍返回另一项分数且落库一条 run。
- [x] 2.4 判分用量入账：`usage_ledger.record_usage(source="assistant_eval_judge")`，`event_id` 带 run id 与指标名保证幂等，异常只记日志。验证：连续两次评测同一草稿产生两条 run、入账事件 id 不重复。

## 3. 历史运行产物的选取

- [x] 3.1 实现候选列表：助手从对话栏日志目录取最近 N 条（`logs/agents/assistants/<assistant_id>/<thread_id>/<stamp>/`，读 `.aligned.json` 的 `summary.final_text`），工作流从任务报告目录取最近 N 条。验证：接口返回带时间与摘要的候选，且不读全量 JSON（只读 summary 段）。
- [x] 3.2 实现 `source_ref` 解析：把候选标识还原成一份交接文本；文件不存在或没有 `final_text` 时返回可读原因。验证：删掉一个候选目录后请求评分，接口说明该运行已不可用。

## 4. 接口与发布解绑

- [x] 4.1 新增 `POST /api/ai/eval-scores/`、`GET /api/ai/eval-scores/`、`GET /api/ai/eval-candidates/`（需 author 权限，信封 `{status, data}`）。验证：三个端点各跑一次，响应符合信封与 snake_case。
- [x] 4.2 下架 `POST /api/ai/evals/run/` 与 `GET /api/ai/evals/runs/{id}/`。验证：两路径返回 404，OpenAPI 里不再出现。
- [x] 4.3 解绑发布闸门：`AssistantPublishView` 与 `WorkflowPublishView` 删除 `eval_passed` 校验，只留草稿与编辑权检查。验证：灰盒用例——低分/未评测都能发布，非作者仍 403/400。

## 5. 删除旧自测机制

- [x] 5.1 删代码：`services/live_runner.py`、`live_rulers.py`、`eval_rulers.py`、`eval_samples.py`、`eval_billing.py`（判分入账改写进新服务）、`engines/backend_bridge/workflow/eval_probe.py`、`fake_world.py`、`engines/ae_harness/tools/scripted/`。验证：全仓 grep `live_runner|live_rulers|eval_probe|fake_world|scripted_tool` 零命中。
- [x] 5.2 删模型与迁移：`AssistantLiveRun`、`AssistantLiveSample`、`AssistantEvalRun` 及其表 `ai_assistant_live_runs` / `ai_assistant_live_samples` / `ai_assistant_eval_runs`。验证：`makemigrations --check` 干净，`python manage.py showmigrations ai_assistant` 无待应用。
- [x] 5.3 更新 `openspec/specs/assistant-eval/spec.md` 的 Purpose（原文是「五把纯函数尺子」，已不成立）。验证：`openspec validate --strict` 通过。

## 6. 前端

- [x] 6.1 重写 `frontend/src/modules/ai-assistant/evals.vue`：目标选择 → 运行产物选择 → 发起评分 → 评分卡（两项指标分数 + 理由 + 判分模型 + 时刻）→ 历史列表。验证：本地起前端跑一次评分，页面显示分数与理由。
- [x] 6.2 历史对比展示：同一目标的历史评分按时间倒序，至少能看出同一指标的趋势。验证：连续评两次后页面出现两条记录与趋势。
- [x] 6.3 去掉判定文案：`helpers/eval-view.ts` 的 `evalVerdict` / `EVAL_PASSED` / `EVAL_FAILED` 删除；发布按钮旁若显示分数，MUST 不禁用按钮。验证：前端测试与 eslint 通过，页面无「通过/未通过」字样。

## 7. 测试、文档与门禁

- [x] 7.1 重写 `tests/ai_assistant/api/test_eval_run.py` 为评分用例（发起评分 → 两条 item 落库 → 历史接口返回两条）；`test_release.py` 覆盖「低分也能发布 / 未评测也能发布 / 非作者不能发布」。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 通过（既有 16 项鉴权失败与本变更无关，结果注明）。
- [x] 7.2 更新 `.agents/docs/apps/ai_assistant/ai_assistant_agent_config_and_cards.md`：评测口径改为「只评分不闸门」、两张评分表、判分模型与用量来源标签。
- [x] 7.3 门禁：`python -m run check`（vitest/vite-build 因本机 EPERM 的既有情况注明）、`openspec validate --strict score-assistant-with-deepeval`、`python -m ruff check` + `ruff format --check`。

## 8. 真题集（已被 add-engines-eval-layer 取代：题库改为独立表，不再挂用例库）

- [x] 8.1 把 D:\Govee\data\H6810\H6810_ui_only_cases.yaml 导入用例库的自动化项目「H6810 真题集（UI 验证）」：ssert 映射为 ssertion、保留 nchor、usiness_type=lighting；验证：项目下 12 条用例、标题与步数与 YAML 一致。
- [x] 8.2 真题集服务 services/eval_suite.py：逐条 compile_automation_cases → load_spec → 
un_bound_sop 真机执行；逐条记步骤达成、尝试次数、耗时、失败说明、交接文本判分；汇总落 i_eval_scores（suite_pass_rate / suite_handover_avg）与 i_eval_case_results。验证：真机跑 1 条用例，两条指标与逐条明细都落库。
- [x] 8.3 接口：GET /api/ai/eval-suite-projects/（项目 + 用例）、POST /api/ai/eval-suite-scores/（发起真题集评测）、GET /api/ai/eval-suite-scores/（历史）。验证：三接口各调一次，信封与字段齐全。
- [x] 8.4 执行前设备校验：
equire_online 在编译用例之前调用；验证：传未连接序列号时拒绝且不产生执行记录。
- [ ] 8.5 **已被取代，不在本单关单范围**（2026-11-26 核对：dd-engines-eval-layer 已归档，真题集改为独立题库表与自有页面）。原任务：前端：评测页加「真题集」页签（选项目 → 勾选用例 → 发起 → 逐条结果表 + 历史）。验证：本地起前端跑 1 条，表格出现该条达成率与交接分。
- [ ] 8.6 **已被取代，不在本单关单范围**（同上；且原前置为真机登录 Govee Home + H6810 配对）。原任务：全量 12 条真跑一次并记录基线分数（前置：Govee Home 已登录且 H6810 已配对；当前实测因未登录，设备列表为空，第 1 条即失败）。
