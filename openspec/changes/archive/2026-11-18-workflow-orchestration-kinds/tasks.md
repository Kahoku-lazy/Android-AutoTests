## 1. 工作流组合与冻结列

- [x] 1.1 为工作流增加编排、种类、队长与成员字段，并把三对白名单放在 `ai_assistant.api`。验证：创建三对成功，交叉组合返回可读错误且不落库。
- [x] 1.2 为任务增加工作流编号、编排、种类三列；迁移回填旧 `assistant_sop` 为 `sop + ui_automation`，并尽量从结果 JSON 回填工作流编号。验证：迁移正向与反向通过，旧行回填后抽查不变成 Goal 或 Team。
- [x] 1.3 新任务创建时写入三列；重跑复制冻结值，不复制失败原因、报告定位和费用。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_rerun_assistant_name.py -q` 通过。

## 2. 保持 UI 自动化

- [x] 2.1 配置弹窗先选择允许的组合，SOP 仍只编辑两张名片，且编辑不能改编排或种类。验证：`cd frontend && npx vitest run tests/ai-assistant` 通过。
- [x] 2.2 UI 任务弹窗保持平台用例或里程碑 YAML，并继续强制选择设备。验证：空设备提交返回 400，合法提交仍进入原设备槽。
- [x] 2.3 任务清单增加编排与种类列；成功、失败、取消、中断显示「重新执行」，执行中只显示「关闭」。验证：`cd frontend && npx vitest run tests/task-list` 通过。

## 3. Goal 用例编写

- [x] 3.1 在工具目录登记用例库工具域，并在名片勾选后按种类过滤。验证：用例编写角色拿不到设备写操作工具，未知工具拒绝启动。
- [x] 3.2 增加 GoalPipeline 薄适配和模块材料输入；任务不占设备，成功产物写入用例库。验证：一次退回重做的单测通过，成功后不自动创建 SOP 任务。
- [x] 3.3 用例编写失败、中断和入库失败仍各登记一张 `case_authoring` BUG。验证：`python -m pytest -c tests/pytest.ini tests/bug_ticket -q` 通过。

## 4. Team 需求拆解

- [x] 4.1 在工具目录登记只读文档与检索工具域，Team 成员只能使用该域。验证：成员勾选设备工具时，本次运行不挂该工具。
- [x] 4.2 增加 TeamPipeline 薄适配，成员说明进入分派描述；合法结果只含模块名、边界、测试点和不覆盖范围。验证：缺任一字段时整次失败，成功后不创建用例编写任务。
- [x] 4.3 增加 `requirement_breakdown` BUG 分类；只有无法形成合法清单或中断时登记一张。验证：合法拆解不登记，失败只新增一张且不归入另两类。

## 5. 报告与边界

- [x] 5.1 报告行读取冻结种类；拆解行展示模块数量，设备和用例为空，三种任务仍归 SOP 筛选。验证：`python -m pytest -c tests/pytest.ini tests/report -q` 通过。
- [x] 5.2 检查跨模块边界与后端基本健康。验证：`python utils/gen_arch_stats.py --check-boundaries` 与 `python manage.py check` 通过。
