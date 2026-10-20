## RENAMED Requirements

- FROM: `### Requirement: 工具箱提供日志关键词只读入口`
- TO: `### Requirement: 串口日志页提供日志关键词只读入口`

## MODIFIED Requirements

### Requirement: 串口日志页提供日志关键词只读入口

串口日志页 SHALL 提供「日志关键词」Tab，以**表格**展示关键词对照，并 MUST 显示关键词总数、功能点总数与表格行数。该 Tab MUST NOT 绑定「交给助手」总闸，MUST NOT 进入 AI 工具箱的来源列表、生效清单、统计或「未装配」提示；页面 MUST NOT 出现「交给助手」开关。数据 MUST 来自串口日志模块的关键词目录接口 `GET /api/serial-log/keywords/`。

#### Scenario: 选中日志关键词来源

- **WHEN** 用户点击串口日志页的「日志关键词」Tab
- **THEN** 以表格列出关键词对照，并显示关键词数、功能点数与行数

#### Scenario: 该来源不参与装配

- **WHEN** 用户查看 AI 工具箱的来源列表、「助手此刻可用的工具」清单与统计
- **THEN** 不出现「日志关键词」来源，也不出现它的计数
- **AND** 日志关键词 Tab 上没有「交给助手」开关或其它装配入口

#### Scenario: 旧接口下线

- **WHEN** 请求 `/api/ai/log-keywords/`
- **THEN** 返回 404，不返回关键词数据，也不发生 3xx 跳转
