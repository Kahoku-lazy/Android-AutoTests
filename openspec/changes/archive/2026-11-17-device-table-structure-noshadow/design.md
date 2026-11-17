# 设计：设备表结构借用与表纸去影

## Context

现状（`/devices` 表格视图）：`AppTable` 渲染 7 列，列头纯文字；首列 `<div class="dev-id">` 两行纯文本；操作列在 `DeviceActionsCell.vue` 里按 `connection_type` 条件渲染最多 3 个 `el-button`；表纸皮肤来自共享 `.wb-shell .sketch-sheet`（`workbench-theme.css:204-210`），带 `--c-device` 位移硬影。

约束：

- 表纸皮肤由 `frontend-doodle-sketch-table` 拥有，且明令「登记线型只覆写 `border-style`，宽度与颜色取 `--comp-sheet-border`」。
- 共享 `.sketch-sheet` 另有 9 处消费方（报告 / 用例 / 缺陷 / 运营 ×3 / 串口日志 ×2 / 用例预览），任何共享层改动都会波及它们。
- `index.vue` 已 283 行，接近 500 行红线，新结构不能再内联堆进去。
- 样式门禁 G12（阴影模糊必须 0）、G13（圆角白名单）、G14（动效令牌）会拦下「柔光阴影 / 对称大圆角 / 裸时长」。

## Goals / Non-Goals

**Goals**：列头可扫读、首列一屏说清身份、操作列主次分明、设备页表纸不再有硬影；全部落在 device-pool 模块内，共享件零改动。

**Non-Goals**：不换底色、不改圆角、不改斑马与无网格线、不加搜索、不改卡片视图与设备检查器、不引入新的设计令牌。

## Decisions

### D1 边框保持共享令牌，只去影

去影用 `box-shadow: none` 写在 `.device-workbench :deep(.sketch-sheet)`（合并进 `DevicePoolView.style.css:334` 已有的实线覆盖），描边宽度 / 颜色 / 圆角继续由 `--comp-sheet-border` 与 `--comp-sheet-radius` 提供。

理由：`frontend-doodle-sketch-table` 明令模块不得另写描边宽度与颜色；用户的要求是「不要阴影」，不是「加粗边框」。把边框提到 2px 墨需要新增 `--comp-sheet-border-strong` 并再改一次 spec，收益只有观感微调，留作 P2。

*替代方案*：加 2px 墨边（原型里演示过）。视觉上更「框得住」，但要新增令牌并突破上述禁令，本次不做。

### D2 表头图标走列配置 + 表头插槽，不改 `AppTable`

`ColumnConfig` 增加可选 `icon`，`COLUMNS[]` 填 emoji；页面用 `AppTable` 已支持的 `#header-<prop>` 插槽渲染「图标 + 列名」。

理由：`AppTable` 的表头插槽本就为这类诉求存在（`frontend-l4-data-surface` 的「Registered exceptions」场景），加一个 `icon` prop 反而把 emoji 渲染策略钉进共享件。`title` 保持纯文字，tooltip 与读屏不受污染。

*替代方案*：把 emoji 直接拼进 `title`（零组件改动）。会让 tooltip 带 emoji、列名语义变脏，只在临时验证时可用。

### D3 首列下沉为 `DeviceIdentityCell.vue`

新组件接 `device: DeviceRecord`，内部用 `IconDevice` 做图标圆、按 `status` 出状态点、两行展示型号与 `serial · address`。`index.vue` 的 `#cell-device` 改为一行组件调用。

理由：`index.vue` 已 283 行；且「组件只渲染、解析逻辑下沉」是本仓前端规范。地址与型号的格式化沿用 `helpers.ts` 现有 `displayModel` / `deviceAddress`，不在组件里重写。

### D4 操作列：主胶囊 + `el-dropdown`

`DeviceActionsCell` 改为：Wi-Fi 行渲染一个主操作（锁定 / 公开）胶囊 + `⋯` 入口，菜单项为「强制释放」「删除」；USB 行渲染 `—`。

语义保持：`lock` / `release` / `disconnect` 三个 emit 与父级 handler 不变；删除仍走 `openDisconnectDialog` → `DisconnectDialog` 二次确认；设备 `BUSY` 时删除项禁用、执行占用时隐藏强制释放（与现状条件一致）。

*替代方案*：保留三按钮只改样式。与「主次分明」的目标不符，未采纳。

### D5 emoji 只进表头

数据单元格（分辨率、活跃时间）保持无图标，等宽数字对齐不能被 emoji 打散；表头 emoji 用正文字体渲染（`--app-font-*`），避免等宽字体下回退成豆腐块。

## Risks / Trade-offs

- [去影后表格从页面上「浮不起来」，框感偏弱] → 由表头淡底、斑马行与 1px 共享描边共同承担层次；若评审仍觉得弱，P2 再议 `--comp-sheet-border-strong`（需改 spec）。
- [删掉三个按钮后，删除操作多一次点击] → 菜单项文案与禁用态保持显式；删除仍有二次确认，误触代价不变。
- [emoji 在不同字体栈下渲染尺寸不一] → 只出现在表头，且图标与列名之间有固定间距；不参与列宽计算（`white-space: nowrap`）。
- [去影被误改到共享层] → 作用域写死在 `.device-workbench` 下，并在 spec 新增「作用域」要求；报告页硬阴影在验收场景里回归比对。

## Migration Plan

纯前端、无数据迁移。上线即生效；回退 = 删除 `box-shadow: none` 一行（回硬影）+ 注释表头插槽（回纯文本列头），两处互不依赖。

## Open Questions

无。
