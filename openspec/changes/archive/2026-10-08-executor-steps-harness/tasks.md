## 1. 跑测工具

- [x] 1.1 新增 `tests/engines/steps.sample.json`：示例步骤文件（含 `serial` 与多条 `action` / `assert` / `log_check`）。验证：文件可被工具解析，步骤数 ≥ 2。**验证结果**：示例含 3 条步骤（启动 govee / 上滑列表 / 返回键），解析通过。
- [x] 1.2 新增 `tests/engines/test_executor_steps.py`：读 JSON 循环执行、逐步打印思考 / 工具调用与返回 / 截图路径 / 输出 / token / 费用，末尾打印总计并写 `tests/reports/engines/run-*.jsonl`。验证：用示例 JSON 真机跑通（≥2 步），每步都有工具调用记录与费用，总费用等于各步之和。**验证结果**：真机 3 步全 OK，每步均有工具调用与返回（`app_control` / `screenshot_page` / `swipe_screen` / `press_key`，状态均为 success）、截图路径与输出 JSON；分步费用 0.002470 / 0.004555 / 0.007162，合计 0.014187 与 0 失败；记录落 `tests/reports/engines/`（输出留档 `temps/harness_run2.txt`）。
- [x] 1.3 配置与跳过：从环境变量取模型连接（缺 `EXECUTOR_API_KEY` 时给可读提示）；pytest 收集时缺配置或缺 steps 就 skip。**验证结果**：`pytest tests/engines/test_executor_steps.py -q` → `1 skipped`（需 `EXECUTOR_STEPS_RUN=1` + 密钥）；缺密钥直接运行时打印含设置示例的可读指引。
- [x] 1.4 单步失败不中断：某步抛错时打印错误后继续下一步，汇总给出失败步数。验证：用一条必然失败的动作跑一次，前后步骤仍执行完毕。**验证结果**：把 base_url 指向不可达地址后跑 3 步，逐步打印 `✗ 执行异常：APIConnectionError`，三步均被执行、汇总「失败 3 步（1, 2, 3）」、退出码 1（留档 `temps/harness_fail.txt`）。

## 2. 关单

- [x] 2.1 复核与汇报：`apps/` 与前端零改动；`python manage.py check`、ruff、相关 pytest 全绿；`openspec validate "2026-10-08-executor-steps-harness" --strict` 通过。验证：以上命令结果与一次真机跑测输出一并汇报。**验证结果**：`apps/` 与前端零改动（前端两处改动为会话前既有、属在办另一单）；`manage.py check` 无问题；ruff 与格式检查通过；最小集 54 通过 + 1 跳过；`openspec validate`（含 `--strict`）通过；真机跑测输出如上。
