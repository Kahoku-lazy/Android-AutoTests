## MODIFIED Requirements

### Requirement: 验收模型只输出六字段

验收模型 SHALL 只输出六个字段的 JSON：`result`、`click_timer`、`logAssertionTimer`、`logAssertionInfo`、`screenshot`、`actual`。`result` MUST 为 `PASS`（实际结果符合断言）或 `FAIL`（不符合或无法确认），MUST NOT 再使用布尔值。`click_timer` MUST 为**点击前的时间戳**，取平台下发给它的执行侧点击时刻（原文照抄）；本步没有点击时 SHALL 为空字符串。`logAssertionTimer` MUST 为**检测到日志关键词的时间戳**，取日志检查工具返回的命中时间戳（原文照抄，多次命中取最早一次）；未检测到或未检查时 SHALL 为空字符串。`logAssertionInfo` SHALL 为**本轮检查的日志关键词**，由平台按对检查工具的实际调用自动填写（模型自己写的值以工具调用为准）。`screenshot` SHALL 为空字符串——截图工具只回图片数据、不返回路径，平台不采集该字段，模型 MUST NOT 编造路径。`actual` MUST 用一句话描述截图里实际看到了什么。该输出 MUST NOT 含 `action` 与 `assert` 两个键。任何取不到的坐标 MUST 留空字符串，模型 MUST NOT 编造时间戳或文件路径。

#### Scenario: 通过的一次验收回六字段

- **WHEN** 某步执行后在设备上截图、截图与断言相符，且检查工具在窗口内检测到该关键词
- **THEN** 该次验收 JSON 恰好只有六个键，`result` 为 `PASS`，`click_timer` 等于平台给出的本步点击前时间戳，`logAssertionTimer` 等于检测到的时间戳，`logAssertionInfo` 等于所检查的关键词，`screenshot` 为空字符串（截图工具不返回路径）

#### Scenario: 未采集日志时为空的如实口径

- **WHEN** 本步没有日志证据（未标记核对 / 端口未监听 / 窗口内未命中）
- **THEN** `logAssertionTimer` 为空字符串，`result` 仍按截图与断言的实际比对给出

#### Scenario: 纯看页面、没有点击的验收

- **WHEN** 某步未产生点击（只读断言）
- **THEN** `click_timer` 为空字符串，其余字段按实际给出

#### Scenario: 输出不含 action 与 assert

- **WHEN** 检查任意一次验收结果
- **THEN** 该 JSON 不含 `action` 键、也不含 `assert` 键

#### Scenario: 输出无效时如实判不通过

- **WHEN** 模型未返回可解析的六字段 JSON
- **THEN** 该次验收按 `FAIL` 处理，`click_timer` / `logAssertionTimer` / `logAssertionInfo` / `screenshot` 均为空字符串，`actual` 给出可读说明，MUST NOT 由平台编造证据坐标

### Requirement: 任务详情页按新契约呈现验收

任务详情页的验收段 SHALL 呈现该步验收的 `result` 与 `actual`，并在 `logAssertionTimer` 非空时给出「日志断言时间」。验证截图不落盘、平台不采集截图路径，因此该段 MUST NOT 呈现验证截图路径，也不得为缺失的路径渲染空壳区块；对存量旧记录里已有的验证截图路径 SHALL 仍按文本呈现，路径指向的图片存在时 MUST 可直接查看原图。该段 MUST 为只读展示。对存量旧记录（`action` / `assert` / `actual` + 布尔 `result`）SHALL 继续如实呈现，MUST NOT 报错、MUST NOT 留空壳。同一处点击的「点击前时间」已在执行结果段呈现，验收段 MUST NOT 重复堆一遍同名行。

#### Scenario: 新记录呈四件

- **WHEN** 打开含新契约记录的任务详情并展开某步尝试
- **THEN** 验收段可见验收结果、实际结果说明、日志断言时间（有则显示）与「该步不采集验证截图路径」的如实标注四件内容，MUST NOT 出现可点击的验证截图路径

#### Scenario: 未检测到日志时如实不显示该行

- **WHEN** 该次验收的 `logAssertionTimer` 为空字符串
- **THEN** 页面不出现「日志断言时间」行，MUST NOT 用其它时间戳顶替

#### Scenario: 存量旧记录兼容

- **WHEN** 打开只有旧字段（`action` / `assert` / `actual` + 布尔 `result`）或带旧验证截图路径的历史任务详情
- **THEN** 验收段按旧字段如实呈现，旧验证截图路径仍按文本显示且图片存在时可点开原图，页面不报错、不出现空壳区块

#### Scenario: 只读

- **WHEN** 查看任意一条验收结果
- **THEN** 该段内没有任何按钮或输入控件，不提供修改或写回操作
