## ADDED Requirements

### Requirement: 坐标核对工具

系统 SHALL 在引擎工具层提供一个只读的坐标核对工具：输入设备序列号与坐标，截取当前屏幕并在该坐标处画红色圆点，返回标记后的图片（base64 + media_type）。工具 MUST 不落盘，且失败时返回可读 error。该工具 MUST 装配给执行角色并保持常驻；验收角色 MUST NOT 获得该工具。

#### Scenario: 标记后的图片返回给模型

- **WHEN** 执行模型以归一化坐标调用坐标核对工具
- **THEN** 工具返回一张在原坐标处带红点的截图，media_type 与原截图一致

#### Scenario: 像素坐标同样可核对

- **WHEN** 执行模型以 `xpath_action` 返回的像素坐标调用坐标核对工具，并传 `normalized=False`
- **THEN** 工具按原图像素坐标画红点，不做归一化换算

#### Scenario: 工具只读且常驻

- **WHEN** 检查执行角色的常驻工具表
- **THEN** 其中包含坐标核对工具，且该工具标记为只读

#### Scenario: 验收角色看不到

- **WHEN** 检查验收角色的工具包
- **THEN** 其中不包含坐标核对工具

#### Scenario: 截屏或坐标失败

- **WHEN** 设备截屏失败，或像素坐标越界
- **THEN** 工具返回 {"error": ...}，不抛出未处理异常
