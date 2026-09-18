## Context

现状审计见 L1b 详档 §三（全部落到文件+行号）：`TestRunStatus` 双定义（`constants.py:57-64` PASSED 大写 / `test_models.py:12-16` completed 小写）；写库点 4 种口径（`state_machine.py:206` "COMPLETED"、`runner.py:265` 枚举值、`ai_assistant/views_drf.py:642` SUCCESS 别名、前端双列映射）；`TaskOutcome` 语义散落 12 处硬编码；`constants.py` 14 枚举 0 消费（grep 实测仅文档字符串自引用）。

## Goals / Non-Goals

**Goals:**

- TestRunStatus 唯一定义（`test_models.py`），写库与枚举同口径（小写）
- TaskOutcome/TaskCardStatus 枚举化，`outcome` 合法值单源
- 存量数据回填（大写 → 小写），运行时行为等价（除大小写口径修正）
- constants.py 死枚举清理 + DeviceStatus 两态收敛 + 幽灵死代码删除

**Non-Goals:**

- 不做 `display_state()` 权威状态下发（属 Step 5）
- 不动前端 `STATUS_LABEL_MAP`/`taskUtils`（属 Step 6）
- 不改 `tr_test_results.result` 的值口径（仅删 constants.TestResult 死枚举，语义已归 StepResult）
- 不为 constants.py 保留枚举补各 App 引用（AI/设备枚举消费属后续独立变更，本变更只删与收敛执行侧枚举）

## Decisions

- **保留"活"的定义**：`test_models.py` 版 TestRunStatus 已被 runner/remote_runner 实际消费 → 以其为唯一真相源，扩充为 5 值（+FAILED，+PENDING 已有）
- **小写口径**：与 `TaskOutcome` 同口径，建立 run 态/task 态一一映射（§4.1 映射表）
- **fail() 校验**：新增 `TaskOutcome.fail_values()`（= terminal 去掉 COMPLETED），保持"fail 不接受 completed"的现状行为（文档 §6.2 的 `terminal_values()` 表述会误收 completed，此处修正）
- **choices 枚举化**：Django 6.0 原生支持 `choices=EnumClass`；TaskCard 两字段改引枚举并生成 AlterField 迁移
- **数据回填**：独立 RunPython 数据迁移（同值域小写化，幂等）；SQLite 测试走 `--nomigrations` 不受影响，生产 MySQL 执行迁移时回填
- **DeviceStatus**：0 消费，直接删幽灵值收敛两态；connect.py:55 死分支一并删除

## 模块防火墙自检

- 无新增跨 App import：全部改动在 `models/`（零依赖）与 `apps/test_runner/`（本 App 内部）；`apps/ai_assistant/views_drf.py` 仅改字符串列表（已存在读 tr_ 的关系，不新增 import）
- 无 ORM 写路径变化：写库仍经 state_machine/api.py；数据迁移是标准 Django 迁移
- 前端零改动；dashboard 零改动
- 通过

## Risks / Trade-offs

- [存量 DB 大小写数据未回填导致统计遗漏] → 数据迁移幂等回填 + 生产执行前在备份库预演
- [写库口径变更影响报告/WS 展示] → 前端 STATUS_LABEL_MAP 已双口径兼容；报告端读取全量小写后无感知
- [枚举 choices 迁移在 MySQL 上执行失败] → AlterField 为通用操作，迁移链中已有同类；执行前 `makemigrations --check` 与本地 SQLite `--nomigrations` 回归兜底
- [fail_values 与文档差异] → 在 design 明确记录，评审时确认
