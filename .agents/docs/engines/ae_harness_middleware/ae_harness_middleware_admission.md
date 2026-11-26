# ae_harness/middleware · 三类中间件准入
> 归属模块：`engines/ae_harness/middleware` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/middleware/observer.py`、`engines/ae_harness/middleware/retry.py`、`engines/ae_harness/middleware/control.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../../../engines/AGENTS.md) → [`ae_harness_overview.md`](../ae_harness/ae_harness_overview.md) → **本文件**。

## 职责

中间件是**挂到角色上的横切能力**。本目录只放三类，每类准入条款在下表；**超出三类的想法一律拒绝**。

| 类别 | 允许做什么 | 现有实现 | 判据 |
| --- | --- | --- | --- |
| **只读观测** | 看、记录、采样；不改变任何调用结果 | `observer.py` | 去掉它，运行结果必须一模一样 |
| **可靠性** | 失败时**重试同一动作**；不换动作、不换模型 | `retry.py` | 成功路径上的调用次数与参数不变 |
| **运行控制** | 按上限或外部信号**提前中止**；不扩展能力 | `control.py` | 只会让运行更早结束，不会让它多做一件事 |

## 硬性边界

1. **禁止能力型中间件** —— 不得借中间件给角色加工具、记忆、知识库、新技能或外部数据源。新能力只有一条路：改提示词、改工具配置，或另开变更新角色。
2. **禁止在可靠性中间件里换动作** —— 重试必须重发**同一个请求**；备用模型切换属「换动作」，需单独立项。
3. **禁止运行控制型中间件吞异常** —— 预算与取消必须抛出各自异常（`BudgetExceeded` / `RunCancelled`），让调用方能区分「中止」与「失败」。
4. **禁止默认挂载** —— 三类中间件都由调用方显式传入；`create_agent` 不得内置任何一类。
5. **禁止在中间件里读配置或建模型** —— 参数从构造函数进来；本层无配置入口，配置由调用方（`backend_bridge/agents/run_params.py` 与后端 `ModelConfig`）传入。

## 两个异常的使用口径

| 异常 | 归属 | 调用方该记成 |
| --- | --- | --- |
| `BudgetExceeded` | 次数或时长超限 | **中止**（不是失败），报告与用量照常保留 |
| `RunCancelled` | 外部置位取消 | **取消**，与失败分开统计 |

两者都继承 `RuntimeError`，便于兜底 `except Exception`；但业务分支必须按具体类型区分。

## 测试

```bash
python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_observer.py tests/engines/ae_harness/unit/test_retry_middleware.py tests/engines/ae_harness/unit/test_run_control.py -q
```
