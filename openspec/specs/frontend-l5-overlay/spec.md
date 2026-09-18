# frontend-l5-overlay Specification

## Purpose
定义前端 L5 覆盖层的实现口径：阻塞型覆盖层统一由 Element Plus 提供，禁止浏览器原生对话框与自建 backdrop / modal，并界定非 modal 浮层的边界，防止同层双实现复发。

## Requirements

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

### Requirement: Overlay visibility binding follows state ownership

覆盖层的可见性绑定 MUST 按**状态归属**确定，同一情形 MUST 只用一种写法：状态由本组件持有的 `ref`，或由本模块 store 持有且关闭时只需写回时，MUST 使用 `v-model`（含 `v-model="store.x"`）；可见性由条件表达式派生、或关闭时需联动清理 / 通知父组件时，MUST 使用 `:model-value` + `@update:model-value`（或 `@close`）显式处理；跨页复用的薄封装 MUST NOT 自持可见性，只接收 `visible` prop 并 emit 领域事件（`cancel` / `confirm` / `close`）。

#### Scenario: Store-owned overlay uses v-model

- **WHEN** 弹层的可见性由本模块 store 的布尔字段持有，且关闭时无需额外清理
- **THEN** 模板使用 `v-model="store.<字段>"` 绑定
- **AND** 不出现 `:model-value="store.<字段>"` + `@update:model-value="(v) => (store.<字段> = v)"` 的纯写回展开

#### Scenario: Derived visibility keeps an explicit binding

- **WHEN** 弹层的可见性由条件表达式派生（如 `creatingKind === 'folder'`），或关闭时必须联动清理选中态 / 取消提交
- **THEN** 模板使用 `:model-value` + `@update:model-value` 显式处理关闭
- **AND** 该写法 MUST NOT 被改成 `v-model`

#### Scenario: Reusable overlay wrapper emits domain events

- **WHEN** 弹层被封装为可跨页复用的组件
- **THEN** 组件只接收 `visible` prop 并在关闭 / 取消 / 确认时 emit 领域事件（`cancel` / `confirm` / `close`）
- **AND** 组件自身不持有可见性状态，也不负责把 `false` 写回父级

### Requirement: Blocking overlay skins are symmetric

`el-dialog`、`el-drawer` 与 `ElMessage` 的全局皮肤 MUST 统一由 `style.css` 提供，使对话框与抽屉使用同一套纸面语言（近直角圆角、墨色描边）；模块 SHALL NOT 为抽屉或对话框各补私有皮肤。

#### Scenario: Drawer shares the dialog paper language

- **WHEN** 在任一页面打开 `el-drawer`（如检查器快照抽屉）
- **THEN** 抽屉的外观与 `el-dialog` 同源：近直角圆角与墨色描边来自 `style.css` 的全局皮肤
- **AND** 该模块的 `<style scoped>` 中没有为抽屉私写的边框 / 圆角 / 背景覆写

#### Scenario: Global skin is the single place for overlay chrome

- **WHEN** 检索全仓的 `.el-dialog` / `.el-drawer` 皮肤声明
- **THEN** 两者都命中 `frontend/src/style.css`
- **AND** 没有第二个文件重复声明抽屉或对话框的边框 / 圆角

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

### Requirement: Blocking overlays escape transformed ancestors

阻塞型覆盖层（`el-dialog` / `el-drawer`）的遮罩 MUST 覆盖整个视口；系统 SHALL NOT 让覆盖层因祖先元素的 `transform` / `translate` / `rotate` / `scale` 建立包含块而被困在局部容器内。当覆盖层的挂载点位于带 transform 的容器之内时，该覆盖层 MUST Teleport 到 `body`（`el-dialog` 的 `append-to-body`），以同时保住容器的手绘倾斜与遮罩的全视口覆盖。容器自身的倾斜 MUST NOT 通过删除 `transform` 来规避本问题。

#### Scenario: Login error overlay mask covers the viewport

- **WHEN** 登录失败触发服务端错误浮层，而挂载它的 `.meeting-doodle` 带 `transform: rotate(1.2deg)`
- **THEN** `.el-overlay` 的实测矩形等于视口（1440×900 @ 0,0），而不是便签卡外框（约 424×403 @ 822,215）
- **AND** 浮层内容相对视口居中，而非相对便签卡居中

#### Scenario: Mask click closes from anywhere on the page

- **WHEN** 错误浮层打开后，用户点击便签卡范围之外的遮罩区域
- **THEN** 浮层关闭并向父组件 emit `close`
- **AND** 纯展示浮层保持 Element Plus 默认的点遮罩关闭（不写 `close-on-click-modal="false"`）

#### Scenario: Tilted container keeps its hand-drawn look

- **WHEN** 修复后检查登录页便签卡
- **THEN** `.meeting-doodle` 仍声明 `transform: rotate(1.2deg)`，视觉与修复前一致
- **AND** 该 transform 处留有指向覆盖层包含块约束的登记注释
