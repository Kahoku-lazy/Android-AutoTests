## 1. 新增两条用例（内容内联）

- [x] 1.1 `tests/ai_planner/cases/extended.yaml` 追加 `classic-page-functions`：`input: json`，`goal` = 一句话目标，`attach` = 经典页面三条测试点**逐字原文**（含编号，来源注释指向 `logs/01/H6810自动化测试点.md`），`device` = 空；`expect`: `must_contain: [H6810, 经典, 开关]`、`steps_min: 3`、`steps_max: 12`、`require_flow_tool: true`、`expect_mixed_log_check: true`。验证：`load_cases` 能加载且该用例字段自洽。**验证结果**：已加入；三条测试点原文（含 `WIFI&蓝牙`）在 YAML 块标量中逐字保留；`device` 留空并在注释与设计中登记原因（实测设备池无在线设备，且规划不需设备）。
- [x] 1.2 同文件追加 `dynamic-page-functions`：结构与上一条一致，`attach` = 灵动页面三条测试点原文，`must_contain: [H6810, 灵动, 开关]`。验证：`load_cases` 加载成功；扩展集由 5 条增至 7 条。**验证结果**：扩展集 5 → **7 条**；两文件头注释仍写明正式口径＝单步/多步。

## 2. 期望校准（真实调用，仅这两条）

- [x] 2.1 用**临时用例文件**（`temps/`，只含这两条）跑一次 `planner_eval`，模型用平台配置的 **deepseek-flash**、`--repeat 1`。验证：命令退出 0；记录硬性通过情况、步骤数、`log_check` 是否出现混合取值、费用。**验证结果**：**硬性 2/2 通过**、无任何疑似提示；`classic-page-functions` **8 步**（¥0.012287 / 10.4s）、`dynamic-page-functions` **9 步**（¥0.012135 / 9.2s），两条都调用了页面流工具；报告 `tests/reports/planner_eval/calib-h6810-20261008-143239.md`。
- [x] 2.2 按真实输出校准期望：若某关键词未被命中且原因是模型用了同义表达（如把"开关"写成"电源键"），**删除该关键词**并在用例注释写明原因（不放宽到无意义）；若步骤数落在区间外，核对是"漏测试点"（保留判失败）还是"正常展开"（调整区间）。验证：校准后重跑这两条 → 硬性通过，且改动有据可查。**验证结果**：**首次校准即全部命中，无需调整任何期望**。关键证据（经典那条的计划）：三个关键词 `H6810` / `经典` / `开关` 均出现；步骤数 8 落在 `3~12` 内；**`log_check` 出现区分**——开关两步为 `true`（断言写明"设备日志上报开关开启/关闭成功事件"），其余步骤为 `false`（页面级断言）——与你测试点里"日志断言"与"检查图标显示正确"两类验收完全对应；模型还把测试点里的"开关 OFF/ON"正确理解成**两个方向各一步**。

## 3. 验证与归档

- [x] 3.1 既有守卫用例：`pytest tests/graybox/unit/test_ai_planner_eval.py -q`（含"扩展集 ≥5 条"断言）。验证：全绿。**验证结果**：全绿（扩展集 7 条仍满足 ≥5）。
- [x] 3.2 静态检查与自检：`python -m ruff check`（门禁范围）+ `python manage.py check`。验证：通过。**验证结果**：`ruff check` All checks passed；`manage.py check` 无问题；本次未改任何 Python 代码。
- [x] 3.3 关单与归档：汇总两条用例的实跑结果（通过情况 / 步骤数 / 费用）与校准结论；`openspec validate` 通过后归档（`skip_specs: true`）。验证：`openspec validate "2026-10-08-add-h6810-card-page-cases"` 通过并完成归档。**验证结果**：validate --strict 通过；已归档（`skip_specs` 生效，无规格 delta）。校准临时文件已删除。
