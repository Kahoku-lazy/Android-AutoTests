## ADDED Requirements

### Requirement: 用例工作台与元素定位工作台共用同一套工作台视觉

用例管理项目工作台的**左栏目录树与工具栏** MUST 与元素定位项目工作台逐项同源，差异 MUST 只限模块色、右栏数据列集与业务动作文案。具体：

1. 树行 MUST 默认不绘制可见描边（用 2px 透明描边占位，避免悬停 / 选中时行高跳动），悬停 MUST 给底色，选中行 MUST 给 2px 墨色实线描边 + `--app-shadow-sm` 硬阴影 + 底色；行圆角与内边距 MUST 取与元素定位同档的圆角 / 间距令牌。
2. 层级 MUST 以不小于 18px 的缩进加子层容器左边界虚线引导线表达；展开箭头 MUST 使用 el-tree 原生箭头，MUST NOT 用行尾自绘符号代替。
3. 文件行的进入指示 MUST 紧贴名称右侧，MUST NOT 推到行尾远端。
4. 目录行 MUST 尾随其直接子项数量，子项为 0 时 MUST 显示「空」。
5. 工具栏 MUST NOT 常驻静态位置面包屑；工具栏按钮 MUST 具备与元素定位一致的 hover 左上位移、disabled 半透明与危险态（红底 + 浅色字）皮肤；内边距 MUST 取间距令牌。

#### Scenario: 行默认态与选中态同源

- **WHEN** 打开用例工作台、指针不在任何行上
- **THEN** 每一行的 `border-color` MUST 为透明值（不绘制可见描边）
- **AND** 选中某文件后，该行 MUST 出现 2px 墨色实线描边与 `--app-shadow-sm` 硬阴影

#### Scenario: 层级引导线与原生箭头

- **WHEN** 观察含子节点的目录行与其子行
- **THEN** 子层容器左边界 MUST 有 `2px dotted` 引导线
- **AND** 目录行 MUST 使用 el-tree 原生展开箭头（MUST NOT 出现自绘的行尾 `▾`）

#### Scenario: 进入指示紧贴名称

- **WHEN** 测量文件行中「进入」指示左边缘与文件名称右边缘的距离
- **THEN** 该距离 MUST 小于 24px

#### Scenario: 空目录表达为空

- **WHEN** 某目录下没有任何文件
- **THEN** 该目录行尾 MUST 显示「空」，MUST NOT 显示「0」或「0 项」

#### Scenario: 工具栏与按钮皮肤同源

- **WHEN** 打开用例工作台并测量工具栏
- **THEN** MUST NOT 出现静态的「项目根 / 全部」面包屑
- **AND** 工具栏按钮 hover 时 MUST 出现左上 1px 位移，disabled 时 MUST 半透明
- **AND** 批量模式下的删除按钮 MUST 为红底 + 浅色字
