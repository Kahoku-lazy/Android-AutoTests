# frontend-login-hand-drawn-hero Specification

## Purpose

定义 `/login` 页 hand-drawn Hero 的可见行为：横线笔记本纸面（仅登录页）、左右分栏文案与 CTA、Meeting doodle 表单容器，以及登录/注册模式切换，使首屏对齐 showcase 而不改动认证业务契约。

## Requirements

### Requirement: Login page uses ruled notebook paper background
登录页（`/login`）SHALL 使用横线笔记本纸面背景（暖白底 + 重复横线），并可叠加稀疏不拦截指针的 doodle 装饰。该横线本背景 MUST 仅作用于登录页；系统 SHALL NOT 将横线本背景扩展到全站 L0 或工作台主区。

#### Scenario: Login shell shows ruled paper
- **WHEN** 用户打开 `/login`
- **THEN** 登录页根区域呈现暖白纸面与可见的横线笔记本纹
- **AND** 主内容区仍可交互（装饰层不拦截点击）

#### Scenario: Non-login pages keep existing paper treatment
- **WHEN** 用户进入已登录后的主区页面（如 `/dashboard`）
- **THEN** 该页背景仍遵循既有全站暖白纸面口径，不出现登录页专用的横线本纹

### Requirement: Hero is a two-column hand-drawn composition
登录页 Hero SHALL 呈现左右分栏：左侧为品牌标题与描述及模式 CTA；右侧为 Meeting doodle 钉板容器。左侧标题文案 MUST 为「AI 自动化测试平台」；描述 MUST 保留两行现有文案，且使用当前登录页描述行的品牌字体风格。系统 MUST NOT 在 Hero 中渲染动物贴纸板。

#### Scenario: Left column shows brand copy and mode CTAs
- **WHEN** 用户打开 `/login` 且不处于账号切换提示态
- **THEN** 左侧可见标题「AI 自动化测试平台」与两行描述文案
- **AND** 可见主按钮「登录」与次按钮「注册」

#### Scenario: Animal sticker board is removed
- **WHEN** 用户打开 `/login`
- **THEN** 页面中不出现动物贴纸板（无「AI助手 / 设备管理 / 用例编排 / 用例执行 / 报告生成」贴纸组合）

### Requirement: Meeting doodle hosts auth forms with mode title
右侧 Meeting doodle 容器 SHALL 承载登录或注册输入区；容器标题 MUST 随当前模式显示「登录」或「注册」。点击左侧「登录」SHALL 显示登录输入区；点击左侧「注册」SHALL 显示注册输入区。认证提交、校验与错误提示行为 MUST 与改版前等价。Meeting doodle 内的认证表单 MUST 为扁平字段布局；系统 SHALL NOT 在 Meeting doodle 内再嵌套 `.ac-card` / `el-card` 作为表单外壳。

#### Scenario: Login CTA reveals login form in Meeting doodle
- **WHEN** 用户点击左侧「登录」
- **THEN** Meeting doodle 标题为「登录」
- **AND** 容器内显示登录输入区（含账号、密码等既有字段）

#### Scenario: Register CTA reveals register form in Meeting doodle
- **WHEN** 用户点击左侧「注册」
- **THEN** Meeting doodle 标题为「注册」
- **AND** 容器内显示注册输入区（含既有注册字段）

#### Scenario: Auth form is flat inside Meeting doodle
- **WHEN** 用户打开 `/login` 且处于登录或注册表单态
- **THEN** Meeting doodle 内可见输入框与提交按钮
- **AND** Meeting doodle 内不存在嵌套的 `.ac-card` / `el-card` 表单外壳

#### Scenario: Auth business flow remains unchanged
- **WHEN** 用户在 Meeting doodle 内完成合法登录或注册提交
- **THEN** 认证请求与成功/失败反馈路径与改版前一致（无新 API、无字段契约变更）

### Requirement: Login page has only login and register modes

登录页（`/login`）的视图态 SHALL 只有 `login` 与 `register` 两种；系统 SHALL NOT 提供账号切换提示态。当浏览器已存在已登录账号时，页面 SHALL 直接呈现登录输入区，而不是先显示切换提示卡。左栏「登录」「注册」模式 CTA SHALL 在 `/login` 上恒可见，SHALL NOT 被任何视图态隐藏。

#### Scenario: Existing account does not trigger a switch prompt

- **WHEN** 本地已存有账号（token 池非空）且用户访问 `/login`
- **THEN** 页面直接显示登录输入区，Meeting doodle 标题为「登录」
- **AND** 页面中不出现「检测到已登录账号」「切换到 <账号>」「添加新账号」这类切换提示内容

#### Scenario: Mode CTA is always visible

- **WHEN** 用户打开 `/login`（无论本地是否已有账号、无论当前是 login 还是 register 态）
- **THEN** 左栏 `[data-testid="login-mode-login"]` 与 `[data-testid="login-mode-register"]` 两个 CTA 均存在且可点击
- **AND** 点击后分别切到登录输入区与注册输入区
