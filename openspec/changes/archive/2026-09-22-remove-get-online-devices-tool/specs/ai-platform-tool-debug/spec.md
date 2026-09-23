## MODIFIED Requirements

### Requirement: 调试页按 schema 收集入参并展示结果

系统 SHALL 根据该工具的入参 schema 渲染表单（不含调用者身份字段）。当某参数的候选值由服务端给出时，系统 SHALL 把它渲染为可选择候选值的控件，MUST NOT 只渲染自由输入框；该控件 MUST 保留手输能力，候选清单不含目标值时用户仍 MUST 能填入该值。候选清单为空、加载中或加载失败时 MUST 以可读文案明示，且 MUST NOT 阻止用户执行（仍可手输后提交）。执行成功后 MUST 展示工具返回的数据内容。当返回含截图图像数据时，MUST 以图片预览展示，MUST NOT 把完整图像编码当作主要可读正文铺开。执行失败时 MUST 展示可读错误，MUST NOT 静默忽略。

#### Scenario: 无参只读工具执行成功

- **WHEN** 已登录用户在 `list_devices` 调试页不填额外参数并执行
- **THEN** 页面展示该工具返回的设备列表数据（或等价 JSON）

#### Scenario: 带参工具表单含必填项

- **WHEN** 用户打开需要 `serial` 的平台工具调试页
- **THEN** 表单出现 `serial` 输入，且不出现调用者身份字段

#### Scenario: 截图工具结果出图

- **WHEN** 有权限的用户成功执行 `screenshot_page`
- **THEN** 页面展示截图预览与摘要字段（如 serial / 包名）
- **AND** 不以完整图像编码作为主要阅读内容

#### Scenario: 设备参数渲染为下拉

- **WHEN** 用户打开 `device_action` 调试页
- **THEN** `serial` 显示为可选择设备的下拉，选项来自平台在线且未被占用的设备

#### Scenario: 无候选设备时仍可手输提交

- **WHEN** 平台当前没有在线且未被占用的设备，用户打开 `device_action` 调试页
- **THEN** 下拉没有选项并给出可读提示
- **AND** 用户手输 `serial` 后仍可提交执行
