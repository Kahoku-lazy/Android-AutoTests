## Purpose

让助手测试对话的每一轮留下可回看的运行日志，并只允许从对应对话栏打开该栏自己的 HTML 报告。

## ADDED Requirements

### Requirement: 每一轮写出 JSONL 与 HTML

助手对话的每一轮 MUST 通过事件流记录思考、工具调用、工具结果与最终文本。记录 MUST 落在 `logs/agents/assistants/<助手编号>/<对话栏>/<时间戳>/` 下，并同时写出一份 JSONL 与一份 HTML。JSONL MUST 是一行一个 JSON 对象。截图的 base64 MUST NOT 写入 JSONL。页面 MUST NOT 接受调用方指定的其它根目录。

#### Scenario: 发送后产生一对日志

- **WHEN** 用户在某对话栏发送一句并等待该轮结束
- **THEN** 该栏目录下出现一个时间戳子目录
- **AND** 其中有一份 `.jsonl` 与一份 `.html`
- **AND** JSONL 中能找到该轮的工具调用或最终文本

#### Scenario: 取消后仍保留已写出的日志

- **WHEN** 用户在该轮进行中点击取消
- **THEN** 已写出的日志文件仍可在该栏日志列表中看到
- **AND** 该轮状态为用户取消

### Requirement: 对话栏只打开本栏的 HTML 报告

对话栏 MUST 提供日志入口，列出该栏各轮的时间与一句话结果。点开一轮 MUST 在浏览器打开该轮 HTML，MUST NOT 把磁盘绝对路径返回前端。进行中的一轮 MUST 显示仍在写入，MUST NOT 提供可打开的半份报告。读取 MUST 要求登录。请求路径越出该助手、该对话栏目录时 MUST 拒绝。

#### Scenario: 从对话栏打开完成的一轮

- **WHEN** 已登录用户打开某栏日志并选择一轮已完成的记录
- **THEN** 浏览器显示该轮 HTML 报告
- **AND** 响应中没有磁盘绝对路径

#### Scenario: 越权路径被拒绝

- **WHEN** 客户端请求的报告编号不属于该对话栏，或试图跳出该栏目录
- **THEN** 请求被拒绝
- **AND** 不返回其它栏或其它目录的文件
