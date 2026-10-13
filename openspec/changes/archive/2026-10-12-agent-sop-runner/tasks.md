## 1. 角色构造参数扩展

- [x] 1.1 执行角色与验收角色的构造支持可选覆盖「系统提示词」与「角色名」，不传时保持既有默认；验收角色默认角色名与执行角色不同。验证：`python -m ruff check --no-cache engines/agents/role/executor.py` 通过，且离线冒烟里 `build_device_sop` 装配出的执行者与验收者角色名不同
- [x] 1.2 用离线脚本确认「不传系统提示词」时角色仍使用既有默认提示词，行为与变更前一致。验证：`temps/_sop_run_check.py` 第 1、2 段输出中默认提示词生效且未传参不报错

## 2. SOP 专用提示词

- [x] 2.1 新增 SOP 执行提示词：只做当前步、先看图再动手、失败如实说明、必须以结构化「交接说明」收尾，交接里带点击时间戳与截图相对路径。验证：`python -m ruff check --no-cache engines/agents/prompt_config.py` 通过，且提示词文本里出现「handover / 结构化输出工具」约束
- [x] 2.2 新增 SOP 验收提示词：必须自己截图、逐条对照本步目标、不通过时写明「缺什么 / 在哪看到 / 下一步怎么做」、结论以结构化输出给出。验证：同上，且文本里出现「passed / message」字段名
- [x] 2.3 确认两份提示词都不含「只输出一个 JSON 字符串」这类与结构化输出工具冲突的表述。验证：在 `engines/agents/prompt_config.py` 里对两份 SOP 提示词做文本检索，无该表述

## 3. SOP 装配

- [x] 3.1 实现「按 (步骤名, 必须达成的结果) 列表装成 SOP」的入口，步骤顺序即执行顺序，支持自定义列表与默认列表。验证：`temps/_sop_run_check.py` 输出步骤名列表与入参一致
- [x] 3.2 装配时取角色上已就绪的智能体实例，未就绪时报错并指明执行侧还是验收侧。验证：`temps/_sop_run_check.py` 第 1 段输出「按预期报错：执行角色还没 start()」，第 2 段输出两处 `is` 判定为 True
- [x] 3.3 每一步都同时挂执行者与验收者，重试上限可配。验证：装配结果里每步的 `max_attempts` 等于入参

## 4. SOP 运行器：驱动与过程日志

- [x] 4.1 运行器按顺序推进流程，事件实时上屏；支持「启动一次运行」「把外部答复交回挂起步骤」「导出运行状态」「用状态重建并续跑」。验证：`temps/_sop_run_check.py` 第 2 段输出运行阶段、`dump_state`、`resume_from` 可用
- [x] 4.2 运行器按「回复开始事件」切换角色、按「步骤起止事件」切换阶段标识，把事件写进执行角色给出的那份过程日志。验证：`temps/_sop_run_check.py` 第 3 段日志原文里执行角色与验收角色分别署名，且第 4 列包含步骤名与「第 1 次」
- [x] 4.3 日志关闭时不产生文件。验证：`temps/_sop_run_check.py` 第 2 段输出「日志文件存在 = False」

## 5. 运行级用量与费用汇总

- [x] 5.1 在模型调用结束事件上累计输入/输出/缓存命中 token，并按该次调用的时刻与模型名分别计费后求和；对外提供合计、三项费用与按角色的分项。验证：`temps/_sop_run_check.py` 第 4 段四项断言（用量正确、费用正确、分角色、合计）全部为 True
- [x] 5.2 用真实日志复算：把一次真实运行的模型调用逐条喂进运行器，结果与独立用计费器逐次求和完全一致。验证：`temps/_sop_cost_runner_check.py` 输出「一致 = True」并给出合计金额
- [x] 5.3 提供商不是 DeepSeek 时只统计 token、费用为 0。验证：以非 deepseek 构造运行器后 `run_cost()` 返回全 0 而 `run_usage()` 仍累计
- [x] 5.4 每次推进结束时把累计用量与费用写一条过程日志，内容含调用次数、三项 token、三项费用与合计。验证：`temps/_sop_run_check.py` 输出「过程日志含「用量汇总」行 = True」，日志原文末行可见该记录
- [x] 5.5 确认没有写入平台用量统计。验证：`git status --short` 与 `git diff` 中不出现平台用量相关模型、迁移或视图的改动

## 6. 对照规格复核与关单

- [x] 6.1 逐条对照本变更规格，确认每个 Scenario 都有对应的可复现证据（离线脚本输出或日志片段），把无证据的场景补上脚本或如实记为未覆盖。验证：`openspec validate agent-sop-runner --strict` 通过，且每条 Scenario 在任务备注里能指到证据
- [x] 6.2 确认平台侧零改动。验证：`git status --short` 在 `engines/ai`、`apps/`、`frontend/` 下无新增改动，`python tools/gen_arch_stats.py --check-boundaries` 通过
- [ ] 6.3 确认本变更未引入跨 App import 与任何写库。验证：`python tools/gen_arch_stats.py --check-boundaries` 与 `python run.py check` 的阻塞项通过
- [x] 6.4 归档前复核：把已知边界（SOP 路径沿用执行角色的日志开关、用量不随运行状态持久化）写进交付说明。验证：`openspec status --change agent-sop-runner` 显示全部产物 done，且交付说明里两条边界都有记录

## 7. 验证记录（本会话）

- 静态检查：`python -m ruff check --no-cache` 覆盖本次触及的 8 个文件 → All checks passed；`python -m ruff format --check --no-cache` 上除 `engines/agents/role/executor.py`（既有 `__main__` 空白行）外全部已格式化。
- 装配与驱动：`python temps/_sop_run_check.py` → 第 0~6 段断言全部 True（含自定义步骤覆盖、系统提示词覆盖进到智能体、跨高峰边界逐次求和 = 3.0 元、续跑后用量从零开始）。
- 真实复算：`python temps/_sop_cost_runner_check.py` → 一致 = True；69 次调用、输入 741832 / 输出 21643 / 缓存命中 507776 tokens、合计 0.331 元（执行 0.263 / 验收 0.068）。
- 提示词契约：`python temps/_sop_prompt_check.py` → 必备约束全部命中，`只输出一个 JSON 字符串` 与 `不要多余文字` 在两份 SOP 提示词中零命中。
- 写库/跨模块：本次变更的 7 个代码文件对 `django` / `from apps` / `.objects.` / `.save(` 的检索零命中（唯一命中是 `prompt_config.py` 里既有的说明性注释）。
- 步骤数不匹配：由框架在装配运行状态时抛错（`agentscope/sop/_engine.py:51-55`），本变更的 `resume_from` 直接透传，未另写逻辑；该项为框架侧证据，本沙箱无法运行时复现。
- 架构边界：`python tools/gen_arch_stats.py --check-boundaries` → 零违规。
- 质量门禁：`python run.py check` → 阻塞项 13/19 通过；本次引入的 `silent-except`（`engines/agents/role/sop.py:55`）已修复并单条复跑确认消失，剩余 5 项为前端既有问题与引擎侧既有文件/供应商产物（详见 `dev_docs/DEV_TEST/agent-sop-runner-交付说明.md`）。
