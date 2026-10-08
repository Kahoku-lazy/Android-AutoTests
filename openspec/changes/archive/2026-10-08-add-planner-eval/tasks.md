## 1. 命令与机械校验

- [x] 1.1 新增 `apps/ai_assistant/management/commands/planner_eval.py`：参数 `--cases`（必填，YAML 文件或目录）、`--repeat`（默认 1）、`--model`（覆盖 planner 模型名）、`--tag`（报告标签，默认取模型名）、`--report-dir`（默认 `tests/reports/planner_eval`）；装配复用 `model_debug.build_device_models_for_agent`，只取 planner 角色。验证：`python manage.py planner_eval --help` 正常，且 `--cases` 缺失时报可读中文错误。**验证结果**：`--cases` 缺失时 Django 报「the following arguments are required: --cases」；`--model` 覆盖经引擎包级入口重建 planner 角色（`build_device_models(config, ...)`）已验证可用（下面 pro 档对比即走该路径）。
- [x] 1.2 实现用例加载与输入构造：支持 `input: text`（默认，直接喂 `goal`）与 `input: json`（按 Django 侧四键 JSON 构造，可带附件文本与设备 ID）；字段缺失/非法时给出指向该用例 `id` 的可读错误。验证：加载合法用例集成功；构造一条缺 `goal` 的用例时报错含其 `id`。**验证结果**：单测覆盖（缺 id / goal 为空 / input 非法 / steps_min>steps_max 四类报错，以及"目录多文件合并""路径不存在""用例集为空"）；四键 JSON 构造断言与规格口径逐字一致。
- [x] 1.3 实现硬性判据（五项）：JSON 契约与字段非空、`must_contain` 关键词全覆盖、步骤数区间、`require_flow_tool` 时工具轨迹含 `list_page_flows`、`expect_mixed_log_check` 时 `log_check` 非单一取值。验证：用桩数据逐项单测——每项各有"通过 / 不通过"两个断言。**验证结果**：五项各有正反用例（含"用例关闭该要求时不判失败"分支），单测 18 项全绿。
- [x] 1.4 实现疑似提示（三项）：多副作用动作 + 并列连接词、断言空话表命中、重复间结构指纹不稳定。验证：桩数据单测覆盖；并断言"疑似提示不影响硬性通过判定"。**验证结果**：单测覆盖"多动作+连接词判疑似""提示词规定的『先找到元素，再点击』不得判疑似""空话断言判疑似而『启动成功并停留在…』不判"；实跑中该判据抓到 2 处真实的"一步多动作"（见 3.2），且这两条用例仍判硬性通过——分级生效。
- [x] 1.5 实现成本与耗时统计：累加每次 `RoleResult.usage` 与 `RoleResult.cost`（引擎侧已计价），报告给总花费、单次均值、逐用例拆分。验证：桩数据单测断言累加正确（含缓存命中字段）。**验证结果**：`add_usage` 四字段累加单测通过；实跑报告给出总用量（输入 210612 / 输出 9498 / 缓存命中 56960）、总费用与逐用例费用。
- [x] 1.6 实现报告：控制台总表 + 落 `tests/reports/planner_eval/<tag>-<时间戳>.md`（含运行参数、汇总、逐用例明细、plan 原文、工具轨迹）。验证：跑 1 条用例后文件存在、内容含该用例 `id` 与 plan 原文；命令始终以 0 退出（除参数错/装配失败）。**验证结果**：报告文件生成且含运行参数/汇总/逐用例表/plan 原文/工具调用与用量；`render_report` 另有单测断言关键字段。**过程中修掉一个自身缺陷**：Windows 控制台是 GBK，`✅` 会让 `stdout.write` 抛 `UnicodeEncodeError`（模型调用已发生、报告却没写成）——改为控制台用 `[OK]/[FAIL]/[WARN]` 标记 + 新增编码降级函数 `encodable_text()`（并补单测守住，含"编码名未知"分支）。

## 2. 用例集（入库）

- [x] 2.1 新增 `tests/ai_planner/cases/planner.yaml`，6~8 条覆盖：单步需求、多步需求、指定设备名（如 H6810）、带附件文本、模糊需求、需日志核对（开关类断言）、页面流依赖场景（启动应用→进入某页）。每条登记 `must_contain` / `steps_min` / `steps_max` / 是否要求页面流工具 / 是否期望 `log_check` 混合。验证：加载成功且每条期望字段自洽（区间有效、关键词非空）。**验证结果**：共 **7 条**（single-step / multi-step / named-device / with-attachment / json-four-keys / log-check-step / vague-demand）；加载与字段自洽由单测覆盖（含区间校验）。
- [x] 2.2 用例期望自校正：先跑 1~2 条已知可控用例，对照真实输出校正期望（避免期望写错造成假失败）；把校正依据写进用例注释。验证：校正后同一用例重跑稳定通过硬性项。**验证结果**：先以 `temps/_calib_cases.yaml`（single-step + multi-step）实跑校准 → 2/2 通过、期望区间与真实输出吻合（1 步 / 2 步，均在区间内；页面流工具两次都调用），未发现需要调整的期望；随后全量 7 条一次通过（无假失败）。校准临时文件已删除。

## 3. 验证

- [x] 3.1 单元测试（零模型调用）：`tests/graybox/unit/test_ai_planner_eval.py` 覆盖 1.3~1.5 的判据与累加（全部用桩数据，不调模型）。验证：全绿，且不产生任何网络调用与费用。**验证结果**：**18 项全绿**（1.1s），全程无模型调用、无费用。
- [x] 3.2 实跑一遍（真实调用，属预期费用）：`python manage.py planner_eval --cases tests/ai_planner/cases/planner.yaml --tag <模型名>`。验证：命令退出 0、控制台出总表、报告文件生成；如实记录硬性通过率、稳定性、总费用与耗时。**验证结果**：`--tag deepseek-flash --repeat 2` → **硬性通过 7/7**、平均稳定性 **93%**、总费用 **¥0.192784**、总耗时 **77.1s**；页面流工具 **7/7 用例两次都调用**（符合提示词"先看页面流"的要求）；疑似提示命中 2 处（`single-step` 一次、`log-check-step` 两次，内容确为"一步塞多个动作"，非误报）。报告：`tests/reports/planner_eval/deepseek-flash-20261008-123620.md`。逐用例稳定性：仅 `multi-step` 为 50%（两次跑出 2 步 / 3 步），其余 100%。
- [x] 3.3 模型对比（可选，视想对比的档位而定）：用 `--model` 换一个模型跑同一批用例，确认报告并列可读、文件名按 tag 区分。验证：两份报告存在且汇总可对照。**验证结果**：以 `--model deepseek-v4-pro --repeat 2 --tag deepseek-v4-pro` 跑同批用例；两份报告并列可对照（结论见关单汇报）。
- [x] 3.4 后端自检与静态检查：`python manage.py check` + 门禁范围 `ruff check` / `ruff format --check`（含新增命令与用例测试文件）。验证：全部通过。**验证结果**：见 5.1 的实测输出。
- [x] 3.5 边界检查与不动生产确认：`python tools/gen_arch_stats.py --check-boundaries`；并确认本次未触碰任务链路 / 接口 / 前端 / 数据库（`git diff --name-only` 仅新增命令、用例、测试与变更文档）。验证：零违规 + 改动清单符合预期。**验证结果**：见 5.2/5.3。
- [x] 3.6 关单与归档：汇总命令用法、用例集、实跑结果与费用；`openspec validate` 通过后归档（`skip_specs: true`）。验证：`openspec validate "2026-10-08-add-planner-eval"` 通过并完成归档。**验证结果**：validate --strict 通过；已归档。
