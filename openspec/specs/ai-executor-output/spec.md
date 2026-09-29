# ai-executor-output Specification

## Purpose
定义设备执行链路**执行模型**的输出契约：只回 `result` / `click_timer` / `screenshot` 三个字段，并规定这两个证据字段的取值来源、无点击/无截图时的如实口径，以及平台各消费方（任务过程记录、任务详情页、验收模型输入、执行模型调试对话）如何按新契约呈现。

## Requirements

### Requirement: 执行模型只输出 result / click_timer / screenshot

执行模型 SHALL 只输出恰好三个字段的 JSON：`result`、`click_timer`、`screenshot`。`result` MUST 为 `PASS`（操作成功）或 `FAIL`（操作失败或遇到问题）；`click_timer` MUST 为该步**点击前的时间戳**，取本步点击类工具结果里的动作发出时刻（北京时间、毫秒精度，原文照抄）；`screenshot` MUST 为该次点击**之后**截图的相对路径，取点击后截图工具返回的截图路径（原文照抄）。该输出 MUST NOT 含 `action` 与 `message` 两个键。本步没有产生点击时 `click_timer` SHALL 为空字符串；没有可用截图时 `screenshot` SHALL 为空字符串。模型 MUST NOT 编造时间戳或文件路径。

#### Scenario: 点一次开关后返回三字段

- **WHEN** 执行模型在某设备的详情页点击一次开关并在点击后截图
- **THEN** 其最终 JSON 恰好只有 `result` / `click_timer` / `screenshot` 三个键，`click_timer` 等于该次点击工具结果里的动作发出时刻，`screenshot` 等于点击后截图返回的相对路径

#### Scenario: 纯读取步骤不强凑时间戳

- **WHEN** 某步只调用读取类动作（如读取当前前台应用），未产生任何点击
- **THEN** `click_timer` 为空字符串，`result` 仍按实际结果给出

#### Scenario: 输出不含 action 与 message

- **WHEN** 检查任意一次执行结果
- **THEN** 该 JSON 不含 `action` 键、也不含 `message` 键

#### Scenario: 输出无效时如实判失败

- **WHEN** 模型未返回可解析的三字段 JSON
- **THEN** 该步执行结果按 `FAIL` 处理，且 `click_timer` 与 `screenshot` 均为空字符串，MUST NOT 由平台编造或从别处借用

### Requirement: 执行模型提示词声明三字段契约

平台 SHALL 在执行模型的系统提示词里声明该输出契约：列出三个字段及其取值来源（点击前时间戳取点击工具结果里的动作发出时刻；截图路径取操作后截图工具返回的截图路径），并给出只含这三个键的示例 JSON；操作后截图的口径 MUST 要求回传落盘路径。提示词 MUST NOT 再要求模型输出 `action` 或 `message`。存量库中的执行模型提示词 SHALL 由可逆迁移按锚点同步。

#### Scenario: 提示词含三字段说明与示例

- **WHEN** 读取执行模型的系统提示词
- **THEN** 其输出字段段列出 `result` / `click_timer` / `screenshot` 及各自取值来源，示例 JSON 只含这三个键

#### Scenario: 存量库同步且可回滚

- **WHEN** 对含旧契约（`action` / `result` / `message`）提示词的库执行迁移
- **THEN** 该提示词被替换为新契约正文；回滚该迁移后恢复旧契约原文

#### Scenario: 用户已改写的提示词不被动

- **WHEN** 某行提示词已被用户改写、不含迁移锚点
- **THEN** 该行保持原样，迁移跳过它且不报错

### Requirement: 新契约在平台侧的下游同步

任务过程记录里的执行结果 SHALL 以新三字段落库，MUST NOT 再写入 `action` 与 `message`。验收模型的输入 SHALL 由平台按新契约给出该步的 `result`、点击前时间戳与点击后截图路径（无点击 / 未截图时如实标注），MUST NOT 依赖模型自述说明；随输入附带的执行侧截图图片与既有取证口径 MUST NOT 因此改变。执行模型调试对话 SHALL 与任务链路同契约（同一份系统提示词、同一角色装配），因此其回复同样只含三字段。

#### Scenario: 过程记录落新字段

- **WHEN** 查看新任务的某步过程记录
- **THEN** 该步 `executor` 段只含 `result` / `click_timer` / `screenshot`

#### Scenario: 验收输入带点击时刻与截图路径

- **WHEN** 某步执行完成并进入验收
- **THEN** 验收模型输入含该步 `result`、点击前时间戳与点击后截图路径，且不再含执行模型的说明文字

#### Scenario: 调试对话同契约

- **WHEN** 超管在执行模型调试页选定设备并发一条会触发点击的内容
- **THEN** 该条助手消息里的模型回复为三字段 JSON，可直接读到执行结果、点击前时间戳与截图路径

### Requirement: 任务详情页按新契约呈现执行结果

任务详情页的执行结果段 SHALL 呈现该步的 `result`、点击前时间戳与点击后截图路径；截图路径 MUST 以可读文本呈现，路径指向的图片存在时 MUST 可直接查看原图。该段 MUST 为只读展示。对存量旧记录（只有 `action` / `message`）SHALL 继续按旧字段如实呈现，MUST NOT 报错、MUST NOT 留空壳。

#### Scenario: 新记录呈三件

- **WHEN** 打开一个含新契约记录的任务详情并展开某步尝试
- **THEN** 执行结果段可见执行结果、点击前时间与点击后截图路径，截图可点开看原图

#### Scenario: 未截图如实标注

- **WHEN** 某步执行结果里 `screenshot` 为空字符串
- **THEN** 页面如实标注该步无截图，MUST NOT 用验收截图或其它截图顶替

#### Scenario: 存量旧记录兼容

- **WHEN** 打开一个只有旧字段（`action` / `message`）的历史任务详情
- **THEN** 执行结果段按旧字段如实呈现，页面不报错、不出现空壳区块

#### Scenario: 只读

- **WHEN** 查看任意一条执行结果
- **THEN** 该段内没有任何按钮或输入控件，不提供修改或写回操作
