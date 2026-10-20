## MODIFIED Requirements

### Requirement: Shared note card matches deco-card DNA

系统 MUST 提供共享内容卡的 `note` 变体，其默认外观 SHALL 对齐模版 deco-card：虚线描边、近直角、纸色底、硬偏移色阴影、可选顶中半透明胶带与微倾；SHALL NOT 以实线细边 + 大圆角 + 模糊 elevation 作为该变体默认样式。

#### Scenario: Assistant route card uses note variant

- **WHEN** 小助手看板渲染线路卡
- **THEN** 卡片呈现虚线边、纸色底、彩色硬阴影与顶中胶带（若启用装饰）
- **AND** 仍展示功能标题与助手身份（连通状态已随校验功能下线）

### Requirement: Shared doodle buttons use marker tones

系统 MUST 提供共享涂鸦按钮，外观 SHALL 对齐模版 `#comp-buttons`：墨色描边、近直角、硬偏移阴影。色调 MUST 为：危险操作用红底（删除）、详情用青绿底、配置用黄底。MUST NOT 用冷蓝作为「蓝色」语义——本条禁令 SHALL 仅约束上述**操作按钮的语义色调**；切换/分段类控件的「未选中 / 选中」二态不属于语义色调，由 `frontend-doodle-button` 规定。

#### Scenario: Action color mapping on cards

- **WHEN** 用户在小助手卡或任务卡上看到操作按钮
- **THEN** 「删除」为红底，「详情」为青绿底，「配置」为黄底
- **AND** 按钮 hover 呈现上移并加深硬阴影，disabled 时不可点且阴影变灰

#### Scenario: Cold blue ban is scoped to semantic tones

- **WHEN** 检索平台内以冷蓝 `var(--c-workflow)` 为底色的按键
- **THEN** 命中项均为切换/分段类控件的「未选中」默认态，不出现于内容卡操作按钮的语义色调中
