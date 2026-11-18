## MODIFIED Requirements

### Requirement: 页内以两个 Tab 承载无线端口与日志关键词

串口日志页 SHALL 提供且仅提供两个 Tab：**无线端口** 与 **日志关键词**。默认选中「无线端口」。两个 Tab 的内容 MUST 分别满足 `device-log-port-console` 与 `device-log-keyword-catalog` 的要求；切换 Tab MUST NOT 触发监听开关变更，也 MUST NOT 发出任何写请求。页面 SHALL 仅向超级管理员提供关键词新建 / 编辑 / 删除入口（口径见 `device-log-keyword-catalog`），MUST NOT 向非超管提供这些入口，也 MUST NOT 提供下载日志备份的入口。

#### Scenario: 默认打开无线端口

- **WHEN** 用户进入串口日志页
- **THEN** 默认展示「无线端口」Tab 的端口表格

#### Scenario: 切到日志关键词

- **WHEN** 用户点击「日志关键词」
- **THEN** 展示关键词表（非超管只读），端口开关状态不变

#### Scenario: 只有两个 Tab

- **WHEN** 用户查看页内 Tab 条
- **THEN** 只有「无线端口」与「日志关键词」两个 Tab，没有第三个入口

#### Scenario: 切 Tab 不发写请求

- **WHEN** 用户来回切换两个 Tab
- **THEN** 除读取端口列表 / 关键词表外不发出写请求，开关值保持不变

#### Scenario: 超管可见维护入口

- **WHEN** 超级管理员打开「日志关键词」Tab
- **THEN** 页头出现「新建关键词」按钮，行内出现编辑 / 删除操作

#### Scenario: 非超管无维护入口

- **WHEN** 普通登录用户打开「日志关键词」Tab
- **THEN** 不出现新建按钮与行内编辑 / 删除操作，表格恰为四个数据列
