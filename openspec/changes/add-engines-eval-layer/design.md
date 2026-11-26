## Context

引擎层现有 `ae_harness`（Agent 原语）、`backend_bridge`（平台角色装配）、`device` / `uart_log` / `vision`（底座）。评测此前无处安放，被塞进 `backend/apps/ai_assistant/services/`：直接 import deepeval、自己算 pass_rate、自己跑 SOP，违反「AI 助手只调用功能」。

同时评测题错挂 `case_manager`（任务用例库），触发 `.linting` 违规 `ai_assistant → case_manager`；可视化靠手工统计，而 deepeval 官方 `DisplayConfig(file_type="html")` 已能导出评测看板。

## Goals / Non-Goals

**Goals**

1. `engines/eval` 作为与 `ae_harness` 同级的原语层，封装 deepeval。
2. `engines/backend_bridge/eval` 合成业务：题目→SOP 编译、真机跑、组样本、调引擎。
3. AI 助手只调 `backend_bridge`，零 deepeval、零打分逻辑。
4. 题库独立成表，与用例库解耦。

**Non-Goals**

1. 轨迹级指标（`@observe` 埋点）不在本单。
2. 不接 Confident AI 云；不做 CI 闸门。

## Decisions

**D1 `engines.eval` 与 `ae_harness` 同级，而非 `ae_harness.eval`。** 二者都是外部框架的封装层（AgentScope / deepeval），并列更符合「一个包一个外部框架」的心智；`ae_harness` 不需要知道 deepeval。

**D2 `engines.eval` 不依赖 `engines.ae_harness`。** 二者同级且互不 import，与 `ae-harness-isolation` 一致。`.linting` 登记 `engines.eval`，`depends_on` 为空。密钥不复用 `load_secret`：在 `judge.py` 内用 `dotenv` 读 `.env`，再回退 `os.environ`。备选「为复用十余行密钥读取拉一条引擎边」被否：会把两个外部框架封装绑在一起。

**D3 打分只走官方 `evaluate()`，不自研。** 用 `evaluate(test_cases, [metric], AsyncConfig(run_async=False), DisplayConfig(results_folder, file_type="html", file_output_dir, print_results=False))`；返回每例 score/reason + 看板 HTML + `test_run_*.json`。理由：自研会与官方看板重复且难维护。

**D3b 裁判用官方模型类，不手写 `DeepEvalBaseLLM`。** `deepseek` 用 `DeepSeekModel(model, api_key, temperature=0)`（端点由官方固定为 `https://api.deepseek.com`）；`dashscope` / `openai` 用 `OpenAIModel(model, api_key, base_url, temperature=0)`。调用方仍传厂商、密钥环境变量名、模型名、可选端点；引擎不读平台配置表。用量取官方返回，不自记 token。

**D3c 判定点写成固定 `evaluation_steps`，不传 `criteria`。** 官方二者只能留一个；只传 `criteria` 时 GEval 每次重新生成步骤，分数会漂。方法目录对外展示的判定点文本与实际打分步骤是同一份。

**D4 用例→SOP 编译放 `backend_bridge`。** 编译需要 SOP 抽象（步骤/重试/验收），属于业务编排；`engines/eval` 只认「样本」不认「SOP」。

**D5 真机执行由调用方注入。** `run_suite` 接受 `runner` 回调（backend 传 `run_case(...)`），使 `backend_bridge/eval` 不依赖平台绑定逻辑。

**D6 一次业务评分、两次官方运行、同一结果目录。** `LLMTestCase` 没有「每条样本挂自己的 metric」；一次 `evaluate()` 的 metrics 整批共用，做不到「一个看板两行」。提示词与交接各跑一次 `evaluate()`，第二次用 `DisplayConfig.results_subfolder` 落在同一 `results_dir` 下。业务记录两份看板路径，页面以交接那次为主、提示词那次可切换。不为「合成一个看板」改 deepeval。

**D7 可视化：单次详情用官方看板 iframe，跨次趋势自研。** 官方看板只管单次运行；跨运行对比是自己的一张小折线。

## 数据模型（backend 侧，已建表）

```text
ai_eval_cases / ai_eval_case_steps   独立题库（UI 执行专用，可编辑）
ai_eval_scores                       一次运行：method_key、judge 模型、report_html、test_run_json
ai_eval_score_items                  每指标分数/理由/阈值
ai_eval_case_results                 逐题：达成步数/尝试/耗时/score/reason/失败步骤
```

## Risks / Trade-offs

1. **官方看板是单次运行**：跨次对比需自研折线；且看板样式不受我们控制。
2. **deepeval 依赖重量**：`grpcio`/`otel`/pytest 插件族，且把 `click` 钉在 `<8.4.0`（与 `huggingface-hub` 冲突）——只能延迟 import + 关遥测，后续可考虑独立 venv。
3. **同进程跑 evaluate 会阻塞请求**：真题集会跑几分钟到十几分钟，接口需要后台任务与状态轮询（本单先做同步 + 前端 loading，长任务另开）。
4. **判分不确定**：只作参考、看趋势。

## Migration Plan

1. 建 `engines/eval`（judge/methods/runner）→ 用真实提示词跑一次，确认产出看板。
2. 建 `engines/backend_bridge/eval`（case_run/scoring）→ 删 backend 三个 service 的实现部分，保留薄翻译。
3. backend：题库迁移（case_manager 项目 25 的 12 条 → 新表，删项目）、接口（methods/cases/runs/reports）、看板文件流。
4. frontend：方法卡 + 裁判下拉 + 题库编辑 + 发起 + iframe 看板 + 趋势 + 发布按钮。
5. 回退：删两个新包 + 恢复旧 service 即回到当前状态（旧 service 未删干净前可快速回退）。

## Open Questions

无。轨迹指标与后台长任务已明确排除在本单。
