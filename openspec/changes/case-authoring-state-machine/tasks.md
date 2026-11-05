## 1. 产物契约与存储（引擎侧）

- [x] 1.1 新增产物数据契约：状态机（`states` / `transitions`）、场景、用例、边界项的数据类与必填/长度约束（title ≤200、source ≤500、每步 ≤200），结构非法时抛可读错误；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_artifact.py -q`
- [x] 1.2 实现 `ArtifactStore`：按任务保存三段产物与编写报告，提供 `put_state_machine` / `append_scenarios` / `append_cases` / `read`，单批 ≤20 条、超限报错不落半份；验证：同文件用例覆盖「分批累计」「非法批次原子不写入」
- [x] 1.3 把 4 个增量工具接到角色工具包（`save_state_machine` / `append_scenarios` / `append_cases` / `read_artifact`），返回只回「本次条数 + 累计条数」，不回显内容；验证：`tests/graybox/unit/test_case_artifact_tools.py` 断言返回值不含正文
- [x] 1.4 工具只允许写当前任务、`read_artifact` 对验收角色只读且支持 `counts_only`；验证：单测断言越权写入与只读工具被拒

## 2. 事实预检

- [x] 2.1 实现「出处真实」校验：`source` 归一空白后必须是需求正文子串，失败项给出条目编号与最接近的原文片段；验证：`tests/graybox/unit/test_case_artifact_facts.py` 覆盖「1600 万色 vs 16 万色」
- [x] 2.2 实现「引用完整」校验：用例 `pre_state`/`expect_state`/`scenario_id` 与迁移 `from`/`to` 必须已声明；验证：单测覆盖悬空引用并给出首次出现位置
- [x] 2.3 实现「数值可追溯」校验：抽取用例与边界项中的整数、百分比、时间、时长，必须出现在自身 `source` 或某条边界 `source` 里；验证：单测覆盖「3 秒内」但 source 无 3
- [x] 2.4 输出结构固定为 `{blocking: [...], warnings: [...]}`，迁移覆盖率只进 `warnings`；验证：单测断言覆盖率不足不产生 blocking
- [x] 2.5 把预检暴露为只读工具 `check_artifact_facts` 并加入验收工具包；验证：`tests/graybox/unit/test_case_artifact_tools.py` 断言验收有、编写无

## 3. 渲染器

- [x] 3.1 实现 Markdown 渲染：状态机摘要 + 场景表 + 用例表（含 `source`），顺序固定；验证：`tests/graybox/unit/test_case_artifact_render.py` 断言三节顺序与行数
- [x] 3.2 实现 Mermaid `stateDiagram-v2` 渲染：状态用 `id`、迁移用 `event` 标注，含 `guard` 时以条件标签输出；验证：单测断言迁移条数一致、非法 id 被转义
- [x] 3.3 渲染只读产物、不写回；产物变化后重渲染结果随之变化；验证：单测覆盖「改产物 → 文档与图同步变化」

## 4. 编排切换（单条目标流水线）

- [x] 4.1 新增 `run_case_authoring_artifact(requirement, ...)`：`GoalPipeline(writer, verifier, verifier_reset_context=True, max_iters=3, max_retries=3)`，执行者只构建一次，结束返回产物 + 预检 + 判决；验证：`tests/graybox/unit/test_case_goal_workflow.py` 重写后断言执行者只构建一次
- [x] 4.2 驳回轮次不再把上一版产物全文拼进输入（依赖 `GoalPipeline` 的 system 反馈）；验证：单测断言第二轮输入不含上一版全文
- [x] 4.3 失败兜底：3 轮仍 fail 或连续 3 次无合法结构化输出时返回 `failed` + 可读 `reason`，保留最后产物与全部判决；验证：单测覆盖两条失败路径
- [x] 4.4 删除双轨与旧兜底：移除 `case_authoring_workflow.py`（SOP 分支）、`case_module_plan.py`、`case_document_check.py` 及相关测试；验证：`python run.py check` 无残留引用（`ruff check engines` 通过）
- [x] 4.5 调整 `ReActConfig`：编写角色 `max_iters` 20 → 60（增量工具轮次），验收角色维持 4；验证：`tests/graybox/unit/test_case_authoring_roles.py` 断言两项配置值

## 5. 角色与提示词（5 → 2）

- [x] 5.1 `agent_config.yaml` 只保留 `CASE_WRITER_ROLE_CONFIG` 与 `CASE_VERIFIER_ROLE_CONFIG`，删除 planner 与两个 Goal 变体；验证：`python -c "import engines.agents.agent_builders as b; b.build_case_writer(); b.build_case_verifier()"` 成功且 `build_case_planner` 已不存在
- [x] 5.2 重写 `CASE_WRITER_PROMPT.md`：三段式（状态机 → 场景 → 用例）+ 工具交付协议 + 「不写代码/不编造/未给数值登记待确认」铁律；验证：`tests/graybox/unit/test_case_authoring_prompts.py` 断言含三节标题与四个工具名
- [x] 5.3 重写 `CASE_VERIFIER_PROMPT.md`：只判「数据一致」与「无捏造」，必须先调 `check_artifact_facts`，禁止以覆盖率/字段数/方法数驳回；验证：同文件断言含两句禁则
- [x] 5.4 删除 `CASE_WRITER_GOAL_PROMPT.md`、`CASE_VERIFIER_GOAL_PROMPT.md`、`CASE_MODULE_PLANNER_PROMPT.md`；验证：`tests/graybox/unit/test_case_authoring_prompts.py` 断言三个文件不存在

## 6. 任务链路（backend）

- [x] 6.1 `task_runner._run_case_authoring` 改调新流水线，`Task.result` 写 `artifact` / `facts` / `verdicts` / `document` / `reason`，不再写 `modules` 与 `truncated`；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_authoring_task_runner.py -q`
- [x] 6.2 入库来源改为产物用例：`id` / `title` / `priority` / `pre_state` / `steps`（action → expect_state 状态名）/ `scenario_id` / `source`，`module` 取场景标题；验证：`tests/graybox/unit/test_case_import.py` 断言落库步骤的期望侧是状态名
- [x] 6.3 `task_reports._case_authoring_flow` 对缺 `modules` 的历史结果做空值兜底，并下发 `artifact` 计数（states/transitions/scenarios/cases）与 `facts`；验证：`tests/graybox/unit/test_task_case_authoring.py` 断言旧结果不报错、新结果带三组计数
- [x] 6.4 `case_manager.api_import` 接收新字段并保持幂等（`source_task_id`）；验证：`tests/graybox/unit/test_case_definitions_api.py` 通过

## 7. 前端（最小适配）

- [x] 7.1 用例编写任务结论区展示「状态 / 迁移 / 场景 / 用例」四个计数与预检结论（blocking/warnings 数），移除模块清单相关类型；验证：`npm run build` 与 `npm run lint:styles` 通过
- [x] 7.2 报告里 `artifact` 缺失（历史任务）时不渲染该区块，不报错；验证：更新 `frontend/tests` 中用例编写报告的用例并跑 `npm run test:unit`

## 8. 门禁与端到端

- [x] 8.1 跑 `python run.py check`（23 项阻塞项）与 `python utils/gen_arch_stats.py --check-boundaries`；验证：两条命令退出码 0
- [x] 8.2 用一份真实需求（H6810 或 H717D 规格）跑通一次用例编写任务，人工核对：三段产物齐全、预检无 blocking、判决与产物一致、用例库可查；验证：任务详情报告 + 用例库页面
- [x] 8.3 故意投喂一份含捏造数值的需求用例（改一处 source 或数值）验证预检与验收能拦下；验证：任务判 `failed` 且 `reason` 点名该条
- [x] 8.4 更新 `dev_docs/DEV_TEST/UI自动化 问题记录.md` 中「用例与锚点」一节，记录新流程与已知限制；验证：文档评审通过
