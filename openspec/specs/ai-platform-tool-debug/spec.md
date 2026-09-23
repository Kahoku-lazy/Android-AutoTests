# ai-platform-tool-debug Specification

## Purpose
让登录用户在 AI 工具箱对平台业务工具做一次真实调用：按入参 schema 填写参数、查看返回数据；写操作仅超级管理员可执行并须二次确认。

## Requirements

### Requirement: 装配台提供平台工具调试入口
系统 SHALL 在 AI 工具箱「平台业务」目录的每张平台工具卡上提供「调试」入口。激活后 MUST 进入该工具的调试子页，且 MUST 在子页正文顶部提供回到工具箱的可见回退（返回芯片或面包屑），MUST NOT 把浏览器后退当作唯一回退手段。停用状态的平台工具 MUST 仍显示该入口。

#### Scenario: 从工具卡进入调试页
- **WHEN** 已登录用户在装配台点击某平台工具的「调试」
- **THEN** 进入该工具的调试子页，页内可见工具名称与说明
- **AND** 正文顶部可见回到「AI工具箱」的控件

#### Scenario: 停用工具仍可进入调试
- **WHEN** 某平台工具在装配台为已停用
- **THEN** 「调试」入口仍可用，进入后可查看说明与入参表单

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

### Requirement: 只读工具任意登录用户可调用
系统 SHALL 允许已登录用户对 `read_only` 为真的平台工具发起一次真实调用，并将 JWT 中的调用者身份注入工具，MUST NOT 接受请求体覆盖该身份。调用 MUST 执行与智能体相同的平台工具函数，MUST NOT 为此新建 Agent 任务，MUST NOT 使用内部服务令牌网关。

#### Scenario: 登录用户调用只读工具
- **WHEN** 已登录非超级管理员调用 `list_devices`
- **THEN** 系统执行该工具并返回数据

#### Scenario: 请求体不得覆盖调用者身份
- **WHEN** 调用请求体包含调用者身份字段
- **THEN** 系统忽略该字段，使用 JWT 身份注入

### Requirement: 写工具仅超级管理员可调用且须确认
系统 SHALL 仅允许超级管理员对 `read_only` 为假的平台工具发起调用。非超级管理员请求 MUST 返回 403 且 MUST NOT 执行工具。调试页在提交写工具前 MUST 要求二次确认；用户取消确认 MUST NOT 发出调用。非超级管理员打开写工具调试页时 MUST 可查看说明与表单，MUST 禁用执行控件。

#### Scenario: 超管确认后调用写工具
- **WHEN** 超级管理员在写工具调试页填写参数、通过确认对话框并提交
- **THEN** 系统执行该工具并返回结果

#### Scenario: 超管取消确认不调用
- **WHEN** 超级管理员点击执行后在确认框选择取消
- **THEN** 系统不发出调用请求

#### Scenario: 非超管 API 调用写工具被拒
- **WHEN** 非超级管理员直接请求调用写工具（如 `acquire_device`）
- **THEN** 系统返回 403 且不执行该工具

#### Scenario: 非超管写工具页禁用执行
- **WHEN** 非超级管理员打开写工具调试页
- **THEN** 可见说明与入参表单，执行控件不可用

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

### Requirement: 调试调用失败按成因区分状态码

平台工具调试调用失败时，系统 MUST 按成因区分响应状态码：请求者可自行修正的错误（未知参数、参数类型无法转换、缺少必填参数、前置条件不满足等）MUST 返回 4xx；工具或引擎内部故障（实现缺陷、设备侧异常等）MUST 返回 5xx，MUST NOT 折成 4xx。内部故障发生时，系统 MUST 记录服务端日志（至少含工具名与请求者身份），再返回可读错误。响应体 MUST 沿用统一错误信封（含可读 `message`）。

#### Scenario: 内部故障返回 5xx 并落日志

- **WHEN** 已登录用户调用某平台工具，且该工具或引擎抛出非入参类异常
- **THEN** 系统返回 5xx
- **AND** 该次调用留下服务端错误日志（含工具名与请求者）

#### Scenario: 入参错误仍是 4xx

- **WHEN** 已登录用户调用只读工具并传入未知参数或无法转换的参数值
- **THEN** 系统返回 400，且响应含可读 `message`

#### Scenario: 未知工具仍是 404

- **WHEN** 已登录用户调用未注册工具名
- **THEN** 系统返回 404

#### Scenario: 写工具权限拒绝仍是 403

- **WHEN** 非超级管理员调用写工具
- **THEN** 系统返回 403 且不执行该工具

### Requirement: 调试失败展示服务端可读错误

调试页加载入参 schema 或执行工具失败时，系统 MUST 展示服务端错误信封中返回的可读 `message`（存在时），MUST NOT 只展示 HTTP 状态码原文（如 `Request failed with status code 400`）。服务端未提供 `message` 时，系统 SHALL 展示按状态码归类的可读提示，MUST NOT 静默忽略错误。本地参数校验失败（如缺少必填参数）MUST 展示其自身的本地提示文案，MUST NOT 被上述服务端错误格式化覆盖。

#### Scenario: 展示服务端返回的失败原因

- **WHEN** 用户执行工具，服务端返回带 `message` 的失败响应
- **THEN** 调试页展示该 `message` 文本
- **AND** MUST NOT 只显示 `Request failed with status code` 一类状态码原文

#### Scenario: schema 加载失败同样展示服务端原因

- **WHEN** 调试页加载某工具 schema 失败且响应带 `message`
- **THEN** 页面错误区展示该 `message`

#### Scenario: 本地参数校验提示不被覆盖

- **WHEN** 用户未填写必填参数即点击执行
- **THEN** 页面提示「请填写必填参数」一类本地文案
- **AND** MUST NOT 变成网络类兜底文案
