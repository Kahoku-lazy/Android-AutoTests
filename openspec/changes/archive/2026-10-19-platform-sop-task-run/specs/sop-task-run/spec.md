## Purpose

控制设备任务只启动和关闭已登记的 SOP 智能体。后端把检查通过的 YAML 文件与解析后的文档正文交给智能体；工具以引擎代码为准，后端不改工具清单。智能体在跑步骤前报告配置是否加载成功。

## ADDED Requirements

### Requirement: 控制设备任务只启动已登记的 SOP
系统 SHALL 只允许控制设备任务启动已登记的智能体。当前登记表 MUST 只包含 `sop`。新建任务所选的平台小助手决定执行与验收模型，流程仍是 `sop`。任务 MUST NOT 再调用规划模型生成步骤。YAML 中出现未登记的智能体名称 MUST 使该任务加载失败，并且 MUST NOT 装配流程。

#### Scenario: 指定 sop 时可以启动
- **WHEN** 一份通过格式检查的 YAML 未写 `agent` 或声明为 `sop`，新建任务选中了平台小助手上展示的助手，且该设备没有其它运行中的任务
- **THEN** 系统启动 `sop`，步骤来自该 YAML，模型来自所选助手，而不是规划模型的产出

#### Scenario: 未登记的智能体不能启动
- **WHEN** YAML 声明的智能体不是 `sop`
- **THEN** 任务显示「加载失败」，并且不产生可运行流程

### Requirement: 工具由引擎代码决定
启动 SOP 时系统 MUST 使用该智能体在引擎代码中声明的工具集。任务请求 MUST NOT 携带工具清单。后端 MUST NOT 在启动时增加、删除或替换这些工具。装配台上的工具开关 MUST NOT 改变这次 SOP 实际使用的工具。

#### Scenario: 启动时使用代码中的工具
- **WHEN** 一条声明为 `sop` 的任务开始执行
- **THEN** 执行与验收使用引擎代码里为 `sop` 声明的工具，任务请求中没有工具清单

#### Scenario: 装配台开关不改变本次工具
- **WHEN** 装配台关闭了某个工具的「交给助手」，随后启动一条 `sop` 任务
- **THEN** 该任务仍使用引擎代码中声明的全部工具

### Requirement: YAML 必须通过格式检查
系统 SHALL 在创建任务前检查 YAML。根节点 MUST 是非空的用例列表，或单条用例映射。每条用例 MUST 含非空的 `title` 与 `steps`。`agent` 可以不写；未写时系统 MUST 按 `sop` 接受该用例。若写了 `agent`，同一文件内 MUST 全部相同且等于 `sop`。每一步 MUST 含非空的 `action` 与 `assert`。一次任务 MUST 只有一份 YAML。检查不通过时系统 MUST 拒绝创建任务并返回可读原因。csv 与 json MUST 被拒绝。

#### Scenario: 合法 YAML 可以创建任务
- **WHEN** 用户提交一份含两条用例的 YAML，两条都没有 `agent`，且每步都有非空 `action` 与 `assert`
- **THEN** 系统创建任务，并保留该 YAML 正文

#### Scenario: 缺少步骤字段或智能体不一致时拒绝创建
- **WHEN** 某步缺少 `action` 或 `assert`，或文件里出现不是 `sop` 的 `agent`，或文件里出现两个不同的 `agent`
- **THEN** 系统拒绝创建任务，并说明格式不符合

#### Scenario: 一次任务上传两份 YAML
- **WHEN** 用户在同一次提交中附上两份 YAML
- **THEN** 系统拒绝创建任务，并说明只能有一份配置

### Requirement: 执行前再次检查配置并显示结论
智能体在跑任何步骤之前 MUST 再读一遍平台传入的 YAML 文件。符合上述格式且智能体为 `sop` 时，任务 MUST 显示「配置加载成功」并开始步骤。不符合时任务 MUST 显示「加载失败」，状态进入失败，并且 MUST NOT 开始第一步。该结论 MUST 出现在任务详情中。

#### Scenario: 文件在启动时仍然合法
- **WHEN** 任务开始执行，且传入的 YAML 文件仍符合格式，并且未写 `agent` 或指定 `sop`
- **THEN** 任务详情显示「配置加载成功」，随后按文件顺序执行用例

#### Scenario: 文件在启动时已不可读
- **WHEN** 任务开始执行，但 YAML 文件缺失或内容不再符合格式
- **THEN** 任务详情显示「加载失败」，任务状态为失败，设备上的后续排队任务可以被拉起

### Requirement: 同一 YAML 的多条用例按文件顺序跑完
一次任务 MUST 按 YAML 中的用例顺序依次执行。后一条用例 MUST NOT 复用前一条的角色对话。任务标题与任务目标 MUST NOT 用来挑选某条用例。某条用例失败时，系统 MUST NOT 开始排在它后面的用例。

#### Scenario: 两条用例依次执行
- **WHEN** YAML 中用例标题依次为「甲」和「乙」，且「甲」完成
- **THEN** 系统先跑完「甲」，再跑「乙」

#### Scenario: 前一条失败则停止后续用例
- **WHEN** 「甲」未完成
- **THEN** 「乙」不会开始，任务状态为失败

### Requirement: 开场说明由任务目标与设备组成
系统 SHALL 把任务目标与设备序列号组成开场说明，只交给第一步。开场说明 MUST NOT 从 YAML 读取。文档附件的 Markdown 正文 MUST 附在开场说明之后，按上传顺序拼接。没有文档附件时，开场说明 MUST 只含目标与设备序列号。

#### Scenario: 目标与设备进入第一步
- **WHEN** 任务目标为「核对开关」，设备序列号为 `R5CT62RH88F`，且没有文档附件
- **THEN** 第一步收到的开场说明同时含有该目标与该序列号

#### Scenario: 多份文档按上传顺序拼接
- **WHEN** 任务附有两份已解析的文档，上传顺序为先「甲.md」后「乙.pdf」
- **THEN** 开场说明在目标与设备之后，先是「甲.md」的 Markdown，再是「乙.pdf」的 Markdown

### Requirement: 用户可以关闭运行中的 SOP
系统 SHALL 允许用户关闭一条运行中的控制设备任务。关闭后该任务 MUST 停止后续步骤，状态变为 cancelled，详情保留已产生的步骤记录与配置加载结论。pending 任务 MUST NOT 提供关闭。

#### Scenario: 关闭运行中的任务
- **WHEN** 用户关闭一条状态为 running 的任务
- **THEN** 该任务不再执行后续步骤，状态变为 cancelled

#### Scenario: 排队中的任务不能关闭
- **WHEN** 用户对一条 pending 任务请求关闭
- **THEN** 系统拒绝该操作，任务仍为 pending
