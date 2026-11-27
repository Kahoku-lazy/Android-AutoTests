## Why

报告页头只有固定的「AGENT 执行报告」，从执行报告列表打开多份报告后分不清自己看的是哪一份；报告区的分组标题又是「用例标题 · 第 N 步」，同一条用例的 5 个步骤标题完全相同，而序号已经由手绘 `01` 徽标表达，同一个步骤号在标题里被说了三次——标题没有提供任何区分信息。

## What Changes

- **页头标题（方案 C）**：`AGENT 执行报告` 降为手写体小标签，主标题显示这份报告到底是谁的——任务报告取任务标题（为空则取用例标题），助手报告取会话标题（为空则取助手名）；两者都没有时页头保持现状（只有品牌标签）。主标题过长时单行省略并可悬停看全文。
- **报告区分组标题取步骤目标**：分组标题就是该步 `subject`（这一步要做什么），不再在前面拼「第 N 步 ·」；正文文本卡里那行 `### 目标：…` 不再作为 Markdown 标题重复出现。
- **步骤 `subject` 的编译口径**：平台自动化用例与评测题库编译里程碑时，`subject` 取该步「动作」（去掉「动作：」前缀、压成单行、上限 40 字），用例标题改写到 `description` 首行「用例：…」，不再拼进 `subject`。
- **报告记录新增 `run.report_title`**：任务侧写任务标题、助手侧写会话标题（空则助手名），渲染层读它作为页头主标题；旧记录没有该字段时页头退回品牌标签。
- **不变**：阶段页标题仍是「第 N 步 · 步骤名」；手绘序号、三层折叠、角色块、五个页签、侧栏、字号三档都不动。

## 关联文档

无 PRD 编号：这是引擎侧报告呈现与步骤字段编译口径的修复。`agent-sop-workflow` 早就规定「`subject` 是执行角色这一步要做的动作」，本变更只是把编译出来的里程碑改回这个语义，不新增产品能力。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ae-harness-report-render`: 页头标题从固定品牌改为「品牌小标签 + 报告标题」；报告区分组标题取步骤目标且不再包含步骤序号；正文不再重复 `### 目标：` 标记。
- `agent-sop-workflow`: 步骤 `subject` 的编译口径明确为「该步动作」，禁止拼接用例标题与步骤序号；用例标题允许写进 `description`。

## Impact

- **代码**：
  - `backend/apps/case_manager/api_rows.py`：平台自动化用例编译的 `subject` / `description`
  - `engines/backend_bridge/eval/case_run.py`：评测题库编译的同款口径
  - `backend/apps/task_list/task_runner.py`：把 `task.title` 交给运行
  - `engines/backend_bridge/workflow/bound_sop.py`：`run.report_title` 元数据
  - `backend/apps/ai_assistant/services/assistant_threads.py`：`run.report_title` = 会话标题 / 助手名
  - `engines/ae_harness/event/render_aligned.py`：页头布局、分组标题、`### 目标：` 标记行、旧记录后缀兼容
  - `engines/ae_harness/event/render.py`：旧渲染器共用同一份页头 CSS，需同步口径
- **测试**：`tests/arch/unit/test_sop_report_contract.py`（契约守护）+ 平台用例编译的灰盒断言（`tests/task/api`）
- **文档**：`.agents/docs/engines/ae_harness/ae_harness_event_observation_and_report.md`
- **产物**：只有新生成的 `*.html` 带新页头与新标题；已落盘的旧报告不重写，渲染层对旧 `subject` 的「· 第 N 步」后缀做去重兼容。无库表迁移。
