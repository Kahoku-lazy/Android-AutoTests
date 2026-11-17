# 设计：纸片提示条

## Context

`style.css` 里 `.el-message` 的现状：

```css
background: var(--app-bg-card) !important;   /* 与纸面几乎同色 */
border: 2.5px solid var(--ink) !important;
border-radius: var(--app-radius-sm) !important;
box-shadow: 2px 3px 0 rgba(0, 0, 0, 0.06) !important;  /* 柔影，几乎看不见 */
```

平台助手的提示把整句文案（含「去任务清单」）塞进一个 `h("button", …)`，因此整条提示都是按钮外观（浏览器默认按钮样式 + EP 的 content 字体）。

## Goals / Non-Goals

**Goals**：提示条与卡片同一套纸面语言（墨边 + 硬偏移影 + 近直角）；只读文案与可点入口在视觉上一眼可分；全站提示自动继承，不需要逐处改。

**Non-Goals**：不改提示的位置、时长与出现时机；不新造提示组件；不动 `ElMessageBox`（那是阻塞型确认框，已另有皮肤）。

## Decisions

### D1 影从柔影换成硬影

`3px 3px 0 0 var(--ink)` —— 与侧栏「退出」键、运营表格的操作胶囊同一档。柔影（模糊半径 > 0）在纸面语言里等于没影；doodle-craft 的硬规则也是「阴影模糊半径恒为 0」。

### D2 底回到纸面，等宽字体

底 `--paper`：提示浮在内容之上，用纸面色而不是卡白色，才像"一张纸条压在上面"。字体取 `--app-font`（Cascadia Mono + 思源黑体），与全站一致；旧版走 EP 的 sans 栈，和页面字体不一致。

### D3 行动入口单独一类，不把整条提示做成按钮

```html
<span>已提交，任务 234。</span>
<button class="el-message__action">去任务清单</button>
```

`.el-message__action`：`border: 0; background: none; font: inherit;` + 墨字 + `text-decoration: underline wavy var(--c-task)` + `--app-font-weight-heavy` + focus 柠黄 outline。波浪下划线是仓库既有的链接语言（BUG 表的任务链、用例空态链接），取 `--c-task` 是因为它指向任务清单。

### D4 图标与关闭键跟状态/次要色走

EP 出厂绿（#67c23a）与主题色板不同源；success / error / warning 分别映射到 `--app-status-success` / `--color-red-46` / `--c-ops`。关闭键默认 `--app-text-secondary`，hover 回墨色。

### D5 helper 返回值改成 `{ text, action }`

`sopSubmittedMessage()` 原来把两段拼成一句交给调用方，调用方只能整句当按钮。改成结构化返回后，"哪段是文案、哪段是动作"由 helper 定义，组件只负责渲染——单测也从"包含子串"改成断言两段各自的内容。

## Risks / Trade-offs

- [全站提示统一变"重"]：墨边 + 硬影比旧的白板更抢眼；但提示是瞬时浮层（默认 3s），抢眼是它的职责。
- [硬影在屏幕顶部贴边时可能被裁]：提示默认 `top: 20px`，3px 影不会出界。

## Migration Plan

纯样式 + 一处提示文案结构 + 一个 helper 返回值。回退 = `style.css` 的 `.el-message` 块、`SopWorkflowSection.onSubmitted`、`sopSubmittedMessage` 三处还原。

## Open Questions

无。
