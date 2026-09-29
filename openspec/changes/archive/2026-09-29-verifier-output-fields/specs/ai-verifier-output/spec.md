## Purpose

定义设备执行链路**验收模型**的输出契约：只回 `result`（PASS/FAIL）、`click_timer`（点击前时间戳）、`logAssertionTimer`（检测到日志关键词的时间戳，未检测到为空）、`screenshot`（验证截图路径）与 `actual`（截图里实际看到什么）五个字段，并规定各字段的取值来源、空值口径，以及工作流、任务过程记录、任务详情页与验收模型调试对话如何按新契约呈现。

## ADDED Requirements

### Requirement: 验收模型只输出六字段

验收模型 SHALL 只输出六个字段的 JSON：`result`、`click_timer`、`logAssertionTimer`、`logAssertionInfo`、`screenshot`、`actual`。`result` MUST 为 `PASS`（实际结果符合断言）或 `FAIL`（不符合或无法确认），MUST NOT 再使用布尔值。`click_timer` MUST 为**点击前的时间戳**，取平台下发给它的执行侧点击时刻（原文照抄）；本步没有点击时 SHALL 为空字符串。`logAssertionTimer` MUST 为**检测到日志关键词的时间戳**，取日志检查工具返回的命中时间戳（原文照抄，多次命中取最早一次）；未检测到或未检查时 SHALL 为空字符串。`logAssertionInfo` SHALL 为**本轮检查的日志关键词**，由平台按对检查工具的实际调用自动填写（模型自己写的值以工具调用为准）。`screenshot` MUST 为本次**验证截图的相对路径**，取本次截图工具返回的截图路径（原文照抄）。`actual` MUST 用一句话描述截图里实际看到了什么。该输出 MUST NOT 含 `action` 与 `assert` 两个键。任何取不到的坐标 MUST 留空字符串，模型 MUST NOT 编造时间戳或文件路径。

#### Scenario: 通过的一次验收回六字段

- **WHEN** 某步执行后在设备上截图、截图与断言相符，且检查工具在窗口内检测到该关键词
- **THEN** 该次验收 JSON 恰好只有六个键，`result` 为 `PASS`，`click_timer` 等于平台给出的本步点击前时间戳，`logAssertionTimer` 等于检测到的时间戳，`logAssertionInfo` 等于所检查的关键词，`screenshot` 等于本次截图返回的相对路径

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

### Requirement: 验收模型提示词声明六字段契约与两条件

平台 SHALL 在验收模型的系统提示词里声明该契约：列出六个字段及其取值来源（点击前时间戳取输入里执行侧给出的时刻、日志关键词时间戳取日志检查工具返回的命中时间戳、日志关键词由平台按工具调用自动填、验证截图路径取本次截图工具返回的路径），给出只含这六个键的示例 JSON，并把日志证据段里的通过/不通过措辞统一为 `PASS`/`FAIL`。提示词 MUST 写明判定口径：**日志检测到与截图确认两个条件都满足才可判 PASS；检查工具未检测到该关键词时必须判 FAIL**，并 MUST 指引模型先调用检查工具、再据其结论判定。存量库中的验收模型提示词 SHALL 由可逆迁移按锚点同步。

#### Scenario: 提示词含六字段说明与示例

- **WHEN** 读取验收模型的系统提示词
- **THEN** 其输出字段段列出六个字段及各自取值来源，示例 JSON 只含这六个键，且不再要求输出 `action` / `assert`

#### Scenario: 提示词写明两条件

- **WHEN** 读取验收模型的系统提示词
- **THEN** 其中含「日志检测到与截图确认两个条件都满足才可判 PASS、未检测到日志必须判 FAIL」的判定口径，并指明用检查工具的结论

#### Scenario: 措辞不再混用布尔

- **WHEN** 读取提示词里的日志证据段与验收判定段
- **THEN** 通过 / 不通过的表述为 `PASS` / `FAIL`，不再出现按 `true` / `false` 判定的要求

#### Scenario: 存量库同步且可回滚

- **WHEN** 对含旧契约（`action` / `assert` / `actual` / 布尔 `result`）提示词的库执行迁移
- **THEN** 提示词被替换为新契约正文；按迁移逆序回滚后恢复旧契约原文

#### Scenario: 用户已改写的提示词不被动

- **WHEN** 某行提示词已被用户改写、不含迁移锚点
- **THEN** 该行保持原样，迁移跳过它且不报错

### Requirement: 日志检查结论与关键词的平台填充

平台 SHALL 在验收输入里把「日志未检测到时必须判 FAIL」的口径与日志检查结论一并给出；并 SHALL 在验收完成后按本轮对检查工具的实际调用填充 `logAssertionInfo`（多个关键词按调用顺序去重后用「、」连接）：模型没写该字段时 MUST 填出、模型写错时以工具调用为准。`logAssertionTimer` 保持由模型照抄检查工具返回的命中时间戳；模型留空而工具确有命中时，平台 SHALL 用该命中时间戳补上（MUST NOT 覆盖模型已写的值，MUST NOT 编造）。平台 MUST NOT 因日志结论改写模型给出的 `result`（判定由模型按输入里写明的两条件作出）。

#### Scenario: 关键词自动填出

- **WHEN** 模型调用了检查工具并报出关键词，但自己的 JSON 里没写或写错了 `logAssertionInfo`
- **THEN** 该次验收记录里的 `logAssertionInfo` 等于工具调用里的关键词

#### Scenario: 多次检查按顺序去重

- **WHEN** 一轮验收里先后检查了两个不同关键词
- **THEN** `logAssertionInfo` 按调用顺序给出两个关键词（去重、以「、」连接）

#### Scenario: 时间戳仅在模型留空时补

- **WHEN** 检查工具检测到关键词，而模型把 `logAssertionTimer` 留空
- **THEN** 平台用工具返回的命中时间戳补上；模型已写值时 MUST NOT 覆盖

#### Scenario: 不改判

- **WHEN** 检查工具未检测到关键词，而模型仍回了 `PASS`
- **THEN** 平台 MUST NOT 把它改写成 `FAIL`，但输入里已写明该口径、记录里如实给出关键词与日志结论

#### Scenario: 过程记录落新六字段

- **WHEN** 查看新任务的某步过程记录
- **THEN** 该步 `verifier` 段含 `result` / `click_timer` / `logAssertionTimer` / `logAssertionInfo` / `screenshot` / `actual`

### Requirement: 工作流按新契约判定与回灌

工作流 SHALL 以验收结果的 `result` 等于 `PASS` 判定该步通过，MUST NOT 再依赖布尔真值。未通过时 SHALL 把该次验收的 `actual`（实际结果说明）回灌给执行模型作为重试修正提示，并在任务的失败步骤记录里给出该说明；`actual` 为空时 MUST 如实留空，MUST NOT 编造原因。任务过程记录里的验收段 SHALL 以新五字段落库。

#### Scenario: 判通过

- **WHEN** 某步验收返回 `result=PASS`
- **THEN** 该步勾选完成并进入下一步

#### Scenario: 未通过时带原因重试

- **WHEN** 某步验收返回 `result=FAIL` 且 `actual` 有说明
- **THEN** 执行模型收到的重试提示里包含该说明，且任务失败记录里该步的原因等于该说明

#### Scenario: 过程记录落新字段

- **WHEN** 查看新任务的某步过程记录
- **THEN** 该步 `verifier` 段只含 `result` / `click_timer` / `logAssertionTimer` / `screenshot` / `actual`

### Requirement: 任务详情页按新契约呈现验收

任务详情页的验收段 SHALL 呈现该步验收的 `result` 与 `actual`，并在 `logAssertionTimer` 非空时给出「日志断言时间」；验证截图 MUST 呈现模型回报的路径文本，且路径指向的图片存在时 MUST 可直接查看原图。该段 MUST 为只读展示。对存量旧记录（`action` / `assert` / `actual` + 布尔 `result`）SHALL 继续如实呈现，MUST NOT 报错、MUST NOT 留空壳。同一处点击的「点击前时间」已在执行结果段呈现，验收段 MUST NOT 重复堆一遍同名行。

#### Scenario: 新记录呈四件

- **WHEN** 打开含新契约记录的任务详情并展开某步尝试
- **THEN** 验收段可见验收结果、实际结果说明、日志断言时间与验证截图路径（截图可点开看原图）

#### Scenario: 未检测到日志时如实不显示该行

- **WHEN** 该次验收的 `logAssertionTimer` 为空字符串
- **THEN** 页面不出现「日志断言时间」行，MUST NOT 用其它时间戳顶替

#### Scenario: 存量旧记录兼容

- **WHEN** 打开只有旧字段（`action` / `assert` / `actual` + 布尔 `result`）的历史任务详情
- **THEN** 验收段按旧字段如实呈现，页面不报错、不出现空壳区块

#### Scenario: 只读

- **WHEN** 查看任意一条验收结果
- **THEN** 该段内没有任何按钮或输入控件，不提供修改或写回操作
