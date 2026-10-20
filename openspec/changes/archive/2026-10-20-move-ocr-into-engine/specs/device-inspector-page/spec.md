## MODIFIED Requirements

### Requirement: 抓取方式恒为 Dump

工具条 SHALL NOT 提供抓取方式选择（「仅 Dump」/「仅 OCR」选项框）；「获取」MUST 以 `dump` 方式发起抓取。后端 `POST /api/inspector/capture` MUST 只接受 `method` 为 `dump`（缺省亦为 `dump`）。`method` 为 `ocr` 或其他值时 MUST 以 400 拒绝，且 MUST NOT 落库、MUST NOT 执行识别。新抓取写入的 OCR 载荷 MUST 为空。历史快照已存的 `di_snapshots.ocr_json` 与 `ocr_count` MUST 保留，不迁移、不清空。

#### Scenario: 工具条不再出现方式选项框

- **WHEN** 用户查看 `/inspector` 工具条
- **THEN** 只出现设备选择控件与「获取」按键，不出现「仅 Dump」「仅 OCR」
- **AND** 点击「获取」发出的抓取请求 `method` 为 `dump`

#### Scenario: 拒绝 OCR 抓取

- **WHEN** 调用方以 `method=ocr` 请求 `POST /api/inspector/capture`
- **THEN** 响应状态为 400
- **AND** 不产生新快照，不执行页面文本识别

### Requirement: 检查器只保留 Dump 链路

检查器 MUST NOT 采集、保存或展示 OCR，也 MUST NOT 提供页面文本识别入口：抓取方式恒为 Dump；保存到元素定位 MUST NOT 写入页面级 OCR（请求不带 `include_ocr`）；手机屏幕 MUST NOT 绘制 OCR 框选、页脚与快照列表 MUST NOT 显示 OCR 计数、元素表 MUST NOT 存在 OCR 合并行。新抓取返回的快照 MUST NOT 含 OCR 文本。历史快照详情 MUST 仍读出该行已存的 OCR 文本与计数，界面 MUST NOT 展示这些文本。检查器对其他模块公开的能力 MUST NOT 包含对当前页面执行文本识别的函数。

#### Scenario: 获取不产生 OCR 数据

- **WHEN** 用户执行一次「获取」
- **THEN** 抓取请求 `method` 为 `dump`，返回快照不含 OCR 文本
- **AND** 该快照的 OCR 计数为 0

#### Scenario: 保存到元素定位不写页面级 OCR

- **WHEN** 用户用一份历史含 OCR 数据的快照保存到元素定位
- **THEN** 请求体不含 `include_ocr`，目标页面的 `ocr_json` 为空

#### Scenario: 手机屏幕不绘制 OCR 框选

- **WHEN** 打开一份历史 OCR 快照
- **THEN** 手机屏幕只绘制元素框选，不绘制 OCR 框选
- **AND** 点击屏幕不会选中 OCR 文本

#### Scenario: 页脚与快照列表不显示 OCR 计数

- **WHEN** 查看页脚与「历史快照」抽屉
- **THEN** 只显示元素数量，不出现「N OCR」字样

#### Scenario: 历史快照仍可读出已存 OCR

- **WHEN** 读取一份抓取时写入过 OCR 文本的历史快照详情
- **THEN** 详情中仍包含当时保存的 OCR 文本与计数
