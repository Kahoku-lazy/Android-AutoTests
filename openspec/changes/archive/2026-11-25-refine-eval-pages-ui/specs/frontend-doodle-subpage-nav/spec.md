## ADDED Requirements

### Requirement: 评测页与题库页以面包屑条承载回退

评测页（`/ai-assistant/evals`）与题库页（`/ai-assistant/eval-cases`）MUST 在 `.doc-body` 顶部渲染面包屑条：祖先链靠左、返回芯片靠右，当前项不可点并带马克笔高亮。系统 MUST NOT 用与正文等宽的动作条充当回退。

#### Scenario: 评测页回退到平台助手

- **WHEN** 用户打开 `/ai-assistant/evals`
- **THEN** `.doc-body` 顶部可见「平台助手 / 评测」面包屑条
- **AND** 返回芯片位于该条右端，激活后进入 `/ai-assistant`
- **AND** 「评测」为当前项，不可点击

#### Scenario: 题库页回退到评测

- **WHEN** 用户打开 `/ai-assistant/eval-cases`
- **THEN** `.doc-body` 顶部可见「平台助手 / 评测 / 评测题库」面包屑条
- **AND** 返回芯片位于该条右端，激活后进入 `/ai-assistant/evals`
- **AND** 祖先两级可点击，当前项不可点击

#### Scenario: 页面动作按内容宽度呈现

- **WHEN** 用户打开评测页或题库页
- **THEN** 「编辑题库」「新建题目」「开始评分」等页面动作位于工具条内、宽度按内容
- **AND** 页面不出现与正文等宽的动作条
