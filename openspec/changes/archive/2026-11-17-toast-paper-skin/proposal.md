# 提示条改成纸片样式（与主题同一套语言）

## Why

「已提交，任务 234。去任务清单」这条提示现在是一块**白底 + 0.06 透明度柔影**的方框，浮在暖白纸面上既没有层次感，也和卡片（墨边 + 硬偏移影 + 近直角）不是一套语言；更糟的是整条提示被包成一个原生 `<button>`，连「已提交，任务 234。」这种只读文字看起来也可点，读者分不出「读」和「点」。

## What Changes

- `ElMessage` 全局皮肤（`style.css`）改成**纸片**：底 `--paper`、框 `2.5px solid var(--ink)`、影 `3px 3px 0 0 var(--ink)`、内距 `--app-space-sm --app-space-md`、等宽字体 `--app-font`、正文 `--app-size-sm` / 600。
- 图标跟状态色走：success → `--app-status-success`、error → `--color-red-46`、warning → `--c-ops`；关闭键取次要色，hover 回墨色。
- 新增 `.el-message__action`：提示里的行动入口用**按钮语义 + 链接外观**（墨字 + `underline wavy var(--c-task)` + focus outline）。
- 平台助手的提交成功提示改为「正文 `已提交，任务 N。` + 行动入口 `去任务清单`」两段；`sopSubmittedMessage()` 从返回整句改成返回 `{ text, action }`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-l5-overlay`：修改「Blocking overlay skins are symmetric」——把 `ElMessage` 从「同一套纸面语言」细化为具体纸片口径（硬影、纸底、状态色图标、行动入口类），并禁止把整条提示做成按钮。

## Impact

- 前端全局：`src/style.css`（`.el-message` 皮肤重写 + `.el-message__action`）。
- 前端 `ai-assistant`：`components/SopWorkflowSection.vue`（提示内容改两段）、`helpers/sop-form.ts`（返回值改 `{ text, action }`）、`tests/ai-assistant/p0/sop-submit-link.spec.ts`（断言随之更新）。
- 样式登记：`.agents/skills/doodle-craft/references/components/feedback.md` §4 更新 el-message 口径与反模式。
- 不动接口、不动其它模块的提示调用（它们自动继承新皮肤）。
