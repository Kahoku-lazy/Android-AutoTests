## ADDED Requirements

### Requirement: Overlay close policy follows input-bearing content

含可编辑输入或危险操作确认的弹层 MUST 关闭「点击遮罩关闭」（`:close-on-click-modal="false"`），以防误触丢失未保存输入或误确认；纯展示 / 预览 / 只读列表选择的弹层 MUST 保持 Element Plus 默认（点遮罩即可关闭），SHALL NOT 一律写死某一种。内容持有本地状态且每次打开必须重置的弹层 SHALL 使用 `destroy-on-close`。

#### Scenario: Input-bearing dialog requires explicit close

- **WHEN** 打开含输入控件的弹层（新建项目 / 新建原型 / 重命名 / 新建目录 / 新建任务 / 试卷编辑器 / 局域网连接 / 导入文档 / 保存到元素定位）
- **THEN** 点击遮罩不关闭弹层，必须点取消 / 关闭按钮或按 ESC
- **AND** 该弹层带 `:close-on-click-modal="false"`

#### Scenario: Read-only overlay stays dismissible

- **WHEN** 打开纯展示 / 预览 / 只读列表选择的弹层（缩略图放大、快照抽屉、已保存页面选择、知识预览、步骤截图预览）
- **THEN** 点遮罩即可关闭（保持默认）
- **AND** 该弹层不写 `close-on-click-modal`

### Requirement: Store layer does not ask users via modal dialogs

Pinia store MUST NOT 直接调用 `ElMessageBox`（或等价模态确认）向用户询问决策；需要用户确认时 MUST 通过调用方传入的回调把决策交回 UI 层。非阻塞 `ElMessage`（Toast）提示不在本约束内。

#### Scenario: Empty-canvas overwrite confirmation is owned by the caller

- **WHEN** 保存时画布为空、服务器已有节点，且调用方要求确认覆盖
- **THEN** store 通过 `confirmEmptyOverwrite(remoteNodes)` 回调询问，弹窗由 UI 层实现
- **AND** 回调返回 `false`（用户取消）时不写入服务器数据

#### Scenario: No modal confirmation inside stores

- **WHEN** 检索 `frontend/src` 中所有 store 文件里的 `ElMessageBox`
- **THEN** 命中数为 0
- **AND** 需要确认的 store 分支都改为回调 / 返回值交给 UI 层
