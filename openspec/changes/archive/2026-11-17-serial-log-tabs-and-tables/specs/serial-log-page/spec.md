## ADDED Requirements

### Requirement: 串口日志 Tab 使用模块私有手稿 chip

串口日志页的 Tab 切换 MUST 由模块私有的手稿 chip 呈现（两枚：无线端口 / 日志关键词），MUST NOT 继续使用 Element Plus `el-tabs` 的默认下划线样式。未选中 MUST 为白底 + 2px 墨边 + 2px 位移硬影，选中 MUST 加 `--c-dashboard` 底。共享件 `AppTabs` SHALL NOT 为本页修改（其它页仍在使用）。

#### Scenario: 两枚 chip 且选中态可辨

- **WHEN** 打开 `/serial-log`
- **THEN** 卡头出现两枚 chip，默认选中「无线端口」
- **AND** 选中项底色为柠黄，与未选中项肉眼可分，切换后下方内容随之切换

### Requirement: 端口表支持只看监听中与分页

端口 Tab MUST 提供「只看监听中」筛选，开启后 MUST 只保留 `enabled` 为真的端口，并 MUST 显示当前命中数与总数。表格 MUST 分页，每页固定 **10** 行，行数取值 MUST 来自模块 `constants.ts`。分页与筛选 MUST NOT 触发写请求。

#### Scenario: 只看监听中

- **WHEN** 端口表存在已停止监听的端口，用户开启「只看监听中」
- **THEN** 列表只剩监听中的端口，计数显示命中数与总数
- **AND** 关闭筛选后恢复全部端口

#### Scenario: 分页固定 10 行

- **WHEN** 端口多于 10 个
- **THEN** 表格按每页 10 行分页，出现「第 X / Y 页」与上一页 / 下一页
