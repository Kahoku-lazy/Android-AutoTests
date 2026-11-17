## MODIFIED Requirements

### Requirement: Blocking overlays are provided by Element Plus

系统 MUST 以 Element Plus 覆盖层组件（`el-dialog` / `el-drawer` / `ElMessageBox`）提供所有阻塞型覆盖层；SHALL NOT 自建 backdrop 或 modal（自绘全屏遮罩 + 手写 ESC / 焦点 / 滚动锁）。

#### Scenario: Error notice overlay on login shell

- **WHEN** 登录或注册流程需要向用户展示服务端错误浮层
- **THEN** 该浮层由 Element Plus 对话框组件渲染
- **AND** 页面 DOM 中不出现自绘全屏遮罩节点，也无需手写 ESC 监听

#### Scenario: Name input dialog in workflow shell

<!-- 场景名沿自变更前：workflow 工作台名称弹层已随页面流模块删除，本场景改为以用例管理「新建项目」弹层守住名称输入对话框契约 -->

- **WHEN** 用户在用例管理新建项目
- **THEN** 名称输入以 Element Plus 对话框呈现，按 Enter 提交、名称为空时不提交
- **AND** 全仓不存在自建 backdrop 的名称输入弹层（原 workflow 工作台弹层已随模块删除）

#### Scenario: Thumbnail enlargement preview

- **WHEN** 用户在任一列表或工作台点击缩略图
- **THEN** 放大预览由 Element Plus 对话框呈现
- **AND** 预览字段内容与关闭行为与改造前一致

### Requirement: No browser-native dialogs

系统 SHALL NOT 使用 `window.confirm` / `window.alert` / `window.prompt`；危险操作确认 MUST 经 Element Plus 确认框（`ElMessageBox.confirm`）或既有共享 `ConfirmButton` 呈现。

#### Scenario: Delete file or directory

- **WHEN** 用户在用例管理目录树删除文件或目录
- **THEN** 出现 Element Plus 确认框而非浏览器原生对话框
- **AND** 取消时数据不变，确定时执行删除并保持原提示文案

#### Scenario: Canvas destructive actions

<!-- 场景名沿自变更前：画布危险操作确认已随页面流模块删除，本场景改为守住「零残留实现」 -->

- **WHEN** 检索画布双击连线、Delete 删除选中节点、清空画布的确认实现
- **THEN** 命中数为 `0`（已随页面流模块删除）
- **AND** 平台其余危险操作确认仍经 Element Plus 确认框或共享 `ConfirmButton`

#### Scenario: Empty-canvas overwrite guard

<!-- 场景名沿自变更前：空画布覆盖确认已随页面流模块删除，本场景改为守住「零残留实现」 -->

- **WHEN** 检索「保存时画布为空、服务器已有节点」的覆盖确认实现
- **THEN** 命中数为 `0`（已随页面流模块删除）

### Requirement: Non-modal overlays are out of scope

右键菜单、画布内 canvas / svg 叠加层、光标锚定 popover MUST NOT 按本能力的 modal 口径改造，除非其引入自绘全屏遮罩并阻断交互。

#### Scenario: Canvas annotation layer preserved

- **WHEN** 组件在截图之上绘制边界框或圈选矩形
- **THEN** 该叠加层保持在流内 canvas / svg 实现
- **AND** 不被替换为对话框

#### Scenario: Context menu preserved

- **WHEN** 用户在目录树等元素上右键
- **THEN** 菜单仍为光标锚定的上下文菜单
- **AND** 不被替换为对话框
