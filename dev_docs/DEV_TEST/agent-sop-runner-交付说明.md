# agent-sop-runner 交付说明

## 范围

- 变更：`openspec/changes/agent-sop-runner`，规格能力 `agent-sop-runner`。
- 代码：`engines/agents/role/sop.py`（新增）、`engines/agents/role/executor.py`、`engines/agents/prompt_config.py`。
- 平台侧（`engines/ai`、`apps/`、`frontend/`）零改动：这些目录下既有的 92 个脏文件，最后一次写入时间全部早于本次动手时刻，期间无一处被写入。
- 验证脚本：`temps/_sop_run_check.py`、`temps/_sop_cost_runner_check.py`、`temps/_sop_prompt_check.py`。

## 验证证据

| 验证项 | 命令 | 结果 |
| --- | --- | --- |
| 静态检查 | `python -m ruff check --no-cache`（本次触及的 8 个文件） | All checks passed |
| 装配 / 驱动 / 日志 / 用量 | `python temps/_sop_run_check.py` | 第 0~6 段断言全部 True |
| 真实运行复算 | `python temps/_sop_cost_runner_check.py` | 一致 = True；69 次调用合计 0.331 元（执行 0.263 / 验收 0.068） |
| 提示词契约 | `python temps/_sop_prompt_check.py` | 必备约束全部命中，冲突表述零命中 |
| 架构边界 | `python tools/gen_arch_stats.py --check-boundaries` | 零违规 |
| 规格校验 | `openspec validate agent-sop-runner --strict` | valid |

## 已知边界（两条）

1. **SOP 路径下角色就绪时的日志开关不直接生效**：日志由运行器沿用执行角色那份日志对象写入，因此开关仍看执行角色的就绪参数，验收角色自己的日志开关在 SOP 模式下不起作用。
2. **用量与费用不随运行状态持久化**：导出的运行状态只含流程自身的阶段、输入、交付与历次结论；用状态重建后续跑，用量与费用从重建时刻重新累计，只覆盖新进程内的调用。该边界已在规格里如实声明为契约。

## 门禁结果

`python run.py check`：阻塞项 13/19 通过，6 项失败。

- **本次引入的 1 条已修复**：`silent-except` 曾命中 `engines/agents/role/sop.py:55`（`except ValueError:` 后只有 `pass`），已补「明确忽略」注释；单条门禁复跑后该文件不再出现。
- **其余 5 条为既有项，与本次变更无关**：
  - `prettier`、`prettier-ts`、`vue-file-size`：前端既有问题（本次未触及前端）。
  - `ruff-engines-lint`、`ruff-engines-format`：引擎侧既有文件（`engines/agents/agents.py`、`engines/agents/mcp_config/mcp_config.py`）与供应商产物（`engines/agents/skills/common/skill-creator/**`）——`ruff.toml` 只排除了 `engines/ai/skills/skill-creator/**`，漏了脚手架里的这份拷贝。
