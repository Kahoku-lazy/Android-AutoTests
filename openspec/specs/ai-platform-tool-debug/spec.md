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
系统 SHALL 根据该工具的入参 schema 渲染表单（不含调用者身份字段）。执行成功后 MUST 展示工具返回的数据内容。当返回含截图图像数据时，MUST 以图片预览展示，MUST NOT 把完整图像编码当作主要可读正文铺开。执行失败时 MUST 展示可读错误，MUST NOT 静默忽略。

#### Scenario: 无参只读工具执行成功
- **WHEN** 已登录用户在 `get_online_devices` 调试页不填额外参数并执行
- **THEN** 页面展示该工具返回的设备列表数据（或等价 JSON）

#### Scenario: 带参工具表单含必填项
- **WHEN** 用户打开需要 `serial` 的平台工具调试页
- **THEN** 表单出现 `serial` 输入，且不出现调用者身份字段

#### Scenario: 截图工具结果出图
- **WHEN** 有权限的用户成功执行 `screenshot_page`
- **THEN** 页面展示截图预览与摘要字段（如 serial / 包名）
- **AND** 不以完整图像编码作为主要阅读内容

### Requirement: 登录用户可读取工具入参 schema
系统 SHALL 允许已登录用户按工具名读取平台业务工具的入参 schema（参数名、类型、是否必填、默认值、只读/写、说明）。未知工具名 MUST 返回 404。

#### Scenario: 读取已知工具 schema
- **WHEN** 已登录用户请求某已注册平台工具的 schema
- **THEN** 响应包含该工具名称、说明、只读标记与参数列表，且参数列表不含调用者身份字段

#### Scenario: 未知工具 schema
- **WHEN** 已登录用户请求未注册工具名的 schema
- **THEN** 系统返回 404

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
