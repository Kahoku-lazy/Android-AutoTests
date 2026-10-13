## ADDED Requirements

### Requirement: Recent steps keep screenshots

工作流在新的一次执行开始前，MUST 裁剪执行角色与验收角色已经积累的对话上下文。含即将开始的这一步，只保留最近 3 步的截图。更早的步骤 MUST 收成不含截图的文字结论。同一步的重试 MUST 仍算同一步，该步已有截图 MUST 保留。挂起后的恢复，以及同一次尝试里交给验收角色的半程，MUST NOT 裁剪。

#### Scenario: A new step drops screenshots older than the window

- **WHEN** 上下文里已有四步完成记录，并且下一步是一个新的步骤
- **THEN** 更早的两步只留下文字结论且不含截图，最近两步的截图仍在；当前步开始后，含当前步共保留 3 步截图

#### Scenario: A retry stays inside the same step

- **WHEN** 当前步已经有一次未通过的尝试，并且即将重试同一步
- **THEN** 这次重试与上一次尝试算同一步，该步截图继续保留，不因重试被收成文字结论
