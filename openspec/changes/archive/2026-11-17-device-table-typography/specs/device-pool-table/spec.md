## ADDED Requirements

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
