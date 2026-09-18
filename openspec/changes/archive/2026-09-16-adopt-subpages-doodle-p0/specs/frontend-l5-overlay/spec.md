## ADDED Requirements

### Requirement: Input dialogs use registered paper skin tokens

含可编辑输入或危险确认的设备弹层（局域网连接、断开确认）MUST 继续由 Element Plus 对话框提供，其纸面描边、底色、硬阴影 MUST 引用 `tokens.css` 已登记令牌。系统 SHALL NOT 为「DialogForm」另建自绘 backdrop 或第二套 modal 实现。

#### Scenario: Network connect dialog stays Element Plus

- **WHEN** 用户在设备管理打开局域网连接
- **THEN** 弹层由 Element Plus 对话框渲染
- **AND** 页面 DOM 中不出现自绘全屏遮罩节点

#### Scenario: Dialog chrome colors come from tokens

- **WHEN** 检查该弹层外壳的边框与背景声明
- **THEN** 色值引用已登记令牌
- **AND** 不出现未登记的纯色字面量
