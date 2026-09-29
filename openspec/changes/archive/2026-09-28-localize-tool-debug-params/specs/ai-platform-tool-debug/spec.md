## MODIFIED Requirements

### Requirement: 调试页按 schema 收集入参并展示结果

系统 SHALL 根据该工具的入参 schema 渲染表单（不含调用者身份字段），参数标签 MUST 以「**中文名（english_name）**」呈现并**保留英文参数名可见**，其后 MUST 标注「必填」或「可选」，并展示参数类型；参数中文说明 MUST 以悬浮提示等非铺开形式呈现，MUST NOT 把长段说明直接铺在表单中。当某参数的候选值由服务端给出时，系统 SHALL 把它渲染为可选择候选值的控件，MUST NOT 只渲染自由输入框；该控件 MUST 保留手输能力，候选清单不含目标值时用户仍 MUST 能填入该值。候选清单为空、加载中或加载失败时 MUST 以可读文案明示，且 MUST NOT 阻止用户执行（仍可手输后提交）。执行成功后 MUST 展示工具返回的数据内容。当返回含截图图像数据时，MUST 以图片预览展示，MUST NOT 把完整图像编码当作主要可读正文铺开。执行失败时 MUST 展示可读错误，MUST NOT 静默忽略。

#### Scenario: 参数标签为中文名加英文名

- **WHEN** 已登录用户打开 `read_device_log` 调试页
- **THEN** 参数标签形如「日志关键词搜索（keyword）」并标注「可选」，英文名 `keyword` 仍可见

#### Scenario: 必填参数标注必填

- **WHEN** 某参数在 schema 中标记为必填
- **THEN** 该参数标签旁标注「必填」

#### Scenario: 说明以提示形式呈现

- **WHEN** 参数带有中文说明
- **THEN** 该说明以悬浮提示等形式呈现，表单正文不被长段说明铺开

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

系统 SHALL 允许已登录用户按工具名读取平台业务工具的入参 schema（参数名、**中文名**、类型、是否必填、默认值、只读/写、说明）。每个参数 MUST 携带中文名（`label`）与中文说明（`hint`）：中文名取自平台集中维护的参数标签（支持工具级覆盖），未登记的参数 MUST 回退为英文参数名本身；中文说明取自工具 docstring 的 `Args` 段，取不到时 MUST 为空字符串，MUST NOT 编造。当某参数的可选值来自平台设备清单时，schema MUST 携带该参数的候选设备清单，每项 MUST 含可提交的取值与可读标签，且清单 MUST 已按请求者可见性收窄。候选值来自工具自身固定值域的参数 MUST 在本变更范围外（无候选声明，按自由输入处理）。未知工具名 MUST 返回 404。

#### Scenario: 读取已知工具 schema

- **WHEN** 已登录用户请求某已注册平台工具的 schema
- **THEN** 响应包含该工具名称、说明、只读标记与参数列表，且每个参数含 `name`、`label`、`hint`、`type`、`required`，参数列表不含调用者身份字段

#### Scenario: 已登记参数的中文名

- **WHEN** 已登录用户请求 `read_device_log` 的 schema
- **THEN** `keyword` 的中文名为「日志关键词搜索」，`at` 为「时间点」，`port` 为「日志端口」，`seconds` 为「查询跨度」

#### Scenario: 未登记参数回退英文名

- **WHEN** 某参数未在参数标签中登记
- **THEN** 该参数的 `label` 为英文参数名本身，MUST NOT 为空串

#### Scenario: 说明取自 docstring

- **WHEN** 工具 docstring 的 `Args` 段写有该参数的中文说明
- **THEN** 该参数的 `hint` 为该说明文本；docstring 未写该参数时 `hint` 为空字符串

#### Scenario: 未知工具 schema

- **WHEN** 已登录用户请求未注册工具名的 schema
- **THEN** 系统返回 404

#### Scenario: schema 携带候选设备清单

- **WHEN** 已登录用户请求 `tap_screen` 的 schema
- **THEN** `serial` 参数携带候选设备清单，每项含可提交取值与可读标签

#### Scenario: 无候选参数不带候选清单

- **WHEN** 已登录用户请求 `list_devices` 的 schema
- **THEN** 参数列表中不出现候选设备清单
