## Why

用例管理「新建项目」弹窗是进入用例模块的唯一入口，但它的动作键与「库类型」分段控件仍停在 Element Plus 出厂几何上：

- 「取消」只有 `1px` 描边、无位移影；「创建」的影是 6% 柔影（`2px 2px 0 rgba(0, 0, 0, 0.06)`）、字重 700 —— 与纸面主题「墨色粗边 + 零模糊硬影 + 800 字重」不是一套语言。
- 「库类型」分段控件靠 EP 的 `outline` 贴合画成一整条胶囊：边框 `1px`、字重 500、两段之间无间隙；选中态虽已取柠黄，但整体读起来仍是 EP 出厂控件。

需求方给出的对照图里这两组键都是通用控件外观，判定为「不符合主题」。

## What Changes

- 弹窗 `#footer`（取消 / 创建）改用共享 `DoodleBtn`：`paper` + `yellow`（墨边 + `2px` 近直角 + `3px 3px 0 0` 硬影 + 800 字重 + hover 上移）；`creating` 期间按钮 disabled 并显示「创建中…」（原为 EP 的 loading 转圈，提交语义与时序不变）。
- 「库类型」分段控件改为主题口径：真实 `2px solid var(--ink)` 墨边（同时撤掉 EP 冒充边框的 `outline`）、段间 `4px` 间隙、`14px / 700`；未选中取次级墨色、hover 提为正文墨色、选中柠黄底墨字且无影，与 `AppTabs` 同口径。键盘焦点补 `2px` 柠黄环 —— EP 的焦点样式挂在被撤掉的 outline 上，不补会丢焦点可见性。
- 多行输入框（`el-textarea__inner`）并入单行框那组墨边声明：此前它只有 EP 的 `1px` 内阴影描边，与上方 `2px` 单行框并排时粗细不一致。

## Capabilities

### New Capabilities

无（纯外观对齐；字段、校验、接口、提交时序均不变）。

### Modified Capabilities

无（`frontend-l0-design-tokens` 的分段控件场景本已要求「圆角取 `--app-radius-*`、选中态可读、与 `AppTabs` 同口径」，本次是把实现补齐，不放宽任何约束）。

## Impact

- 前端代码：`frontend/src/modules/case-manager/ProjectList.vue`（footer 换 `DoodleBtn`）、`frontend/src/style.css`（分段控件、输入件墨边两组声明）。
- 主题文档：`.agents/skills/doodle-craft/references/components/form-controls.md`（§1 textarea 由「未覆盖」改为实规格、§4 分段控件补实测坑）、`references/components/general.md`（`DoodleBtn` 用途补「浮层动作区」）。
- 后端 / 接口 / 数据：无。
- 影响面：分段控件与多行框属于全局 EP 皮肤，但当前唯一的分段控件消费者就是该弹窗；多行框外观全站统一变粗（`.sketch-kit` 内的虚线框由 kit 的更高特异性接管，不受影响）。
