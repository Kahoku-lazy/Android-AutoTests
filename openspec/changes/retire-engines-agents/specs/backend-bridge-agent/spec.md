## ADDED Requirements

### Requirement: 平台任务事件落库归 backend_bridge

平台任务运行产生的事件在写出前的接收方绑定、运行上下文、运行预算计数、步骤中断收集与批量折叠 MUST 由 `engines/backend_bridge` 提供；引擎侧 MUST NOT 直接写数据库，MUST NOT 依赖后端框架类型。`engines/ae_harness` 只负责把事件写成本地记录与报告，不承担落库。

#### Scenario: 任务事件经 backend_bridge 落库

- **WHEN** 平台启动一条任务并产生模型调用、工具执行与步骤结论事件
- **THEN** 事件经 `engines/backend_bridge` 的接收方绑定与折叠后交给后端写库，`engines/ae_harness` 内不出现数据库写入

#### Scenario: 预算与中断仍可计数

- **WHEN** 一次运行超过模型调用次数上限或被外部中断
- **THEN** 超限与中断结论由 `engines/backend_bridge` 的预算与中断收集给出，并随事件落库

#### Scenario: 引擎不依赖后端类型

- **WHEN** 扫描 `engines/backend_bridge` 的事件代码
- **THEN** 不出现 `django` 或 `apps.*` 的导入

### Requirement: 平台运行可取消

平台 MUST 能在一次运行进行中请求取消，并在取消后让当前步骤中断、停止后续步骤、把取消与失败区分记录。取消信号 MUST NOT 依赖已退役包内的实现。

#### Scenario: 运行中取消

- **WHEN** 用户在任务详情页点击取消
- **THEN** 后端经 `engines/backend_bridge` 置位取消，当前步骤中断，后续步骤不再启动

#### Scenario: 取消与失败分开记录

- **WHEN** 一次运行因取消而结束
- **THEN** 运行结论记为用户取消，而不是验收失败，且已产生的尝试记录保留

#### Scenario: 取消后的清理

- **WHEN** 取消处理完成
- **THEN** 取消信号被清除，同一进程的下一次运行不受影响
