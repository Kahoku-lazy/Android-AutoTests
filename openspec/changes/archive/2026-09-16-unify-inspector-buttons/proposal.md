## Why

设备检查器（`/inspector`）页内 9 个按键并存 **3 套外观**，与 `2026-09-16-unify-device-pool-buttons`
已落地的「硬边按键皮肤」不一致：

| 按键组 | 现有几何（读码核实） |
| --- | --- |
| 历史快照 / 已保存页面 / 保存到元素定位 / 结构分析 / 返回元素列表（`button.action-btn`） | 2px 墨边、`--app-radius-sm`（= `4px 8px` 两值不对称）、**无 box-shadow**、hover 仅换底为 `--app-highlight`、disabled `opacity .4` |
| 获取（`button.action-btn--primary`） | 同上，另加墨黑底 `var(--ink)` + 白字 |
| 取消 / 保存（弹窗 `el-button`） | **Element Plus 默认几何**（1px `#dcdfe6` 边、4px 圆角、无阴影） |
| 删除（抽屉 `el-button text type="danger"`） | Element Plus 文字型：无底、无边、无阴影 |
| 筛选 / 错误重试（共享 `FilterTabs` / `ErrorState`） | 由共享皮肤承担，不在本次范围 |

同时 `frontend-doodle-button` 现有一条要求把皮肤作用域**限定在设备管理页**，其 Scenario 原文点名
`/inspector`「按键几何与配色与变更前一致」。因此本变更**必须同步修改该要求**，
否则实现与规格直接矛盾——这是本次真正的约束，而非实现细节。

## What Changes

- 设备检查器页全部「需要硬边外观」的按键应用既有硬边皮肤；几何**不变**，唯一来源仍是侧栏「退出」按钮：
  2px 墨色实边、2px 近直角、`2px 2px 0 0 var(--ink)` 零模糊偏移阴影；hover 左上位移 1px 且阴影增至 `3px 3px`；
  disabled `opacity .5` 且撤掉位移阴影。
- 纳入范围：工具条 6 个原生按键（`index.vue` 5 个 + `CaptureForm.vue` 1 个）+ 弹窗 2 个 `el-button`。
- **MUST NOT 纳入**：抽屉内 `el-button text type="danger"` 图标删除键——文字型按键保持无底无边，
  强行套硬边会在列表行内形成过重色块。
- 底色不重新分配：「获取」沿用既有墨黑底并以主题浅色令牌承载文字（深色底例外）；弹窗「保存」沿用
  `--el-color-primary` 柠黄；其余沿用纸色。MUST NOT 把设备管理页的模块配色（局域网紫 / 刷新绿）搬入本页。
- **BREAKING（规格层面）**：修改 `frontend-doodle-button` 的作用域要求，由「仅设备管理页」改为
  「已登记承载页清单（设备管理 / 设备检查器）」；原 Scenario「打开 `/inspector` … 与变更前一致」必须改写。
- 把 `.action-btn` 的重复声明收敛为单一来源（现逐字重复于 `index.vue:264-272` 与 `CaptureForm.vue:48-57`）。
- **不破坏性**：共享件 `FilterTabs` / `ErrorState` / `DoodleBtn` 与 `workbench-theme.css` / `style.css` /
  `tokens.css` MUST NOT 修改；其它页面按键外观 MUST NOT 改变。不新增任何色值令牌。

## 关联文档

- `dev_docs/文档编号对照表.md` **不存在**，故本变更不引用 PRD/ARCH 编号（与 `unify-device-pool-buttons` 同口径）。
- 设计方案与可点原型：`temps/inspector-buttons-proto.html`（本次评审通过稿，含现状/目标实测对照）
- 皮肤几何来源：`openspec/specs/frontend/sidebar-doodle/spec.md`（侧栏「退出」按钮）
- 对比度约束来源：`openspec/specs/frontend-l0-design-tokens/spec.md`（交互文本与自身背景对比度 MUST ≥ 4.5:1）
- 前序变更：`openspec/changes/archive/2026-09-16-unify-device-pool-buttons/`（该皮肤首次落地，本次复用其几何）

## Capabilities

### New Capabilities

（无。本次不引入新能力，只扩大既有皮肤的作用域。）

### Modified Capabilities

- `frontend-doodle-button`: 「Skin scope is limited to the device-management page」要求的作用域由单页扩为
  「已登记承载页清单」，并新增设备检查器按键几何与状态的 Scenario。

## Impact

- 前端页面：`/inspector`（`frontend/src/modules/device-inspector/`）
- 改动文件：`index.vue`、`components/CaptureForm.vue`（样式与单一来源收敛）；
  `components/SaveToElementsDialog.vue` 仅由页面作用域 `:deep()` 覆写，自身不引入皮肤声明
- 规格：`openspec/specs/frontend-doodle-button/spec.md`（经 delta 修改）
- 共享件 `FilterTabs.vue` / `ErrorState.vue` / `DoodleBtn.vue` 与 `workbench-theme.css` / `style.css` /
  `tokens.css` **不修改**（由页面作用域覆写）
- 无后端、无 API 契约、无依赖、无路由变更
- 属**有意的视觉变更**：设备检查器按键向设备管理页对齐（用户已评审通过 `temps/inspector-buttons-proto.html`）
- 本次不改 `DoodleBtn` 的 2.5px/3px 几何——那是仓库内已存在的第二套硬边几何，留待后续独立变更收敛
