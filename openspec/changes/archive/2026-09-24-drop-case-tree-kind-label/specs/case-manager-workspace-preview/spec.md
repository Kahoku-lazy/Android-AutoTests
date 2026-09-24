## ADDED Requirements

### Requirement: 目录树行不标注节点类型且在窄左栏内不溢出

用例管理工作台目录树的每一行 MUST 通过图标与尾部信息表达节点类型，MUST NOT 再单独渲染「目录」或「文件」文字标签。行内的名称、尾随信息与进入指示 MUST 在左栏宽度（取 T0 分栏档位 `--layout-pane-left`）内**完整容纳且不横向溢出**：名称 MUST 可压缩并在超长时以省略号呈现（完整值 MUST 可经 `title` 获取），尾随信息 MUST NOT 被截断——文件行的时间 MAY 省去年份，完整时间 MUST 可经 `title` 获取；进入指示 MAY 以图标级紧凑形式呈现。目录行 MUST 尾随其直接子项数量。行内交互（拖拽、右键菜单、批量勾选）MUST 保持不变。

#### Scenario: 行内不再出现类型文字标签

- **WHEN** 读取目录树任一行的可见文本
- **THEN** MUST NOT 出现独立的「目录」或「文件」文字标签
- **AND** 该行的图标与尾随信息 MUST 仍在

#### Scenario: 目录与文件仍可区分

- **WHEN** 对比同一棵树中的一个目录行与一个文件行
- **THEN** 目录行的图标为文件夹形态且尾随「N 项」
- **AND** 文件行的图标为文档形态且尾随时间

#### Scenario: 行不横向溢出

- **WHEN** 量测目录树任一行的 `scrollWidth` 与 `clientWidth`
- **THEN** 两者 MUST 相等（MUST NOT 出现被裁剪的内容）
- **AND** 名称超长时 MUST 以省略号呈现，且其 `title` MUST 为完整名称

#### Scenario: 文件行时间可获取完整值

- **WHEN** 文件行的时间以紧凑形式呈现（省去年份）
- **THEN** 该元素的 `title` MUST 为完整时间戳
- **AND** 右栏预览的「时间」列 MUST 仍呈现完整时间戳

#### Scenario: 行交互不回归

- **WHEN** 用户对去掉标签后的行执行拖拽、右键或批量勾选
- **THEN** 移动 / 重命名 / 删除 / 勾选行为与改动前一致
