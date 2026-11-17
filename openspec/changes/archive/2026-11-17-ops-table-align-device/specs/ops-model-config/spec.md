## MODIFIED Requirements

### Requirement: 列表展示模型类型

模型配置列表 MUST 以「模型」为首列身份单元（模型名 + 「厂商 · 类型（· 音色）」副行），「模型类型」列 MUST 紧随该首列，取值为聊天、实时语音、语音合成，并以 chip 呈现（1.5px 墨边 + 类型色混底 + 14px 粗字）。记录缺少模型类型时 MUST 按聊天展示（副行与 chip 同时回退为聊天）。

#### Scenario: 三类配置并排展示
- **WHEN** 列表里同时存在聊天、实时语音、语音合成三条配置
- **THEN** 每条记录在模型首列的右侧显示与自身类型一致的类型 chip
- **AND** 首列副行同时给出厂商与类型

#### Scenario: 旧数据缺类型按聊天展示
- **WHEN** 某条历史记录没有模型类型字段
- **THEN** 类型 chip 显示聊天，副行也按聊天渲染

## ADDED Requirements

### Requirement: 模型配置列表的表格形态

模型配置列表的表纸 MUST 使用与设备管理、BUG 单一致的无影变体：保留共享描边与圆角，MUST NOT 绘制赭橙模块色位移硬影；同样 MUST NOT 被 `.doc-section` 外框再包一层，且 MUST NOT 传 `:border`。表格 MUST 使用 `table-layout="fixed"`，长地址由 tooltip 承担，MUST NOT 把表格撑出表纸而被裁切。字号 MUST 为表头 16px、正文 14px、次级 12px（首列副行）。

控制区 MUST 单行：左侧条数、中间关键字搜索、右侧「新建模型」。搜索 MUST 在页面前端过滤（模型名 / 厂商 / 类型 / 密钥环境变量 / 地址），MUST NOT 为它新增接口参数。操作列 MUST 为「编辑」主操作胶囊 + `⋯` 菜单，删除 MUST 收进 `⋯`，且 MUST 保留二次确认。列表 MUST NOT 为这一小体量数据加服务端分页。

#### Scenario: 无影表纸 + 固定布局
- **WHEN** 打开 `/ops/model-configs`
- **THEN** 表纸 `box-shadow` 为 `none`，页面里只有表纸一层框
- **AND** 超长 `wss://` 地址不会把表格撑出表纸，操作列完整可见

#### Scenario: 操作列收敛
- **WHEN** 查看任一模型行的操作列
- **THEN** 只有「编辑」胶囊与 `⋯` 两颗
- **AND** 点 `⋯` 里的删除仍会弹出二次确认

#### Scenario: 前端关键字过滤
- **WHEN** 在搜索框输入厂商名或模型名片段
- **THEN** 列表只保留命中项，条数随之更新
- **AND** 不产生新的网络请求
