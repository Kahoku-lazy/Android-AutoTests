## Why

任务 119（配置里 2 条用例 × 9 步）实际只跑到第 1 条用例的第 2 步就整轮终止：第 2 步两次验收都没通过，`_drive_real` 收到 `phase != "completed"` 立刻 `return _case_failed(...)`，于是第 1 条余下 7 步与第 2 条 9 步**一步都没执行**，报告只能显示“用例 2 未执行”。

复盘这一步的两次失败，还有两个放大器：

1. **轮次预算**：第 2 次尝试用满 30 轮工具调用（`max_iters=30`），在长按成功后反复试错（误点分段控件、试「…」菜单、三次 xpath 查询），到第 30 轮被引擎提示“预算用尽、立即交卷”，于是**差最后一次点右上角 ✓** 就交了 handover。
2. **自述未完成仍交卷**：执行者自己在 handover 里写「尚未点击右上角 ✓」「请下一步立即执行」，说明它明知没做完；提示词已经禁止这种表述，但没有任何机制拦回，只能靠验收者驳回，而驳回次数（2 次）一次就烧完。另一处诱因是提示词把“长按卡片后出现的加载圈”与“页面加载超时”混为一谈，让它第一次尝试直接放弃。

## What Changes

- **不再一批陪葬**：单条用例失败只记该条失败，继续跑后续用例；结果里同时给出 `completed` 与 `failed` 两份清单，任务终态在有失败时仍为 `fail`，`reason` 汇总所有失败用例标题。
- **轮次预算翻倍**：平台装配执行者角色时 `max_iters` 由默认 30 提到 60；验收者维持 30。
- **交卷硬拦截**：执行者交卷时若 handover 自述未完成（如“尚未/未完成/请下一步”），引擎在同一轮尝试内回灌“继续执行”并要求重做，最多回灌 2 次；超出后放行给验收者判定，不吞掉这次尝试。
- **提示词区分加载语义**：长按/点击卡片后出现的设备连接加载圈不属于“页面加载超时”，等待其消失即可，MUST NOT 据此判失败。

## Capabilities

### New Capabilities

- `case-execution-continuity`：一批用例的执行连续性——单条失败不终止整批，结果清单区分完成/失败，取消立即停止。
- `executor-handover-guard`：执行者交卷前的轮次预算与“自述未完成”拦截。

### Modified Capabilities

- `role-prompt-guardrails`：执行提示词的“提交前自检”补充两条——长按加载圈不等于页面加载超时；handover 出现未完成措辞即视为未做完，必须继续而不是交卷。

## Impact

- 引擎：`engines/agents/workflow/platform_run.py`（用例循环与结果字典）、新增 `engines/agents/workflow/handover_guard.py`、`engines/agents/prompts/executor_prompt.py`。
- 后端：`backend/apps/task_list/task_runner.py`（把 `failed` 清单写进任务结果载荷）。
- 测试：新增 `tests/graybox/unit/test_case_run_continuity.py`、`test_handover_guard.py`；扩写 `test_role_prompt_guardrails.py`。
- 数据：不改表结构，不改历史任务记录；报告页的用例格子仍按事件还原，失败用例之后的用例现在会有真实执行记录。
