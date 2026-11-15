## ADDED Requirements

### Requirement: 任务跑完直出测试报告

平台任务运行 MUST 产出一份可直接打开的 HTML 报告，落在 `engines/backend_bridge/reports/paths.py` 定义的平台报告根下；报告路径 MUST 随任务结果返回并可从任务列表直接跳转。系统 MUST NOT 再提供任务详情报告（轮次 / 用例分解 / 事件面板），MUST NOT 为任务执行写事件明细表。

#### Scenario: 跑完拿到报告

- **WHEN** 一条平台任务执行结束（成功、失败或取消）
- **THEN** 平台报告根下出现本次运行的 HTML 报告，任务记录里能取到该报告的定位信息

#### Scenario: 任务列表直达报告

- **WHEN** 用户在任务清单里打开一条已完成任务
- **THEN** 直接进入该任务的 HTML 报告，不再进入任务详情页

#### Scenario: 不再写任务事件明细

- **WHEN** 一次任务运行结束
- **THEN** 不为该任务写入事件明细行，也不生成事件缩略图

### Requirement: 用量与费用仍入既有账本

任务报告直出 MUST NOT 改变用量与费用的记账口径：逐次调用的用量仍写入既有账本，任务的总费用仍落在任务记录上。

#### Scenario: 用量照常入账

- **WHEN** 一次任务运行产生若干次模型调用
- **THEN** 每次调用的用量写入既有账本，任务的总费用与改动前一致

#### Scenario: 引擎不依赖后端类型

- **WHEN** 扫描 `engines/backend_bridge` 的代码
- **THEN** 不出现 `django` 或 `apps.*` 的导入

### Requirement: 平台运行可取消

平台 MUST 能在一次运行进行中请求取消，并在取消后让当前步骤中断、停止后续步骤、把取消与失败区分记录。取消能力 MUST 基于 `ae_harness` 的取消令牌与中间件实现，MUST NOT 自建第二套编排。

#### Scenario: 运行中取消

- **WHEN** 用户在任务清单点击取消
- **THEN** 后端经 `engines/backend_bridge` 置位取消令牌，下一次模型调用前中断，后续步骤不再启动

#### Scenario: 取消与失败分开记录

- **WHEN** 一次运行因取消而结束
- **THEN** 任务结论记为用户取消，而不是验收失败

#### Scenario: 取消后的清理

- **WHEN** 取消处理完成
- **THEN** 取消令牌被清除，同一进程的下一次运行不受影响
