## MODIFIED Requirements

### Requirement: 串口日志 Tab 使用模块私有手稿 chip

串口日志页的 Tab 切换 MUST 由模块私有的手稿 chip 呈现（两枚：无线端口 / 日志关键词），MUST NOT 继续使用 Element Plus `el-tabs` 的默认下划线样式。未选中 MUST 为白底 + 2px 墨边 + 2px 位移硬影，选中 MUST 加 `--c-dashboard` 底。

#### Scenario: 两枚 chip 且选中态可辨

- **WHEN** 打开 `/serial-log`
- **THEN** 卡头出现两枚 chip，默认选中「无线端口」
- **AND** 选中项底色为柠黄，与未选中项肉眼可分，切换后下方内容随之切换
