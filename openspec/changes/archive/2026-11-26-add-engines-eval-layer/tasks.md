## 1. 引擎层 `engines/eval`（原语）

- [x] 1.1 收紧 `engines/eval/{judge,methods,runner,__init__}.py`：`deepseek` 用官方 `DeepSeekModel`，`dashscope`/`openai` 用官方 `OpenAIModel(base_url=...)`，密钥在本包内读、关遥测，不手写 `DeepEvalBaseLLM`、不 import `ae_harness`；methods 目录 3 项，判定点作为固定 `evaluation_steps`（不传 `criteria`）；runner 调官方 `evaluate()` + `DisplayConfig(results_folder, file_type="html")`，同一次业务评分的第二次运行写 `results_subfolder`。验证：`python -m ruff check engines/eval` 通过，`list_methods()` 返回 3 项，且 `engines/eval` 内无 `ae_harness` import。
- [x] 1.2 用真实提示词跑一次 `run_evaluation`，确认产出 `test_run_*.json` 与看板 HTML 且能打开。验证：记录文件路径与打开截图。
- [x] 1.3 `.linting` 声明 `engines.eval`，`depends_on` 为空。验证：`python -m utils.check_gates --only linting` 通过。
- [x] 1.4 文档：新增 `.agents/docs/engines/eval/eval_deepeval_wrapper.md`，并在 `engines/AGENTS.md` 模块表登记。验证：`python -m temps.check_engines_doc_headers` 通过。

## 2. 桥接层 `engines/backend_bridge/eval`（业务合成）

- [x] 2.1 `case_run.py`：`compile_case_yaml(case)`（动作+断言+锚点 → SOP 步骤，`max_attempts=3`）与 `run_case(...)`（真机跑 → 步骤结论/交接/报告路径）。验证：用一条真题编译出的 YAML 能被 `load_spec` 读取。
- [x] 2.2 `scoring.py`：`run_single`（提示词与交接各一次 `evaluate()`，同一 `results_dir`，第二次用 `results_subfolder`）与 `run_suite`（逐题跑 → 组 `LLMTestCase` → 调 `engines.eval`）。验证：不连真机时，用桩 runner 跑 1 条用例能拿到两段路径字段与分数结构；真机验收留在 4.1。
- [x] 2.3 `engines/eval` 与 `backend_bridge/eval` 之外无 deepeval import。验证：全仓 grep `import deepeval` 只命中 `engines/eval`。

## 3. 后端：只调功能

- [x] 3.1 删 `services/score_judge.py`；`services/eval_scores.py` 瘦成薄翻译（候选运行、指纹、judge 绑定、落库、记账），打分逻辑走 `backend_bridge.eval`。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q` 无新增失败。
- [x] 3.2 重写 `services/eval_suite.py`：读新题库表，逐题调用 `backend_bridge.eval.run_case`，不再 import `case_manager`。验证：`linting` 违规清零。
- [x] 3.3 `api.create_eval_score` 补 `method_key/report_html/test_run_json`；接口补：`GET /api/ai/eval-methods/`、`GET/POST/PATCH/DELETE /api/ai/eval-cases/`、`POST/GET /api/ai/eval-runs/`、`GET /api/ai/eval-reports/<id>/`（看板文件流）。验证：OpenAPI 基线更新且各接口跑通。
- [x] 3.4 题库迁移：把 `case_manager` 项目 25 的 12 条题导入 `ai_eval_cases`/`ai_eval_case_steps`（含 anchor），删除该项目。验证：题库接口返回 12 条，项目列表不再有临时项目。

## 4. 前端

- [x] 4.1 评测页：方法卡（判定点全文）、裁判模型下拉、题库勾选、发起评测、逐题表（达成率/耗时/理由）、iframe 嵌官方看板、跨次趋势折线。验证：本地起前端跑 1 条真题，看板可显示。
- [x] 4.2 题库编辑页：题目与步骤的增删改（含 anchor）。验证：新增一条题后能被评测选中。
- [x] 4.3 发布入口：助手卡片、工作流卡片加「发布」；评测页顶部显示最近分数 + 发布按钮（不阻断）。验证：发布后 `release_state` 变 published，再发布被拒。

## 5. 收尾

- [x] 5.1 旧单 `score-assistant-with-deepeval` 收窄或作废，避免两套方案并存。验证：`openspec list` 里不再有互相矛盾的描述。
- [x] 5.2 门禁：`python -m run check`（`vitest`/`vite-build` 的既有 EPERM 注明）、`openspec validate --strict add-engines-eval-layer`、ruff/format、`linting`、`engines-agents-style` 全绿。
