## MODIFIED Requirements

### Requirement: Every L2 page root provides the workbench theme scope

每一个 L2 页面根 SHALL 携带工作台主题作用域（`.wb-shell`），使页头按钮与页内 `AppCard`/`AppTable`/`FilterTabs` 呈现 Doodle Craft 主题；系统 MUST NOT 出现同一模块内列表页与详情页使用同一共享组件却外观不一致。

#### Scenario: Report list and report detail share one component appearance

- **WHEN** 用户先打开 `/reports`（列表页），再打开 `/tasks/{id}`（承接报告行点击的任务详情页）
- **AND** 已删除的 `/reports/{runId}` 场景不再参与本断言
- **THEN** 两个页面里的 `AppTable` / `AppCard` 呈现相同的 Doodle Craft 边框、底色与圆角，无 Element Plus 默认外观回退

#### Scenario: Theme scope present on all workbench page roots

- **WHEN** 逐一打开 `/reports`、`/tasks/{id}`、case-manager、device-pool 与 serial-log 的页面
- **THEN** 每个页面根都在带 `.wb-shell` 的祖先之内，页头按钮与页内卡片均为主题皮肤
