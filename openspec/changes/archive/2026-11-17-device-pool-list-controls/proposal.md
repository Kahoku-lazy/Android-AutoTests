# 设备管理页：单一表格视图 + 常驻分页 + 下拉筛选与名称搜索

## Why

设备页现在把「看哪台设备」的控制件摊在三处：顶部有「全部设备 / 在线 / 使用中」三个 Tab、一个「表格 / 卡片」视图切换、一个「显示行数 5」按钮组；分页文案与翻页键又在只有多页时才出现。设备一多，视线要在两行控件之间来回跳，而且「找某台设备」只能靠肉眼扫列表。

## What Changes

- **删除卡片视图**：页面只保留表格视图，移除「表格 / 卡片」切换、卡片网格与 `DeviceCard` 组件。
- **删除「显示行数」控件**：每页固定 **7** 行，行数配置仍留在模块 `constants.ts`。
- **分页条常驻**：「第 X / Y 页 · 共 N 台」在左，「上一页 / 下一页」在右；无翻页空间时按键置灰但仍显示。
- **筛选改下拉**：原三个 Tab 改成下拉按键，位置在分页文案右侧，选项保留各状态计数。
- **新增名称搜索**：搜索框紧跟筛选下拉，按设备名称 / 序列号 / 连接地址过滤；筛选与搜索叠加生效。
- 顺带移除顶部与「共 N 台」重复的计数角标。

## Capabilities

### New Capabilities

- `device-pool-list-controls`：设备列表的控制区契约（单视图、固定行数、常驻分页、下拉筛选、名称搜索）。

### Modified Capabilities

- `frontend-doodle-button`：设备页不再有分段 / 切换类控件，按键角色分配改为「命名动作键 + 筛选下拉与搜索框 + 常驻分页键」，原「切换类二态 + 显示行数单选」要求整体退役并被新要求替代。

## Impact

- 前端 `device-pool` 模块：`index.vue`、`DevicePoolView.logic.ts`、`constants.ts`、`DevicePoolView.style.css`，删除 `components/DeviceCard.vue`。
- 共享类型：`shared/types/device.ts` 移除 `DeviceViewMode`。
- 测试：`tests/device-pool/p0|p1/DevicePoolView.logic.spec.ts`（卡片分组用例退役，补搜索与每页行数用例）。
- 不改后端与接口；`usePagination` 与 `FilterTabs` 共享件不动（后者在本页不再使用，仍供其它模块使用）。
