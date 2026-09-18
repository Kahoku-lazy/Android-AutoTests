## ADDED Requirements

### Requirement: 抓取方式恒为 Dump

工具条 SHALL NOT 提供抓取方式选择（「仅 Dump」/「仅 OCR」选项框）；「获取」MUST 以 `dump` 方式发起抓取。后端 `POST /api/inspector/capture` 的 `method` 入参与 `di_snapshots.ocr_json` 落库口径 MUST NOT 因本要求改变（仅前端不再发 `ocr`）。

#### Scenario: 工具条不再出现方式选项框

- **WHEN** 用户查看 `/inspector` 工具条
- **THEN** 只出现设备选择控件与「获取」按键，不出现「仅 Dump」「仅 OCR」
- **AND** 点击「获取」发出的抓取请求 `method` 为 `dump`

### Requirement: 元素表格常驻与固定 8 行分页

元素表格 MUST 常驻渲染表头与全部列；无数据时 MUST 由表格自身的空态承担提示，MUST NOT 用整块空态替换表格。空态提示文案 SHALL 统一为「未选中设备」——未选设备、未获取、筛选无匹配等任何无数据情形同一句。表格 SHALL 每页固定 8 行，并提供「第 X / Y 页 · 共 N 条」与「上一页 / 下一页」（无可翻页时禁用）；SHALL NOT 提供「显示行数」选择器。切换分区、筛选条件或搜索词后 MUST 回到第 1 页。

#### Scenario: 无数据时表格与表头常驻

- **WHEN** 用户打开 `/inspector` 且尚未获取任何快照
- **THEN** 表格渲染出选择列、缩略图、元素名称、标识、元素、指标、XPath 与 bounds 列及其表头
- **AND** 表体提示「未选中设备」，分页显示「第 1 / 1 页 · 共 0 条」且上一页 / 下一页禁用

#### Scenario: 固定 8 行一页

- **WHEN** 当前筛选结果共 27 行
- **THEN** 表格首屏只渲染 8 行，分页显示「第 1 / 4 页 · 共 27 条」
- **AND** 点「下一页」后渲染第 9–16 行且页码变为 2

#### Scenario: 不提供显示行数选择器

- **WHEN** 检查表格分页区
- **THEN** 不出现「显示行数」按钮组，每页行数恒为 8

#### Scenario: 切分区或筛选后回到第 1 页

- **WHEN** 用户先翻到第 3 页，再切换分区或修改筛选条件 / 搜索词
- **THEN** 页码回到第 1 页

#### Scenario: 筛选无匹配时同一句提示

- **WHEN** 筛选或搜索没有任何匹配元素
- **THEN** 表体同样显示「未选中设备」（统一口径，MUST NOT 另起一句）

### Requirement: 页面分区筹码与设备选择控件

页面分区列 MUST 为纵向硬边按键列：每项含分区名与元素计数徽标，未选中底色为天蓝 `var(--c-workflow)`、选中为柠黄 `var(--c-dashboard)`，并 MUST 提供「全部分区」复位项清除分区筛选。设备选择 MUST 为硬边触发键（始终可用的天蓝底，MUST NOT 呈灰键）+ 下拉浮层：下拉项 SHALL 展示设备型号 / 序列号与在线或使用中状态，被执行引擎占用或不可用的设备 MUST NOT 可选中。下拉浮层 SHALL 由 Element Plus 承担定位与键盘可达（MUST NOT 自绘下拉，也 MUST NOT 为浮层依赖自定义传送/皮肤）。

#### Scenario: 分区筹码带计数与选中态

- **WHEN** 已载入快照且分区列为 App头部 / 系统状态栏 / 内容区 等
- **THEN** 每个筹码显示分区名与该分区元素数，选中项为柠黄底、其余为天蓝底

#### Scenario: 全部分区复位

- **WHEN** 用户先点选某个分区，再点「全部分区」
- **THEN** 元素表格恢复列出当前筛选条件下的全部元素

#### Scenario: 设备下拉展示状态且占用项不可选

- **WHEN** 用户展开设备选择下拉
- **THEN** 每项显示设备型号或序列号与在线 / 使用中状态，被执行引擎占用的设备项不可选中

#### Scenario: 选中设备后触发键显示所选设备

- **WHEN** 用户在下拉中选定一个设备
- **THEN** 触发键显示该设备（型号或序列号），下拉收起

### Requirement: 检查器只保留 Dump 链路

检查器 MUST NOT 采集、保存或展示 OCR：抓取方式恒为 Dump；保存到元素定位 MUST NOT 写入页面级 OCR（请求不带 `include_ocr`）；手机屏幕 MUST NOT 绘制 OCR 框选、页脚与快照列表 MUST NOT 显示 OCR 计数、元素表 MUST NOT 存在 OCR 合并行。后端 `di_snapshots.ocr_json` 字段与 7 个端点契约 MUST NOT 因本要求改变（历史快照中的 OCR 数据不再展示）。

#### Scenario: 获取不产生 OCR 数据

- **WHEN** 用户执行一次「获取」
- **THEN** 抓取请求 `method` 为 `dump`，返回快照不含 OCR 文本

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

## MODIFIED Requirements

### Requirement: 按键可用性以颜色与提示表达

工具条按键 SHALL 以底色表达可用性：可用为天蓝底（`--c-workflow`），不可用为灰底（`--color-ink-79`）。设备选择触发键 SHALL 使用可用的天蓝底（其本身是选择设备的入口，MUST NOT 呈灰键、MUST NOT 提示「按键不可用」）。不可用按键 MUST 保持可点击（MUST NOT 用原生 `disabled` 静默拦截点击），点击时系统 MUST 提示「按键不可用，请先选择设备」。按键文字色 SHALL 为 `var(--ink)`，文字与底色对比度 MUST 不低于 4.5:1。「获取」在请求进行中 MAY 使用原生 disabled 表达忙碌态。

#### Scenario: 可用按键为蓝色

- **WHEN** 已选定可用设备且当前展示的是自有快照
- **THEN** 「获取」「历史快照」「已保存页面」「保存到元素定位」底色为 `--c-workflow`

#### Scenario: 未选设备时点「获取」提示

- **WHEN** 未选择设备时点击灰底的「获取」
- **THEN** 页面提示「按键不可用，请先选择设备」
- **AND** MUST NOT 发起抓取请求

#### Scenario: 无快照时「保存到元素定位」为灰

- **WHEN** 页面尚无快照、或当前展示的是「已保存页面」回看（无 `snapshot_id`）时点击「保存到元素定位」
- **THEN** 该按键底色为灰并提示「按键不可用，请先选择设备」
- **AND** MUST NOT 打开保存弹窗

#### Scenario: 无可选设备时设备下拉为空

- **WHEN** 设备池无可用设备
- **THEN** 设备选择下拉为空、「获取」为灰底，点击按上一 Scenario 提示

#### Scenario: 设备选择触发键始终为可用态

- **WHEN** 未选择设备时查看设备选择触发键
- **THEN** 触发键为天蓝底 `var(--c-workflow)`，点击展开设备下拉
- **AND** MUST NOT 提示「按键不可用，请先选择设备」，选定设备后触发键显示所选设备

### Requirement: 元素表格勾选驱动筛减保存

元素表格 MUST 提供选择列（每行一个复选框，表头提供全选）；勾选集合 MUST 决定「保存到元素定位」的元素范围：勾选非空且少于全量时按勾选筛减，勾选为全量时不筛减。表头全选 MUST 只作用于当前页所示行（每页 8 行），已勾选元素 MUST 跨页保持并计入保存范围。已勾选行 MUST 在切换分区、修改筛选条件或搜索词后保持勾选。

#### Scenario: 勾选后保存按勾选筛减

- **WHEN** 元素表格共 10 行，用户勾选其中 3 行后打开「保存到元素定位」并确认保存
- **THEN** 保存请求携带这 3 行的元素下标
- **AND** 目标页面新增或更新这 3 个元素

#### Scenario: 表头全选与取消全选

- **WHEN** 用户点击表头全选框
- **THEN** 当前页所示 8 行被勾选；再次点击则全部取消勾选
- **AND** 其他页已勾选的行 MUST NOT 被清空

#### Scenario: 未勾选时保存被拒

- **WHEN** 用户未勾选任何行就打开「保存到元素定位」并确认保存
- **THEN** 提示先勾选要保存的数据，MUST NOT 发起保存请求

#### Scenario: 勾选跨分区与筛选保持

- **WHEN** 用户勾选若干行后切换分区、切换筛选条件或输入搜索词
- **THEN** 已勾选行仍处于勾选状态，保存范围仍包含它们

#### Scenario: 已保存页面回看用同一张表格

- **WHEN** 用户从「已保存页面」打开一个已保存页面
- **THEN** 该页面元素以同一张结构表格展示，页面分区列为空态、指标列显示 —
- **AND** 缩略图、元素名称、标识、元素、XPath 与 bounds 列口径与快照视图一致

#### Scenario: 勾选跨页累计

- **WHEN** 用户在第 1 页勾选 3 行、翻到第 2 页再勾选 2 行
- **THEN** 保存范围包含这 5 行，翻回第 1 页时原勾选仍在

## REMOVED Requirements

### Requirement: 保存到元素定位不写入页面级 OCR

**Reason**: 检查器不再有 OCR 链路（抓取恒为 Dump，OCR 展示与合并行一并下线）；该要求中「检查器自身的 OCR 快照（手机屏幕 OCR 框选与 OCR 计数）SHALL 保留不受影响」的条款与本变更直接冲突。
**Migration**: 不落库条款由新增的「检查器只保留 Dump 链路」承接（保存请求仍不带 `include_ocr`、`el_pages.ocr_json` 仍为空）；存量清空迁移 `element_locator/0014_clear_page_ocr_json` 已在上一变更执行完毕，无需回滚。
