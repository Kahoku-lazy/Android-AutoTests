## ADDED Requirements

### Requirement: 截图取帧不依赖 uiautomator2

截图工具 SHALL 只经 adb 取帧，MUST NOT 在取帧前建立 uiautomator2 会话。uiautomator2 会话 SHALL 只在需要 xpath 元素查找或非 ASCII 文本输入时建立；uiautomator2 服务不可用 MUST NOT 导致截图失败。设备控制对象的创建 MUST NOT 因 uiautomator2 连接失败而失败。

#### Scenario: u2 不可用时截图仍成功

- **WHEN** 设备的 uiautomator2 服务未启动或不可用，而 adb 通道正常
- **THEN** 截图工具仍返回图片数据，不返回错误

#### Scenario: 截图不建立 u2 会话

- **WHEN** 角色只调用截图工具，未调用 xpath 查询、未输入非 ASCII 文本
- **THEN** 全程不建立 uiautomator2 会话

#### Scenario: 用到 u2 能力时才建立会话

- **WHEN** 角色调用 xpath 查询或输入非 ASCII 文本
- **THEN** 此时才建立 uiautomator2 会话；该次调用失败时返回可读错误，且不影响此前已完成的截图
