## MODIFIED Requirements

### Requirement: 设备动作记录并回传发出时间

系统 SHALL 在每个产生设备副作用的动作工具执行时记录该动作的**发出时刻**，取值 MUST 为北京时间（UTC+8）且精确到毫秒；该时刻 MUST 随该工具结果一并返回，使编排层能把它与该步截图一起交给验收模型。读取类动作 MUST NOT 被记为动作发出时刻。

点击类动作（按归一化坐标点击、按像素坐标点击或长按）MUST 携带坐标核对帧标识 `token`，该 `token` MUST 来自本步一次已完成的坐标核对（视觉路径的 `mark_dot` 或 xpath 路径的 `xpath_action` 标记）。`token` 有效时，该次动作 MUST 用该帧的标记点定位，MUST NOT 为定位重新截取设备屏幕；`token` 缺失、过期或不属于该设备时 MUST 返回可读 error 且 MUST NOT 产生任何手势，MUST NOT 悄悄退回新截图或新估算。点击类动作 MUST 同时返回点击后的页面图（base64 + media_type），使执行模型无需再单独截屏核对；调用方显式要求不出图时 MUST NOT 返回该图。回图 MUST NOT 改变发出时刻的取值与语义。

#### Scenario: 点击类动作返回发出时间

- **WHEN** 智能体带有效帧标识执行一次点击类动作
- **THEN** 该工具结果中包含本次动作的发出时刻，且为北京时间毫秒精度

#### Scenario: 未确认锚点的点击被拒绝

- **WHEN** 智能体调用点击类动作但没带 `token`
- **THEN** 返回可读 error 并提示先做坐标核对，设备上 MUST NOT 发生任何手势

#### Scenario: 帧标识失效时动作失败

- **WHEN** 点击类动作带上的 `token` 已过期或不属于该设备
- **THEN** 返回可读 error，设备上 MUST NOT 发生点击，MUST NOT 改用新截图定位

#### Scenario: 点击返回点击后的页面图

- **WHEN** 智能体带有效帧标识点击成功
- **THEN** 该工具结果同时含 `action_time`、实际像素坐标与一张点击后的页面图

#### Scenario: 有效帧标识的点击不重新截屏

- **WHEN** 点击类动作带上核对刚签发的有效 `token`
- **THEN** 该次动作按该帧的标记点执行，且设备侧只发生一次手势，不额外截屏

#### Scenario: 读取类动作不产生发出时间

- **WHEN** 智能体调用只读动作（如读取当前前台应用）
- **THEN** 该调用不产生设备副作用，且不被记录为动作发出时刻

## ADDED Requirements

### Requirement: xpath 命中点可标记、可按序号点击

`xpath_action` SHALL 支持标记命中点：给出 `confirm`（默认开启）时，工具 MUST 截取当前屏幕，把**全部命中点画在同一张图上**，每个点带可读序号（从 1 开始，先按纵坐标升序、同纵坐标再按横坐标升序），并返回 `items[]`（序号、节点文本、像素 `x` / `y`）与该帧 `token`。图上序号 MUST 与 `items[]` 一一对应。命中 0 个时 MUST NOT 出图、MUST NOT 截屏。

点击类动作 SHALL 接受 `index`：给出时 MUST 点击该帧序号等于 `index` 的点；越界或该帧无此序号时 MUST 返回可读 error 且 MUST NOT 产生手势。

#### Scenario: 单命中直接给出标记图与帧标识

- **WHEN** 某次 xpath 候选只命中 1 个节点
- **THEN** 返回体含标记图、`token`、该节点的文本与像素坐标，图上该点带序号 1

#### Scenario: 多命中全部标在同一张图上

- **WHEN** 查询 `//*[@text='定时']` 命中 2 个节点，坐标分别为 (142, 774) 与 (230, 1684)
- **THEN** 返回一张同时带序号 1、2 两个标记的图，`items` 按纵坐标升序给出这两组序号与坐标

#### Scenario: 按序号点击命中的那一个

- **WHEN** 执行模型带 `token` 与 `index=2` 调用点击类动作
- **THEN** 点击落在该帧序号 2 的像素坐标上，并回传实际点击坐标

#### Scenario: 序号越界被拒绝

- **WHEN** 该帧只有 2 个标记点，点击时传 `index=5`
- **THEN** 返回可读 error，设备上 MUST NOT 发生手势

#### Scenario: 没命中就不出图

- **WHEN** 所有候选都未命中任何节点
- **THEN** 返回 `count=0`、不含标记图，MUST NOT 为本次查询截屏

## ADDED Requirements

### Requirement: xpath 文本匹配容忍写法差异

`xpath_action` 的文本匹配 MUST 先按原文精确匹配；未命中时 MUST 去掉空白、全角转半角、忽略大小写再匹配一次。工具 MUST 接受最多 3 个候选表达式，并在**一次 UI 树读取**内全部试完，MUST NOT 为每个候选各读一次 UI 树；结果 MUST 分别给出每个候选的命中数。

#### Scenario: 归一化匹配命中带空格的文案

- **WHEN** 页面上节点文本为 `睡 眠`，候选写的是 `睡眠`
- **THEN** 归一化匹配命中该节点，返回它的文本与像素坐标

#### Scenario: 多候选只读一次 UI 树

- **WHEN** 一次给出 3 个候选表达式
- **THEN** 工具只读一次 UI 树就把全部候选试完，并在结果里分别给出每个候选的命中数
