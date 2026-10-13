## REMOVED Requirements

### Requirement: 新契约在平台侧的下游同步

**Reason**: 该需求中的「执行模型调试对话 SHALL 与任务链路同契约」条款及其场景（调试对话同契约）随模型调试页与单角色调试对话整体退役而失效；其余条款行为不变，改以新需求名承载。
**Migration**: 任务过程记录落新三字段、验收输入带点击时刻与截图路径两项行为不变，见本 delta 新增的「执行模型输出契约在平台侧的下游同步」；单角色联调改用命令行 `model_test`。

## ADDED Requirements

### Requirement: 执行模型输出契约在平台侧的下游同步

任务过程记录里的执行结果 SHALL 以新三字段落库，MUST NOT 再写入 `action` 与 `message`。验收模型的输入 SHALL 由平台按新契约给出该步的 `result`、点击前时间戳与点击后截图路径（无点击 / 未截图时如实标注），MUST NOT 依赖模型自述说明；随输入附带的执行侧截图图片与既有取证口径 MUST NOT 因此改变。执行模型输出契约的兑现面只有任务链路——平台 MUST NOT 再提供单角色调试对话。

#### Scenario: 过程记录落新字段

- **WHEN** 查看新任务的某步过程记录
- **THEN** 该步 `executor` 段只含 `result` / `click_timer` / `screenshot`

#### Scenario: 验收输入带点击时刻与截图路径

- **WHEN** 某步执行完成并进入验收
- **THEN** 验收模型输入含该步 `result`、点击前时间戳与点击后截图路径，且不再含执行模型的说明文字

#### Scenario: 平台不再提供单角色调试对话

- **WHEN** 用户查看 AI 工具箱的工具来源与任务详情页
- **THEN** 两者都不提供针对单个角色发起调试对话的入口
