## ADDED Requirements

### Requirement: 模型运行只记对话稿

本能力覆盖的智能体运行 SHALL 只把模型运行信息写入对话稿 JSONL。同一次运行 MUST NOT 再追加按天切分的管道过程日志（以「时间戳 | 角色 | 模型」起头的文本行）。运行结束 MUST NOT 生成 HTML 日志页。

#### Scenario: 跑完只有对话稿

- **WHEN** 一次运行正常结束
- **THEN** 本次运行的块都在 `logs/agent_logs/` 下该次文件里，同一次运行 MUST NOT 新写出管道过程日志文件

#### Scenario: 不生成 HTML

- **WHEN** 一次运行结束
- **THEN** 运行器 MUST NOT 写出 HTML 文件；已有的本地演示页不是这次运行的产物
