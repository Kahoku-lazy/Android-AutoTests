## MODIFIED Requirements

### Requirement: Reusable data blocks use AppCard inside the theme scope

图表卡 · 表格卡 · 指标卡 · 认证卡 · 条目卡等**可复用数据块** SHALL 使用 `AppCard`；使用它的页面 MUST 位于工作台主题作用域（`.wb-shell` 或 `.workflow-workbench`）之内，否则其外观退化为 Element Plus 默认。`AppCard` 默认外观 SHALL 为 Hand-Drawn Doodle 钉板壳（虚线描边、近直角、硬偏移色阴影、可选图钉），SHALL NOT 再以实线大圆角 + 彩色顶条为默认。

#### Scenario: Data blocks render the workbench skin

- **WHEN** 打开 `/reports`（图表卡 / 表格卡）、`/reports/{runId}`（表格卡）与 `/ai-assistant/knowledge`（状态卡 / 分组卡）
- **THEN** 这些块渲染 Doodle 钉板皮肤（`.ac-card` 虚线边与硬阴影），无 Element Plus 默认外观回退

#### Scenario: Auth card stays AppCard on the login view

- **WHEN** 打开 `/login`
- **THEN** 认证卡仍渲染 `.ac-card`（登录页无 `.wb-shell`，其皮肤由登录页自有样式提供，属已登记的独立视觉）

#### Scenario: Dashboard trend cards use AppCard

- **WHEN** 打开 `/dashboard` 的趋势数据区
- **THEN** 趋势块使用 `AppCard`，不出现裸 `el-card` 作为趋势外壳
