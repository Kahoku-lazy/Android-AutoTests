## 1. 用例步骤的结构化字段

- [x] 1.1 `engines/agents/workflow/case_file.py`：`CaseStep` 增可选 `anchor`（`page`/`entry`/`target`）与 `log`（`sku`/`port`/`keyword`），`parse_cases` 增加解析与校验（未知 anchor 键、`port` 非正整数、`keyword` 为空都要拒绝并给出可读原因），无这两个键时行为不变；验证：`test_case_step_fields.py` 6 条通过。
- [x] 1.2 新建 `engines/agents/workflow/step_brief.py`：`executor_brief`（`action` + 【本步页面锚点】）、`verifier_brief`（`expected` + 【本步日志证据】 + 【本步关键词表】）、`with_context`（开场上下文重放），保证执行者简报不含 `expected`、验收简报不含 `action`/`anchor`；验证：`test_step_brief.py` 6 条通过。
- [x] 1.3 新增 `tests/graybox/unit/test_step_brief.py` 与 `test_case_step_fields.py`：覆盖「anchor 只进执行者」「log 只进验收者」「无字段时逐字同旧行为」「非法字段被拒」；验证：两文件 12 条通过。

## 2. 按型号的日志关键词目录

- [x] 2.1 新建 `engines/agents/config/data/log_keywords/H6810.md`：按「功能点 → 关键词」列出设备开关 / 亮度 / 灯效 / 场景 / 音乐 / DIY / 定时（含 `timer_configs_set_success`、`awaken_configs_set_success`、`sleep_configs_set_success`）；验证：文件 43 行，装载长度 877 字符。
- [x] 2.2 新建 `engines/agents/config/log_keywords.py`：`load_log_keywords(sku) -> str`，只读 `config/data/log_keywords/<SKU>.md`，型号名白名单过滤，缺失/不可读返回空串；验证：`test_log_keywords.py` 4 条通过（含 `../../etc/passwd` 被拒）。
- [x] 2.3 新增 `tests/graybox/unit/test_log_keyword_catalog.py`：解析型号目录里的关键词，断言都存在于 `backend/config/device_log_keywords.json`；验证：3 条通过，且故意加一条臆造关键词时用例变红（已手工验证并还原）。
- [x] 2.4 把关键词表接进步骤简报：`_step_keywords` 按 `log.sku`（缺省用用例级型号）装载，`step_brief.verifier_brief` 附加【本步关键词表】；目录缺失时写入「该型号关键词目录缺失，请退回截图核对」；验证：`test_step_brief.py` / `test_sop_step_isolation.py` 相关用例通过。
- [x] 2.5 改 `engines/agents/config/data/prompts/UI_VERIFIER_PROMPT.md` 第 4 条：删掉「系统提示词末尾附有日志关键词表」，改为「优先用【本步日志证据】的 keyword → 其次【本步关键词表】 → 都没有则判不通过并写明缺哪个功能点，禁止连续盲试」；验证：`test_role_prompt_guardrails.py::test_verifier_prompt_takes_keyword_from_step_evidence` 通过。
- [x] 2.6 改 `engines/agents/config/data/prompts/UI_EXECUTOR_PROMPT.md`：第 15 条要求优先按【本步页面锚点】导航、找不到入口最多试 2 个 xpath 候选；验证：`test_executor_prompt_uses_page_anchors` 通过。
- [x] 2.7 用例级型号兜底：`platform_run._case_sku` 从用例标题识别型号（`H6810 定时功能测试` → `H6810`），经 `run_workflow(..., default_sku=...)` 传给装配；旧用例没有 `log` 时仍能拿到关键词表；验证：`test_sop_step_isolation.py::test_case_sku_fills_keyword_catalog_for_steps_without_log` 通过。
- [x] 2.8 执行提示词第 16 条：交卷前必须停在本步结果页并先截图留证，禁止先返回/退出再交卷；验证：`test_executor_prompt_stays_on_result_page_before_submitting` 通过。
- [x] 2.9 验收提示词按断言类型分流主证据：日志型以日志为唯一判据（不必截图、不因页面已离开判负），页面型以截图为主（不查日志），混合型两类都要；验收方法的 1~4 条重写并保留原有硬约束；验证：`test_verifier_prompt_splits_evidence_by_assertion_type` 与全部 15 条提示词纪律测试通过。

## 3. 每步新建角色实例

- [x] 3.1 `engines/agents/workflow/ui_auto_workflow.py`：`AgentSOPWorkflow` 改为接收 `executor_factory` / `verifier_factory`，`run_workflow` 为每步各调一次工厂；角色名与模型取第一对实例用于日志与事件映射；验证：`test_sop_step_isolation.py` 通过。
- [x] 3.2 模块级 `run_workflow()`（手工入口）改为传工厂；验证：`python -c "import engines.agents.workflow.ui_auto_workflow"` 成功且入口传 `build_executor, build_verifier`。
- [x] 3.3 `engines/agents/workflow/platform_run.py`：`_drive_real` 传工厂（执行者外层仍包 `IncompleteHandoverGuard`），步骤改为 `CaseStep` 对象；验证：`test_case_run_continuity.py`、`test_close_recent_apps.py`、`test_platform_case_title.py` 共 26 条通过。
- [x] 3.4 新增 `tests/graybox/unit/test_sop_step_isolation.py`：验证「每步实例不同」「提示按步拼装」「开场上下文重放到每步」「用例级型号兜底」「空步骤被拒」；验证：5 条通过。
- [x] 3.5 确认仓库内无「最近 3 步保留截图」的残留实现或断言；验证：`Select-String -Path engines,tests -Pattern '最近 3 步|保留最近'` 无命中（仅后端测试数据里的无关文案）。
- [x] 3.6 开场上下文每步重放（TASK-179 实测暴露：第二步新实例丢掉设备 serial）：`with_context` 把 `run_input` 前置到每步 subject 与 description；验证：`test_opening_context_is_replayed_on_every_step` 通过。

## 4. 回归与验收

- [x] 4.1 跑相关单测：结构化字段 / 简报 / 关键词 6 个文件 + 隔离用例 + 提示词纪律 + 执行连续性，共 38 条全过。
- [x] 4.2 注释与风格自检：`.agents/skills/engines-docstring-check` 下 `python -m scripts.docstrings check` → 0 error；`.agents/skills/engines-agents-style-check` → 仅 HEAD 存量的 23 条 `raises-doc`，本次文件无新增。
- [x] 4.3 门禁：`ruff check engines/` + `ruff format --check engines/` 全过；`python run.py check` 20/22，两项 prettier 失败全部来自未提交的前端 WIP（`frontend/src/modules/task-list/*`、`ai-assistant/helpers/assistant-cards.ts`），与本次改动无关；engines 的 ruff / lint / silent-except / docstring 全绿。
- [x] 4.4 真机回归 TASK-178 同一用例（`H6810 定时功能测试`，`R5CT62RH88F`）跑两轮：均 5 步首判通过；run1 540s、run2 478s（基线 580s，-18%）；费用 ¥1.2831（基线 ¥1.2542，+2%，与估算的「省一半」不符，原因见文档）；`check_device_log` 19→3。
- [x] 4.5 文档：`dev_docs/DEV_TEST/分析-定时任务178执行过程与优化空间-20261103.md` 增「八、实施后：实测对比」，含两轮数据、费用未降的原因与 TASK-179 暴露的三处修复。
