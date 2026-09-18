## MODIFIED Requirements

### Requirement: Shared doodle buttons use marker tones

系统 MUST 提供共享涂鸦按钮，外观 SHALL 对齐模版 `#comp-buttons`：墨色描边、近直角、硬偏移阴影。色调 MUST 为：危险操作用红底（删除）、校验与详情用青绿底、配置用黄底。MUST NOT 用冷蓝作为「蓝色」语义——本条禁令 SHALL 仅约束上述**操作按钮的语义色调**；切换/分段类控件的「未选中 / 选中」二态不属于语义色调，由 `frontend-doodle-button` 规定。

#### Scenario: Action color mapping on cards

- **WHEN** 用户在小助手卡或任务卡上看到操作按钮
- **THEN** 「删除」为红底，「校验」与「详情」为青绿底，「配置」为黄底
- **AND** 按钮 hover 呈现上移并加深硬阴影，disabled 时不可点且阴影变灰

#### Scenario: Cold blue ban is scoped to semantic tones

- **WHEN** 检索平台内以冷蓝 `var(--c-workflow)` 为底色的按键
- **THEN** 命中项均为切换/分段类控件的「未选中」默认态，不出现于内容卡操作按钮的语义色调中
