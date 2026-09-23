## Why

历史快照抽屉里的「一键清空」当前是 Element Plus 的 **text 型** `el-button`（`SnapshotListDrawer.vue` 的 `size="small" text type="danger"`）。设备检查器页的硬边皮肤选择器**明确排除** text / link 型按键（`index.vue` 的 `.el-button:not(.is-text):not(.is-link)`），于是它保持 EP 默认的文字键外观 —— 无边框、无底色、无硬阴影 —— 与整页的墨线硬边风格脱节。

真浏览器实测（Playwright，`temps/probe_clear_button_style.py`）：

| | 「一键清空」（改前） | 参考键：侧栏「退出」 |
|---|---|---|
| class | `el-button el-button--danger el-button--small is-disabled is-text` | `el-button el-button--small logout-btn` |
| border | `0px` | `2px solid rgb(30,30,36)` |
| border-radius | `4px 8px` | `2px` |
| background | `rgba(0,0,0,0)` | `rgb(245,107,106)`（危险红） |
| color | `rgb(242,192,189)`（浅粉） | `rgb(255,255,255)` |
| box-shadow | `none` | `rgb(30,30,36) 2px 2px 0 0` |

用户点名的参考元素 `//*[@id="app"]/div/aside/div[1]/div/div[2]/button` 经 XPath 解析确认就是**侧边栏底部的「退出」键**（`data-testid="sidebar-logout"`，样式在 `AppSidebar.style.css` 的 `.logout-btn`）—— 那正是全平台的硬边按键几何基准，其几何（2px 墨线 / 2px 近直角 / `2px 2px 0 0` 硬阴影）被本页照抄；**色值只取危险红语义，不取它的具体红**（理由见上）。

## What Changes

- 「一键清空」不再使用 EP 的 `text` 模式，从而落回设备检查器页**既有**的硬边皮肤（2px 墨线 + 2px 近直角 + `2px 2px 0 0 var(--ink)` 零模糊硬阴影 + hover 左上位移 1px、阴影增至 3px）。**几何不新造**，直接复用页面作用域已有规则。
- 危险语义保留，但**不照抄参考键的色值**：底色取 EP 实心 `danger` 的**深**危险红（`--el-color-danger` = `--color-red-46` = `#b23838`）、文字取浅色 `var(--color-white)`。理由是实测对比度：参考键的 `--app-marker-red` + 白字只有 **2.92:1**，跌破本 capability 自有的 4.5:1 条款；深危险红 + 白字为 **5.97:1**（已与用户确认取此方案）。先例：设备管理页 `DevicePoolView.style.css:131-136` 对实心 danger 键的同一处理。
- **不可用态**（本人尚无历史快照）改为页面统一的灰键：底色 `var(--color-ink-79)`、撤掉位移阴影、`opacity: 1`，替代 EP 的浅粉文字。
- **行为零改动**：保留原生 `disabled`、二次确认文案与「确认后只调一次清空端点」的既有流程。
- 行内**快照删除**键（同为 text 型图标键）**不动** —— 规格要求 text 型图标键保持无底无边、不被套上边框与硬阴影。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### Modified Capabilities

- `frontend-doodle-button`: 新增「快照抽屉的『一键清空』按键采用危险红硬边皮肤」需求（含启用态几何与配色、不可用态灰键、以及「不改动同行删除图标键」三条场景）。

## Impact

- 前端 2 个文件：`frontend/src/modules/device-inspector/components/SnapshotListDrawer.vue`（去掉 `text`）、`frontend/src/modules/device-inspector/index.vue`（页面作用域补危险红底色与不可用态灰键）
- 测试：`frontend/tests/device-inspector/p0/SnapshotListDrawer.spec.ts` 补「清空键不携带 `text`、携带 `danger` 型别」断言
- 不涉及：后端、接口、清空与确认流程的语义、共享件（`DoodleBtn` / `FilterTabs` / `ErrorState`）与全局主题
