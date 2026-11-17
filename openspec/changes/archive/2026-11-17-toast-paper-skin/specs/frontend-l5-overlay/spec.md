## MODIFIED Requirements

### Requirement: Blocking overlay skins are symmetric

`el-dialog`、`el-drawer` 与 `ElMessage` 的全局皮肤 MUST 统一由 `style.css` 提供，使对话框、抽屉与提示条使用同一套纸面语言；模块 SHALL NOT 为抽屉、对话框或提示条各补私有皮肤。

`ElMessage` MUST 呈现为「纸片」：底色取 `--paper`、描边 `2.5px solid var(--ink)`、圆角取 `--app-radius-sm`、硬偏移影 `3px 3px 0 0 var(--ink)`（模糊半径必须为 0，MUST NOT 使用柔影）、内边距取 `--app-space-sm` / `--app-space-md`、字体取 `--app-font`、正文 `--app-size-sm` 且字重不小于 600。状态图标 MUST 跟随语义色：success → `--app-status-success`、error → `--color-red-46`、warning → `--c-ops`，MUST NOT 使用 Element Plus 出厂调色。

提示里的可点入口 MUST 用独立按钮承载并使用 `.el-message__action`（按钮语义 + 链接外观：墨字、`underline wavy var(--c-task)`、`--app-font-weight-heavy`、focus 时 `2px` 柠黄 outline）；MUST NOT 把整条提示包成一个按钮，因为那会让只读文案与可点入口在视觉上无法区分。

#### Scenario: Drawer shares the dialog paper language

- **WHEN** 在任一页面打开 `el-drawer`（如报告或页脚抽屉）
- **THEN** 抽屉的外观与 `el-dialog` 同源：近直角圆角与墨色描边来自 `style.css` 的全局皮肤
- **AND** 该模块的 `<style scoped>` 中没有为抽屉私写的边框 / 圆角 / 背景覆写

#### Scenario: Global skin is the single place for overlay chrome

- **WHEN** 检索全仓的 `.el-dialog` / `.el-drawer` 皮肤声明
- **THEN** 两者都命中 `frontend/src/style.css`
- **AND** 没有第二个文件重复声明抽屉或对话框的边框 / 圆角

#### Scenario: Toast renders as a paper slip

- **WHEN** 任一页面弹出 `ElMessage`
- **THEN** 其计算背景为纸面色、描边 2.5px 墨色、圆角 `4px 8px`
- **AND** `box-shadow` 为 `3px 3px 0 0` 墨色且模糊半径为 0
- **AND** 字体为全站等宽字体栈，正文 14px

#### Scenario: Action entry is a link, not the whole toast

- **WHEN** 平台助手提交任务成功并弹出「已提交，任务 N。去任务清单」
- **THEN** 只有「去任务清单」是一个按钮，带波浪下划线与 focus outline
- **AND** 「已提交，任务 N。」是纯文本，点击它不触发跳转
