## ADDED Requirements

### Requirement: Overlay visibility binding follows state ownership

覆盖层的可见性绑定 MUST 按**状态归属**确定，同一情形 MUST 只用一种写法：状态由本组件持有的 `ref`，或由本模块 store 持有且关闭时只需写回时，MUST 使用 `v-model`（含 `v-model="store.x"`）；可见性由条件表达式派生、或关闭时需联动清理 / 通知父组件时，MUST 使用 `:model-value` + `@update:model-value`（或 `@close`）显式处理；跨页复用的薄封装 MUST NOT 自持可见性，只接收 `visible` prop 并 emit 领域事件（`cancel` / `confirm` / `close`）。

#### Scenario: Store-owned overlay uses v-model

- **WHEN** 弹层的可见性由本模块 store 的布尔字段持有，且关闭时无需额外清理
- **THEN** 模板使用 `v-model="store.<字段>"` 绑定
- **AND** 不出现 `:model-value="store.<字段>"` + `@update:model-value="(v) => (store.<字段> = v)"` 的纯写回展开

#### Scenario: Derived visibility keeps an explicit binding

- **WHEN** 弹层的可见性由条件表达式派生（如 `creatingKind === 'folder'`），或关闭时必须联动清理选中态 / 取消提交
- **THEN** 模板使用 `:model-value` + `@update:model-value` 显式处理关闭
- **AND** 该写法 MUST NOT 被改成 `v-model`

#### Scenario: Reusable overlay wrapper emits domain events

- **WHEN** 弹层被封装为可跨页复用的组件
- **THEN** 组件只接收 `visible` prop 并在关闭 / 取消 / 确认时 emit 领域事件（`cancel` / `confirm` / `close`）
- **AND** 组件自身不持有可见性状态，也不负责把 `false` 写回父级

### Requirement: Blocking overlay skins are symmetric

`el-dialog`、`el-drawer` 与 `ElMessage` 的全局皮肤 MUST 统一由 `style.css` 提供，使对话框与抽屉使用同一套纸面语言（近直角圆角、墨色描边）；模块 SHALL NOT 为抽屉或对话框各补私有皮肤。

#### Scenario: Drawer shares the dialog paper language

- **WHEN** 在任一页面打开 `el-drawer`（如检查器快照抽屉）
- **THEN** 抽屉的外观与 `el-dialog` 同源：近直角圆角与墨色描边来自 `style.css` 的全局皮肤
- **AND** 该模块的 `<style scoped>` 中没有为抽屉私写的边框 / 圆角 / 背景覆写

#### Scenario: Global skin is the single place for overlay chrome

- **WHEN** 检索全仓的 `.el-dialog` / `.el-drawer` 皮肤声明
- **THEN** 两者都命中 `frontend/src/style.css`
- **AND** 没有第二个文件重复声明抽屉或对话框的边框 / 圆角
