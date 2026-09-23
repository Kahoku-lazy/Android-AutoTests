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

- **WHEN** 用户打开 `tap_screen` 调试页
- **THEN** `serial` 显示为可选择设备的下拉，选项来自平台在线且未被占用的设备

#### Scenario: 无候选设备时仍可手输提交

- **WHEN** 平台当前没有在线且未被占用的设备，用户打开 `tap_screen` 调试页
- **THEN** 下拉没有选项并给出可读提示
- **AND** 用户手输 `serial` 后仍可提交执行

### Requirement: 登录用户可读取工具入参 schema

系统 SHALL 允许已登录用户按工具名读取平台业务工具的入参 schema（参数名、类型、是否必填、默认值、只读/写、说明）。当某参数的可选值来自平台设备清单时，schema MUST 携带该参数的候选设备清单，每项 MUST 含可提交的取值与可读标签，且清单 MUST 已按请求者可见性收窄。候选值来自工具自身固定值域的参数 MUST 在本变更范围外（无候选声明，按自由输入处理）。未知工具名 MUST 返回 404。

#### Scenario: 读取已知工具 schema

- **WHEN** 已登录用户请求某已注册平台工具的 schema
- **THEN** 响应包含该工具名称、说明、只读标记与参数列表，且参数列表不含调用者身份字段

#### Scenario: 未知工具 schema

- **WHEN** 已登录用户请求未注册工具名的 schema
- **THEN** 系统返回 404

#### Scenario: schema 携带候选设备清单

- **WHEN** 已登录用户请求 `tap_screen` 的 schema
- **THEN** `serial` 参数携带候选设备清单，每项含可提交取值与可读标签

#### Scenario: 无候选参数不带候选清单

- **WHEN** 已登录用户请求 `list_devices` 的 schema
- **THEN** 参数列表中不出现候选设备清单

### Requirement: 设备参数候选限于可见、在线且未被占用的设备

需要 `serial` 并经开引擎取数的平台工具（`list_apps`、`input_text`、`tap_screen`、`swipe_screen`、`press_key`、`current_app`、`click_ratio`、`drag_ratio`、`xpath_action`）的 `serial` 参数 SHALL 提供候选设备清单。候选 MUST 同时满足三项：对请求者可见（与设备管理列表同一可见性规则）、状态为在线、当前未被占用。MUST NOT 出现在线但被占用（含被执行引擎占用）的设备，MUST NOT 出现请求者不可见的设备。候选项 MUST 含可提交的取值与可读标签（设备名称或型号与序列号）。设备池占用记账工具 `acquire_device` 与 `release_device` MUST NOT 提供候选，其 `serial` 保持自由输入。

#### Scenario: 候选只含在线且未被占用的可见设备

- **WHEN** 已登录用户打开 `tap_screen` 调试页
- **THEN** `serial` 下拉只列出其可见、在线且当前未被占用的设备
- **AND** 不列出使用中或被执行引擎占用的设备

#### Scenario: 非超管候选按可见性收窄

- **WHEN** 非超级管理员请求设备候选
- **THEN** 候选集合与其在设备管理列表中可见的设备一致，不含其不可见的设备

#### Scenario: 记账类工具不提供候选

- **WHEN** 用户打开 `release_device` 或 `acquire_device` 调试页
- **THEN** `serial` 仍为自由输入，不出现设备下拉
