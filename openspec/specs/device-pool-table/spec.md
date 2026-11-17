# device-pool-table Specification

## Purpose
定义设备管理表格（`/devices` 表格视图）的列结构契约：列头以图标辅助扫读、首列承担设备身份、操作列把「主操作」与「次操作」分层，使同一张表在一屏内能回答「这是哪台设备、现在能不能用、下一步点哪里」。

## Requirements

### Requirement: Column headers carry an icon and keep a plain-text title

设备表每一列的列头 MUST 同时呈现「图标 + 纯文字列名」，图标 SHALL 来自该列配置（`columns[].icon`），SHALL NOT 拼接进列名文本。列名 MUST 保持纯文字，使表头 tooltip 与无障碍读屏仍只读出列名。图标 MUST 只出现在表头，SHALL NOT 出现在数据单元格（分辨率、活跃时间等数据列保持可等宽扫读）。

#### Scenario: Every header shows icon plus plain text

- **WHEN** 用户在 `/devices` 切换到表格视图
- **THEN** 七列的列头各自渲染一个图标与其纯文字列名
- **AND** 列名文本本身不含图标字符

#### Scenario: Data cells stay icon-free

- **WHEN** 检查任一数据行的分辨率列与活跃列
- **THEN** 单元格文本不含图标字符，等宽数字与时间文本可垂直对齐

### Requirement: First column presents device identity in one cell

设备表首列 MUST 以一个身份单元同时表达三件事：设备类型图标、当前在线状态点、设备标识（型号一行，序列号与连接地址一行）。状态点 MUST 与该行「状态」列的取值一致；离线设备的状态点 MUST 与在线设备可区分。首列 SHALL NOT 再用纯色块或伪元素作为第二状态载体（状态仍由「状态」列与状态点表达）。序列号与地址 MUST 保持可复制，SHALL NOT 因截断而丢失实际值。

#### Scenario: Identity cell shows icon, state dot and identifiers

- **WHEN** 用户查看一台在线设备的首列
- **THEN** 该单元同时呈现设备图标、在线色状态点、型号、序列号与连接地址
- **AND** 悬停序列号或地址可看到完整值

#### Scenario: Offline device is distinguishable at the icon

- **WHEN** 同一列表中同时存在在线设备与离线设备
- **THEN** 离线设备的状态点颜色与在线设备不同

### Requirement: Row actions split primary action from secondary menu

设备表操作列 MUST 至多呈现一个主操作（锁定 / 公开切换）作为可见按钮，其余操作（强制释放、删除）MUST 收进次操作菜单。USB 连接的设备行 SHALL 保持无操作。删除 MUST 仍经二次确认后执行；菜单项在不可执行时（如设备使用中时的删除）MUST 呈禁用态而不是被隐藏。把操作收进菜单 SHALL NOT 改变任何操作的既有权限判定与请求语义。

#### Scenario: Wi-Fi row shows one primary action and a menu

- **WHEN** 查看一台 Wi-Fi 连接、已锁定的设备行
- **THEN** 操作列只显示一个「已锁定」主操作按钮与一个次操作入口
- **AND** 「强制释放」「删除」出现在次操作菜单里

#### Scenario: USB row keeps an empty action column

- **WHEN** 查看一台 USB 连接的设备行
- **THEN** 操作列不呈现任何按钮或菜单入口

#### Scenario: Delete still asks for confirmation

- **WHEN** 用户从次操作菜单选择「删除」
- **THEN** 打开删除确认对话框，取消则设备不被删除
- **AND** 菜单项在设备处于使用中时呈禁用态

### Requirement: 设备表字号三档

设备管理表格的字号 MUST 分三档且与 BUG 单表同口径：六个列头 MUST 为 **16px** 且不折行；表内其余文本 MUST 为 **14px**（设备型号、序列号与地址、状态标签、连接胶囊、可见性胶囊、分辨率、活跃相对时间、操作胶囊与「⋯」）；**时间日期** MUST 为 **12px**（活跃列的「接入 YYYY-MM-DD HH:mm:ss」）。表格上方的控制区（分页文案、筛选下拉、搜索框、上一页 / 下一页、「开发调试」标签、「局域网」「刷新」键）MUST 同样使用 **14px**，SHALL NOT 停留在 Element Plus `size="small"` 的 12px。字号 MUST 取 `tokens.css` 的字号刻度，SHALL NOT 写像素字面量。

#### Scenario: 表头 16、内容 14

- **WHEN** 打开 `/devices` 表格视图并量测计算字号
- **THEN** 六个 `th` 的字号为 16px
- **AND** 型号、序列号行、胶囊、分辨率与操作键均为 14px

#### Scenario: 时间日期保持 12

- **WHEN** 查看活跃列的绝对时间
- **THEN** 「接入 …」这一行的字号为 12px
- **AND** 其上的相对时间（如「11 分钟前」）为 14px

#### Scenario: 表头不折行

- **WHEN** 六个列头在默认视口下渲染
- **THEN** 每个列头单行显示，不出现折行或省略号

#### Scenario: 控制区与表格同档

- **WHEN** 量测表格上方控制区各元素的计算字号
- **THEN** 分页文案、筛选下拉、搜索框、上一页 / 下一页、开发调试标签与工具条动作键均为 14px
- **AND** 不出现 12px 的 Element Plus `small` 按钮
