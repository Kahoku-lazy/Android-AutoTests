## MODIFIED Requirements

### Requirement: 设备动作记录并回传发出时间

系统 SHALL 在每个产生设备副作用的动作工具执行时记录该动作的发出时刻。取值 MUST 用 `time` 取得本地当前时间，格式 MUST 为 `YYYY-MM-DD HH:MM:SS,mmm`，与日志文件中 logging 的时间一致。该时刻 MUST 随该工具结果一并返回，使编排层能把它与该步截图一起交给验收模型，并作为检查日志的起点。读取类动作 MUST NOT 被记为动作发出时刻。

#### Scenario: 点击类动作返回发出时间

- **WHEN** 智能体对指定设备执行一次点击类动作
- **THEN** 该工具结果中包含本次动作的发出时刻，格式为 `YYYY-MM-DD HH:MM:SS,mmm`

#### Scenario: 读取类动作不产生发出时间

- **WHEN** 智能体调用只读动作（如读取当前前台应用）
- **THEN** 该调用不产生设备副作用，且不被记录为动作发出时刻

### Requirement: 平台侧设备工具在本变更中保持不变

平台侧设备动作工具的工具名、入参、分类与启停开关 MUST NOT 变化。发出时间字段仍叫 `action_time`，其字符串格式改为 `YYYY-MM-DD HH:MM:SS,mmm`。除此以外的返回字段与调用结果 MUST NOT 变化。

#### Scenario: 平台工具行为不变

- **WHEN** 经外部工具通道或工具箱调试页调用平台侧设备工具
- **THEN** 工具名、入参与启停与变更前一致，副作用动作返回的 `action_time` 为 logging 的逗号毫秒格式

#### Scenario: apps 目录零改动

- **WHEN** 审阅设备动作发出时间的改动范围
- **THEN** 该格式改动落在设备工具实现中，`apps/` 下的设备动作接口形状没有改动
