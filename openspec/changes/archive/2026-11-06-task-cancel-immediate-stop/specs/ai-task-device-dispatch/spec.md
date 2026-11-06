## ADDED Requirements

### Requirement: 关闭任务不提前释放设备槽

用户关闭运行中的任务时，系统 MUST NOT 在关闭动作中拉起该设备上排队中的 `pending` 任务。设备槽的放行 MUST 发生在执行该任务的工作线程退出之后，由工作线程统一触发。若工作线程在 60 秒内仍未退出，系统 MUST 记录一条可见的告警事件并强制放行，MUST NOT 让该设备永久不可用。

#### Scenario: 关闭时同设备有排队任务

- **WHEN** 设备 A 上有一条 `running` 任务正在被关闭，且该设备还有一条 `pending` 任务
- **THEN** `pending` 任务在旧工作线程退出之前保持 `pending`
- **AND** 旧工作线程退出后，该 `pending` 任务被拉起为 `running`

#### Scenario: 工作线程超时未退出

- **WHEN** 任务被关闭后工作线程超过 60 秒仍未退出
- **THEN** 系统记录一条告警事件，并强制放行该设备的排队任务
- **AND** 设备不会因为该线程而永久无法接新任务
