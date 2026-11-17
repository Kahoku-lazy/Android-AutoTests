## ADDED Requirements

### Requirement: 任务清单每页固定 10 行且无行数选择器

任务清单每页 MUST 固定 **10** 行；取值 MUST 来自模块 `constants.ts`（选项集与默认值同源），页面 SHALL NOT 内联行数字面量。工具栏 MUST NOT 渲染「显示行数」标签或行数按钮组。分页文案与翻页键仍 MUST 保留「第 X / Y 页 · 共 N 条」与上一页 / 下一页。

#### Scenario: 每页 10 行

- **WHEN** 打开 `/tasks` 且任务多于 10 条
- **THEN** 表格每页呈现 10 行

#### Scenario: 无行数选择器

- **WHEN** 检查工具栏
- **THEN** 不存在「显示行数」标签与行数按钮
- **AND** 分页选项集仍由模块 `constants.ts` 提供
