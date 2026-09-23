## 1. 清空键加入硬边皮肤

- [x] 1.1 `SnapshotListDrawer.vue`：清空 `el-button` 去掉 `text` 模式（保留 `size="small"`、`type="danger"`、`:disabled`、`data-testid` 与确认流程），使其命中页面作用域既有的硬边皮肤选择器。验证：真浏览器实测 `border-radius` 为 `2px`、`border` 为 `2px solid rgb(30,30,36)`、`box-shadow` 为 `rgb(30,30,36) 2px 2px 0 0`（与侧栏「退出」逐项同值）
- [x] 1.2 `index.vue` 页面作用域：危险键底色取深危险红 `--el-color-danger`（T0 原子 `--color-red-46`）+ 文字 `--color-white`（含 hover），不可用态回落灰键（`--color-ink-79` + 墨字 + 撤位移阴影 + `opacity:1`）；只加声明，不改既有工具条规则。验证：`npm run lint:styles` 退出码 0 且**消费位置裸色字面量仍为 32 处**（改动中一度因注释里写了十六进制值升到 33，已把该字面量从注释移除回到基线）；实测启用态对比度 `5.97:1`、不可用态 `10.11:1`
- [x] 1.3 行内删除图标键保持 `text` 模式不动。验证：单测断言它仍带 `text` prop；规格场景「Row delete icon key stays bare」覆盖

## 2. 用例与门禁

- [x] 2.1 `SnapshotListDrawer.spec.ts`：新增「清空键不是 text 型、行内删除键仍是 text 型」对照断言（替身补声明 `type` / `text` 两个 prop —— Element Plus 把它们消费成类名，透不到替身 DOM，第一次尝试用 `attributes('type')` 被 `<button>` 的 IDL 钳成 `submit`，改为读 prop 后成立）。验证：4 条用例全绿；全量 `npx vitest run` 50 文件 / **256** 用例通过（较改前 +1）
- [x] 2.2 前端门禁：`npm run lint:styles`（退出码 0，批 1 / 1b / 2 / 3 / 4 全过）、`npx vue-tsc --noEmit`（**错误仍恰为 3 条既有 `ProjectTree.vue`**，逐条核对无新增）、`npx vitest run`（50/256）、`npx vite build`（✓ built in 1m22s）
- [x] 2.3 真浏览器实测（Playwright，`temps/probe_clear_key_after.py`）：对照测量「一键清空」与侧栏「退出」的几何 / 底色 / 文字色 / 对比度；并留三张特写（启用态清空键、退出键参照、抽屉 meta 行整体）。验证：几何逐项同值、启用态 `5.97:1`、不可用态灰底无阴影 `10.11:1`、meta 行无裁切

## 3. 规格与归档

- [x] 3.1 `specs/frontend-doodle-button/spec.md` delta（ADDED 需求 + 4 场景）。验证：`npx openspec validate sync-snapshot-clear-key-skin --strict` 通过
- [x] 3.2 归档：`npx openspec archive sync-snapshot-clear-key-skin -y`；验证：归档成功、`npx openspec validate --specs --strict` 全绿

## 4. 验收留痕（apply 期实测）

- **参考元素的确认**：用户给的 `//*[@id="app"]/div/aside/div[1]/div/div[2]/button` 经 `document.evaluate` 解析为 `button.el-button.el-button--small.logout-btn`（`data-testid="sidebar-logout"`，文本「退出」），其父链为 `.app-shell > aside.sidebar > .sidebar__footer > .sidebar__user-card > .sidebar__user-row`。样式真相源：`AppSidebar.style.css` 的 `.logout-btn`。
- **改前实测**：清空键 class `el-button--danger el-button--small is-disabled is-text`，`border:0px`、`border-radius:4px 8px`、`background:rgba(0,0,0,0)`、`color:rgb(242,192,189)`、`box-shadow:none`；参考键为 `2px solid`、`2px`、`rgb(245,107,106)`、`white`、`2px 2px 0 0`。
- **改后实测（启用态）**：`border-radius:2px`、`border:2px solid rgb(30,30,36)`、`background:rgb(178,56,56)`、`color:rgb(255,255,255)`、`box-shadow:rgb(30,30,36) 2px 2px 0 0` → 除底色深浅与字号/内边距外与参考键逐项同值。**不可用态**：`background:rgb(201,202,204)`、`color:rgb(30,30,36)`、`box-shadow:none`、`opacity:1`。
- **对比度决策（经用户确认）**：参考键的 `--app-marker-red`(#f56b6a) + 白字只有 **2.92:1**，低于 `frontend-doodle-button` 自己写的 4.5:1（元素定位「删除」键同值同问题）；故底色改用 EP 实心 danger 的深红 `--el-color-danger`(#b23838) + 白字 = **5.97:1**。**参考键与元素定位删除键的 2.92:1 缺口是既有问题，本单未改**，登记待另单。
- **启用态的测量方法（如实说明）**：`e2e_probe` 账号当前 0 条快照，故启用态用「摘掉 `disabled` 属性 + `is-disabled` 类」后再测 —— Element Plus 的禁用样式完全由该类承担，测得的级联与真实启用态等价；不可用态则为页面真实状态。
- **同页影响面**：本页仅两处 `type="danger"`（清空键、行内删除键）；后者是 text 型被 `:not(.is-text)` 排除，行为与外观均未变。`ElMessageBox` 的确认按钮渲染在 body，不在本页作用域内。
- **未涉及**：后端、`api.ts`、接口契约、视图切换、SSE / 文件下载 / WebSocket（本改为纯样式 + 一个 prop，`vue-frontend-check` 的「六、协议对照」不适用）。
- **顺带发现（未处置）**：`--app-marker-red` 作危险实心键底色时白字仅 2.92:1，凡用它 + 浅色字的按键（侧栏「退出」、元素定位「删除」、`DoodleBtn` marker tone 等）都低于 4.5:1 —— 属令牌选型的既有问题。
