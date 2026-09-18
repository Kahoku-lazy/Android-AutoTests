## Purpose

定义前端 L5 覆盖层的实现口径：阻塞型覆盖层统一由 Element Plus 提供，禁止浏览器原生对话框与自建 backdrop / modal，并界定非 modal 浮层的边界，防止同层双实现复发。

## ADDED Requirements

### Requirement: Blocking overlays are provided by Element Plus

系统 MUST 以 Element Plus 覆盖层组件（`el-dialog` / `el-drawer` / `ElMessageBox`）提供所有阻塞型覆盖层；SHALL NOT 自建 backdrop 或 modal（自绘全屏遮罩 + 手写 ESC / 焦点 / 滚动锁）。

#### Scenario: Error notice overlay on login shell

- **WHEN** 登录或注册流程需要向用户展示服务端错误浮层
- **THEN** 该浮层由 Element Plus 对话框组件渲染
- **AND** 页面 DOM 中不出现自绘全屏遮罩节点，也无需手写 ESC 监听

#### Scenario: Name input dialog in workflow shell

- **WHEN** 用户在 workflow 工作台新建目录或页面流
- **THEN** 名称输入以 Element Plus 对话框呈现
- **AND** 打开后输入框自动聚焦并全选、按 Enter 提交、名称为空时不提交

#### Scenario: Thumbnail enlargement preview

- **WHEN** 用户在 device-inspector 点击元素缩略图或结构缩略图
- **THEN** 放大预览由 Element Plus 对话框呈现
- **AND** 预览字段内容与关闭行为与改造前一致

### Requirement: No browser-native dialogs

系统 SHALL NOT 使用 `window.confirm` / `window.alert` / `window.prompt`；危险操作确认 MUST 经 Element Plus 确认框（`ElMessageBox.confirm`）或既有共享 `ConfirmButton` 呈现。

#### Scenario: Delete file or directory

- **WHEN** 用户删除工作流文件或目录
- **THEN** 出现 Element Plus 确认框而非浏览器原生对话框
- **AND** 取消时数据不变，确定时执行删除并保持原提示文案

#### Scenario: Canvas destructive actions

- **WHEN** 用户在画布双击连线、按 Delete 删除选中节点、或清空画布
- **THEN** 三处均出现 Element Plus 确认框
- **AND** 取消时画布数据不变，确定后操作与状态提示与原实现一致

#### Scenario: Empty-canvas overwrite guard

- **WHEN** 保存时画布为空、服务器已有节点，且调用方要求确认覆盖
- **THEN** 覆盖确认由 Element Plus 确认框发起
- **AND** 取消时不覆盖服务器数据并保持拒绝保存的语义

### Requirement: Single implementation per overlay scenario

同一覆盖层场景 MUST 只保留一种实现；同层 SHALL NOT 同时存在 Element Plus 实现与自建实现。

#### Scenario: Image preview scenario convergence

- **WHEN** 审视全站图片或缩略图放大预览场景
- **THEN** 全部由 Element Plus 对话框实现
- **AND** 不再存在模块自建的遮罩版预览

### Requirement: Non-modal overlays are out of scope

右键菜单、画布内 canvas / svg 叠加层、光标锚定 popover MUST NOT 按本能力的 modal 口径改造，除非其引入自绘全屏遮罩并阻断交互。

#### Scenario: Canvas annotation layer preserved

- **WHEN** 组件在截图之上绘制边界框或圈选矩形
- **THEN** 该叠加层保持在流内 canvas / svg 实现
- **AND** 不被替换为对话框

#### Scenario: Context menu preserved

- **WHEN** 用户在目录树、画布节点或连线上右键
- **THEN** 菜单仍为光标锚定的上下文菜单
- **AND** 不被替换为对话框
