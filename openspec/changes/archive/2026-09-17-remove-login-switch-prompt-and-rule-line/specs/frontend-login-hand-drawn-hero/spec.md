## ADDED Requirements

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
