## Why

执行模型今天只能经平台任务链路（建任务 → 后台线程 → 工作流）才能跑起来，看一次真机执行要读平台日志、翻任务详情。需要一份**直接驱动引擎**的步骤级跑测工具：给一个 JSON（多条步骤），循环执行，并把模型思考、工具调用、截图路径与费用当场打印出来，用于调提示词、换模型、排现场问题。

## What Changes

- 新增 `tests/engines/test_executor_steps.py`：读 JSON（`{"serial": "...", "steps": [{"action","assert","log_check"}, ...]}`）逐条循环执行；直接使用引擎侧的执行模型（不经平台任务接口、不落库）。
- 每步打印：模型思考过程、工具调用与返回（含只读/写与状态）、点击后截图路径、该步输出 JSON；运行结束打印每步与总计的 token 与费用。
- 运行记录与截图统一落到 `tests/reports/engines/`（已被 git 忽略），供事后核对。
- 模型连接从环境变量读取（`EXECUTOR_API_KEY` 等），缺配置时明确跳过并打印设置指引；缺 steps / serial 时同样给出可读提示。
- 非目标：不改引擎与平台代码；不替代平台任务链路；不做断言判定（验收模型不在本单范围）。

## 关联文档

无关联需求编号：本单是测试工具链（不改产品行为），故按规范约定在变更元数据里声明 `skip_specs: true`。

## Capabilities

### New Capabilities

（无：纯测试工具，不改任何产品的可观察行为。）

### Modified Capabilities

（无。）

## Impact

- **新增**：`tests/engines/test_executor_steps.py`、`tests/engines/steps.sample.json`。
- **运行面**：`tests/reports/engines/`（git 忽略）。
- **不改**：`engines/`、`apps/`、前端、既有测试。
- **依赖**：真机（adb 可达）+ 模型密钥（环境变量）；缺任一项即跳过，不影响默认测试套件。
