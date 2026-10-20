## MODIFIED Requirements

### Requirement: 执行模型只输出 result / click_timer / screenshot

执行模型 SHALL 只输出恰好三个字段的 JSON：`result`、`click_timer`、`screenshot`。`result` MUST 为 `PASS`（操作成功）或 `FAIL`（操作失败或遇到问题）；`click_timer` MUST 为该步**点击前的时间戳**，取本步点击类工具结果里的动作发出时刻（北京时间、毫秒精度，原文照抄）；`screenshot` SHALL 为空字符串——截图工具只回图片数据、不返回路径，平台不采集该字段，模型 MUST NOT 编造路径。该输出 MUST NOT 含 `action` 与 `message` 两个键。本步没有产生点击时 `click_timer` SHALL 为空字符串。模型 MUST NOT 编造时间戳。

#### Scenario: 点一次开关后返回三字段

- **WHEN** 执行模型在某设备的详情页点击一次开关并在点击后截图
- **THEN** 其最终 JSON 恰好只有 `result` / `click_timer` / `screenshot` 三个键，`click_timer` 等于该次点击工具结果里的动作发出时刻，`screenshot` 为空字符串（截图工具不返回路径）

#### Scenario: 纯读取步骤不强凑时间戳

- **WHEN** 某步只调用读取类动作（如读取当前前台应用），未产生任何点击
- **THEN** `click_timer` 为空字符串，`result` 仍按实际结果给出

#### Scenario: 输出不含 action 与 message

- **WHEN** 检查任意一次执行结果
- **THEN** 该 JSON 不含 `action` 键、也不含 `message` 键

#### Scenario: 输出无效时如实判失败

- **WHEN** 模型未返回可解析的三字段 JSON
- **THEN** 该步执行结果按 `FAIL` 处理，且 `click_timer` 与 `screenshot` 均为空字符串，MUST NOT 由平台编造或从别处借用

### Requirement: 任务详情页按新契约呈现执行结果

任务详情页的执行结果段 SHALL 呈现该步的 `result` 与点击前时间戳。截图不落盘、平台不采集截图路径，因此该段 MUST NOT 呈现截图路径，也不得为缺失的路径渲染空壳区块。对存量旧记录里已有的截图路径 SHALL 仍按文本呈现，路径指向的图片存在时 MUST 可直接查看原图。该段 MUST 为只读展示。对存量旧记录（只有 `action` / `message`）SHALL 继续按旧字段如实呈现，MUST NOT 报错、MUST NOT 留空壳。

#### Scenario: 新记录呈三件

- **WHEN** 打开一个含新契约记录的任务详情并展开某步尝试
- **THEN** 执行结果段可见执行结果、点击前时间与「该步无截图路径」的如实标注三件内容，MUST NOT 出现可点击的截图路径，也 MUST NOT 用验收截图或其它截图顶替

#### Scenario: 未截图如实标注

- **WHEN** 某步执行结果里 `screenshot` 为空字符串
- **THEN** 页面如实标注该步无截图，MUST NOT 用验收截图或其它截图顶替

#### Scenario: 存量旧记录兼容

- **WHEN** 打开一个只有旧字段（`action` / `message`）或带旧截图路径的历史任务详情
- **THEN** 执行结果段按旧字段如实呈现，旧截图路径仍按文本显示且图片存在时可点开原图，页面不报错、不出现空壳区块

#### Scenario: 只读

- **WHEN** 查看任意一条执行结果
- **THEN** 该段内没有任何按钮或输入控件，不提供修改或写回操作

### Requirement: 执行模型输出契约在平台侧的下游同步

任务过程记录里的执行结果 SHALL 以新三字段落库，MUST NOT 再写入 `action` 与 `message`。验收模型的输入 SHALL 由平台按新契约给出该步的 `result`、点击前时间戳与执行侧截图**图片**（截图工具只回图片、不返回路径，故不给路径；无点击 / 未截图时如实标注），MUST NOT 依赖模型自述说明；随输入附带的执行侧截图图片与既有取证口径 MUST NOT 因此改变。执行模型输出契约的兑现面只有任务链路——平台 MUST NOT 再提供单角色调试对话。

#### Scenario: 过程记录落新字段

- **WHEN** 查看新任务的某步过程记录
- **THEN** 该步 `executor` 段只含 `result` / `click_timer` / `screenshot`

#### Scenario: 验收输入带点击时刻与截图路径

- **WHEN** 某步执行完成并进入验收
- **THEN** 验收模型输入含该步 `result`、点击前时间戳与执行侧截图图片；截图路径按不采集口径不存在，且输入不再含执行模型的说明文字

#### Scenario: 平台不再提供单角色调试对话

<!-- 场景名沿自变更前：AI 工具箱已下线，核对范围收窄为「平台入口与任务详情页」 -->

- **WHEN** 检查平台入口与任务详情页
- **THEN** 两者都不提供针对单个角色发起调试对话的入口
