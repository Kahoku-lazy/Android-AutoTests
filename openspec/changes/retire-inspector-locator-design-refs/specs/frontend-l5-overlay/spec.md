## MODIFIED Requirements

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

- **WHEN** 用户在任一列表或工作台点击缩略图
- **THEN** 放大预览由 Element Plus 对话框呈现
- **AND** 预览字段内容与关闭行为与改造前一致

### Requirement: Blocking overlay skins are symmetric

`el-dialog`、`el-drawer` 与 `ElMessage` 的全局皮肤 MUST 统一由 `style.css` 提供，使对话框与抽屉使用同一套纸面语言（近直角圆角、墨色描边）；模块 SHALL NOT 为抽屉或对话框各补私有皮肤。

#### Scenario: Drawer shares the dialog paper language

- **WHEN** 在任一页面打开 `el-drawer`（如报告或页脚抽屉）
- **THEN** 抽屉的外观与 `el-dialog` 同源：近直角圆角与墨色描边来自 `style.css` 的全局皮肤
- **AND** 该模块的 `<style scoped>` 中没有为抽屉私写的边框 / 圆角 / 背景覆写

#### Scenario: Global skin is the single place for overlay chrome

- **WHEN** 检索全仓的 `.el-dialog` / `.el-drawer` 皮肤声明
- **THEN** 两者都命中 `frontend/src/style.css`
- **AND** 没有第二个文件重复声明抽屉或对话框的边框 / 圆角

### Requirement: Overlay close policy follows input-bearing content

含可编辑输入或危险操作确认的弹层 MUST 关闭「点击遮罩关闭」（`:close-on-click-modal="false"`），以防误触丢失未保存输入或误确认；纯展示 / 预览 / 只读列表选择的弹层 MUST 保持 Element Plus 默认（点遮罩即可关闭），SHALL NOT 一律写死某一种。内容持有本地状态且每次打开必须重置的弹层 SHALL 使用 `destroy-on-close`。

#### Scenario: Input-bearing dialog requires explicit close

- **WHEN** 打开含输入控件的弹层（新建项目 / 新建原型 / 重命名 / 新建目录 / 新建任务 / 试卷编辑器 / 局域网连接 / 导入文档）
- **THEN** 点击遮罩不关闭弹层，必须点取消 / 关闭按钮或按 ESC
- **AND** 该弹层带 `:close-on-click-modal="false"`

#### Scenario: Read-only overlay stays dismissible

- **WHEN** 打开纯展示 / 预览 / 只读列表选择的弹层（缩略图放大、快照抽屉、知识预览、步骤截图预览）
- **THEN** 点遮罩即可关闭（保持默认）
