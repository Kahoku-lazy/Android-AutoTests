## 1. 步骤编译口径（subject = 动作）

- [x] 1.1 `backend/apps/case_manager/api_rows.py` 的 `compile_automation_cases`：`subject` 取该步动作（去「动作：」前缀、压成单行），`description` 首行改为「用例：<标题>」；验证：`python -m pytest -c tests/pytest.ini tests/task/api/test_task_submit_sop.py` 通过，并用一条两步用例断言编译结果里 `subject` 不含用例标题与「第 N 步」。
- [x] 1.2 `engines/backend_bridge/eval/case_run.py` 的 `compile_case_yaml` 同口径（subject = 动作，description 首行带用例标题）；验证：用评测题库的一条两步用例跑编译，断言两步 `subject` 分别是两步动作。

## 2. 报告记录带上标题

- [x] 2.1 `engines/backend_bridge/workflow/bound_sop.py`：`run_bound_sop` 增加可选 `report_title` 入参，`_run_meta` 写进 `run.report_title`（缺省空串）；验证：`python -m pytest -c tests/pytest.ini tests/task/api/test_task_submit_sop.py` 通过，且断言的记录里出现该字段。
- [x] 2.2 `backend/apps/task_list/task_runner.py`：调用 `run_bound_sop` 时传 `task.title`；验证：提交一条平台用例任务后，`.aligned.json` 的 `run.report_title` 等于任务标题。
- [x] 2.3 `backend/apps/ai_assistant/services/assistant_threads.py`：`AlignedRun.begin` 的 run 段补 `report_title`（会话标题，空则助手名）；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant` 通过，且新会话报告的 run 段有该字段。

## 3. 渲染层

- [x] 3.1 `engines/ae_harness/event/render_aligned.py` 页头改为方案 C：12px 品牌小标签 + 24px 主标题；主标题读 `run.report_title`，为空时退回改动前的品牌标题；单行省略 + `title` 全文；验证：用 `logs/agents/backend_bridge/20261127_155225` 的记录重渲染，页头出现任务标题且页签不被挤动。
- [x] 3.2 新增 `_step_goal()` / `_stage_step_title()` 并接入报告区与阶段页：`subject` 带「 · 第 N 步」尾缀时回退 `description` 的「动作：」行；报告区标题不再拼 `第 {position} 步 · `，阶段页仍是「第 N 步 · 目标」；分组按步骤序号归并；验证：上述重渲染里 5 个分组标题是 5 个不同目标、每组只有一个序号。
- [x] 3.3 正文剥掉 `### 目标：` 标记行（含已绑定步骤的回复，用 `_GOAL_LINE`）；验证：重渲染后文本卡里不再出现该标题行，页面只出现一次目标文本。
- [x] 3.4 `engines/ae_harness/event/render.py` 抽出共用 `_report_heading()` 与 `.wb-heading` / `.wb-brand` / 省略号样式，旧渲染器改用同一份页头件；验证：旧渲染器产物打开后页头不重叠、不换行塌陷。

## 4. 测试与门禁

- [x] 4.1 `tests/arch/unit/test_sop_report_contract.py` 增加契约断言：页头读 `run.report_title`、报告区标题取 `_step_goal` 且不带序号前缀、阶段页保留「第 N 步」、`### 目标：` 行被剥；验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_sop_report_contract.py` 通过。
- [x] 4.2 `tests/task/api/test_task_submit_sop.py` 增加灰盒断言：编译出的配置里 `subject` 是动作、`description` 首行是用例标题；验证：该文件全绿。
- [x] 4.3 全量门禁：`python -m run check` + `python -m pytest -c tests/pytest.ini -m "unit or integration"` + `python utils/gen_arch_stats.py --check-boundaries` 全部通过。

## 5. 文档与人工验收

- [x] 5.1 更新 `.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md`：页头两段式布局与标题来源、报告区分组标题取步骤目标、`### 目标：` 标记行不再重复；验证：`python utils/gen_arch_stats.py --check-md --doc .agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md` 通过（该文件无 ARCH_STATS 区域，脚本只给初始化提示）。
- [x] 5.2 用 `20261127_155225` 与一份助手会话记录各重渲染一份报告，人工核对：页头标题、5 个目标标题、阶段页「第 N 步 · 目标」、无重复 `### 目标：`。

## 验收记录

- `python -m run check`：阻塞项 30/30 通过（含 ruff、django-check、makemigrations、boundary、engines 风格）。
- `python -m pytest -c tests/pytest.ini -m "unit or integration"`：345 通过。
- `python utils/gen_arch_stats.py --check-boundaries`：零违规。
- 任务报告重渲染（`logs/agents/backend_bridge/20261127_155225`，页头注入任务标题「H705F 音乐功能测试（UI 验证）」）：页头 = 12px `AGENT 执行报告` + 24px 主标题；报告区 5 个分组标题为 `启动应用并进入 H705F 详情页` / `设置两种不同的音乐灯效（拾音来自设备）` / `灵敏度设置大于 70%` / `灵敏度设置小于 30%` / `关闭 Govee Home`，调用次数 15/15/7/7/9 与改动前一致；阶段页为 `第 1 步 · 启动应用并进入 H705F 详情页`；全文 `### 目标` 出现 0 次。
- 助手会话记录（无 `report_title`）重渲染：页头退回改动前的 24px `AGENT 执行报告`，页签与版式不变。
- 截图产物（未入库）：`temps/after_report.png`、`temps/assistant_fallback.png`。
