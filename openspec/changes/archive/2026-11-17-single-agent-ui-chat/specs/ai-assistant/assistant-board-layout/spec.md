## ADDED Requirements

### Requirement: 助手入口是编排卡片与对话框

平台小助手入口页 SHALL 分为左右两栏：左栏是单智能体编排卡片，右栏是对当前所选卡片的对话框。左栏 MUST NOT 再展示原来的角色线路卡，右栏 MUST NOT 再展示模型池。页面页头 MUST 保留。窄屏下两栏 MUST 改为上下堆叠，MUST NOT 横向溢出。

#### Scenario: 进入助手页看到卡片和对话框

- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 左栏至少有一张「Android UI 控制」卡片，右栏是对话框
- **AND** 本页不出现模型池，也不出现原角色线路卡

#### Scenario: 点卡片后右栏对应该编排

- **WHEN** 用户点选「Android UI 控制」
- **THEN** 右栏对话发往该编排，而不是裸模型对话

### Requirement: 对话前展示当前设备选择

Android UI 控制的对话框 MUST 在发送前展示当前设备选择。未选择设备时发送控件 MUST 不可用，并说明原因。设备列表 MUST 来自现有设备接口，MUST NOT 在助手页另建一套设备数据。

#### Scenario: 没选设备不能发送

- **WHEN** 用户选中 Android UI 控制但没有当前设备
- **THEN** 发送控件不可用，并提示先选择设备
