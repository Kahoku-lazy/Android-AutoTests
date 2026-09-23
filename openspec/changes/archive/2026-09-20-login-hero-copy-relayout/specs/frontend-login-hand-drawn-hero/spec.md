## MODIFIED Requirements

### Requirement: Hero is a two-column hand-drawn composition
登录页 Hero SHALL 呈现左右分栏：左侧为品牌文案区与模式 CTA；右侧为 Meeting doodle 钉板容器。左侧文案 SHALL 为四行：标题「AI 自动化测试平台」，以及三行副文案「实现让AI来做测试」「让测试工作摆脱重复的劳动」「专注于创造价值」；字体 MUST 沿用当前登录页品牌字体（`--app-font-brand`）。标题字号 MUST 取字号刻度的 48px 档，三行副文案字号 MUST 取 32px 档，两者 MUST 以 `var()` 引用刻度，SHALL NOT 直写 `font-size` 字面量。四行文案与模式 CTA MUST 在左侧文案块内居中排列。左栏 SHALL 显示当前版本徽标 `v3.0`，且左栏 SHALL NOT 再出现独立成行的眉标文案「AI 自动化测试」。系统 MUST NOT 在 Hero 中渲染动物贴纸板。

#### Scenario: Left column shows brand copy and mode CTAs
- **WHEN** 用户打开 `/login` 且不处于账号切换提示态
- **THEN** 左侧自上而下可见标题「AI 自动化测试平台」与三行副文案「实现让AI来做测试」「让测试工作摆脱重复的劳动」「专注于创造价值」
- **AND** 标题字号取 48px 档、三行副文案字号取 32px 档，四行文案在左侧文案块内居中
- **AND** 可见主按钮「登录」与次按钮「注册」，二者同一行且在该文案块内居中

#### Scenario: Version badge shows v3.0
- **WHEN** 用户打开 `/login`
- **THEN** 左栏版本徽标文本为「v3.0」

#### Scenario: Eyebrow copy is removed
- **WHEN** 用户打开 `/login`
- **THEN** 左侧文案块内不存在独立成行的眉标文案「AI 自动化测试」

#### Scenario: Animal sticker board is removed
- **WHEN** 用户打开 `/login`
- **THEN** 页面中不出现动物贴纸板（无「AI助手 / 设备管理 / 用例编排 / 用例执行 / 报告生成」贴纸组合）
