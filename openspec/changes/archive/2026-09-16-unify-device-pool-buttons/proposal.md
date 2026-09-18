## Why

设备管理页（`/devices`）的按键当前并存 **5 套外观**，用户已明确要求按侧栏底部「退出」按钮
（`button.logout-btn`，即 `//*[@id="app"]/div/aside/div[1]/div/div/button/span`）统一样式：

| 按键组 | 现有几何（读码核实） |
| --- | --- |
| 局域网 / 刷新（`.action-bar-btn`） | 2px 墨边、`--app-radius-sm`、**无阴影**（`box-shadow: none !important`） |
| 上一页 / 下一页（`.wb-btn`） | 2px 墨边、`--app-radius-sm`、`--app-shadow-sm`、hover 黄底 + `translate(1px,1px)` |
| 表格 / 卡片（`.view-btn`） | **无自身边框**，靠容器 1px 白边与 `border-right` 白线分隔、`--app-radius-sm` |
| 显示行数（`.page-size-btn`） | 1px **白**边、`--app-radius-sm` |
| 全部设备 / 在线 / 使用中（共享 `FilterTabs`） | 1px **白**边、`--app-radius-pill` |
| 公开 / 强制释放 / 删除（表格操作列） | 1px 边、`--app-radius-pill` |
| 锁定 / 释放 / 删除（卡片操作） | 1.5px 墨边、`--app-radius-sm`、删除为**虚线**边 |
| 取消 / 连接 / 删除（弹窗） | **EP 默认几何**（全局只改了 `--app-radius-sm`） |
| 重试（共享 `ErrorState`） | 2px 墨边、`--app-radius-sm` |

即同一页内并存 3 种圆角、6 种边框（无 / 1px / 1.5px / 2px / 2.5px / 虚线）与 3 种阴影
（无 / `--app-shadow-sm` / 无）。这与 `frontend-doodle-content-card` 已登记的
「共享涂鸦按钮 SHALL 墨色描边、近直角、硬偏移阴影」口径不一致。

## What Changes

- 新增硬边按键皮肤 `frontend-doodle-button`：几何唯一来源为侧栏「退出」按钮
  （2px 墨色实边、2px 近直角、`2px 2px 0 0 var(--ink)` 扁平硬阴影、hover 上移 1px 且阴影增至 3px），
  交互文字统一 `var(--ink)`。
- 设备管理页全部按键应用该皮肤；切换类控件（显示行数 / 全部设备·在线·使用中 / 表格·卡片）
  未选中为天蓝 `var(--c-workflow)`、选中为柠黄 `var(--c-dashboard)`；
  「局域网」为薰衣草紫 `var(--c-element)`、「刷新」为薄荷绿 `var(--c-device)`；
  其余按键沿用各自既有语义底色。
- **不破坏性**：皮肤作用域限定在 `.device-workbench`，共享 `FilterTabs` / `ErrorState` / `.wb-btn`
  的默认皮肤与其它页面外观 MUST NOT 改变（共享件代码本身不改，仅由页面作用域就地覆写）。
- 卡片「删除」按钮的虚线边并入统一实边（虚线属"外形"，`--ghost` 变体取消）。
- 明确既有约束的边界：「MUST NOT 用冷蓝作为『蓝色』语义」只约束**内容卡操作按钮的语义色调**，
  切换控件的「未选中/选中」二态不属于语义色调。

## 关联文档

- `dev_docs/文档编号对照表.md` **不存在**，故本变更不引用 PRD/ARCH 编号。
- 依据报告：`dev_docs/DEV_TEST/设备管理页面设计元素清单-2026-09.md`（§2.2 按键清册与 §3 口径问题）
- 皮肤几何来源：`openspec/specs/frontend/sidebar-doodle/spec.md`（「退出」按钮：马克笔红实心底、墨色边框、扁平偏移阴影）
- 对比度约束来源：`openspec/specs/frontend-l0-design-tokens/spec.md`（交互文本与自身背景对比度 MUST ≥ 4.5:1）

## Capabilities

### New Capabilities
- `frontend-doodle-button`: Doodle Craft 硬边按键皮肤 —— 皮肤几何、页面内按键的角色底色分配，以及皮肤的作用域约束。

### Modified Capabilities
- `frontend-doodle-content-card`: 「Shared doodle buttons use marker tones」中的「MUST NOT 用冷蓝作为『蓝色』语义」需要限定作用范围，明确其只约束内容卡操作按钮的语义色调。

## Impact

- 前端页面：`/devices`（`frontend/src/modules/device-pool/`）
- 改动文件：`index.vue`、`DevicePoolView.style.css`、`components/DeviceCard.vue`、`components/DeviceActionsCell.vue`
- 共享件`FilterTabs.vue` / `ErrorState.vue` / `workbench-theme.css` **不修改**（由页面作用域覆写）
- 无后端、无 API 契约、无依赖、无路由变更
- 属**有意的视觉变更**：设备管理页按键外观与其它页面不同（用户明确选择"仅设备管理页"）
