## Why

设备检查器有三类**界面与真实状态不一致**，且都发生在用户已经看得到的地方：

1. **后端写好的失败原因全被丢弃**。`shared/renderers.py:7-10` 明确把 4xx/5xx 的 `{status:false,message}` 交给 `formatApiError()` 消费；但 `store.ts` 的 9 处失败分支（`:124,148,149,176,193,215,236,284,324`）写的是固定文案，catch 里也从不读 `err.response.data.message`。于是「设备正被执行引擎占用（runner-xxx），请等待执行完毕」「同级重名」「快照不存在」等全部变成「获取失败 / 保存失败 / 快照加载失败」。**全仓 40+ 处用 `formatApiError`（element-locator / case-manager / workflow / ai-assistant / login），本模块 0 处**，而同层的 `element-locator-page-workbench` 早已把「展示中文错误信息与重试入口」写成要求。
2. **删除当前快照后仍展示已删数据**。`store.ts:229-232` 只清 `snapshot` 与 `checkedIds`，不清 `analysis`／`selected`，于是结构面板继续渲染已删快照的分区与行、工具条计数照旧，而手机屏幕已空。
3. **快照抽屉静默截断**。`apiGetSnapshots(0, 100)` 与后端 `views.py:47` 的 100 上限叠加，dev 库现有 **309 条**快照时用户只看到 100 条且**没有任何提示**；`snapshotTotal` 正是为「共 N 条」准备的状态，却被写了从不读。

附带两个同主题小缺陷：`error` 单槽被四个数据源共用、成功路径不清（一次设备列表失败会常驻）；错误条上的「重试」只清空提示、不重发请求（`index.vue:89`）。

## What Changes

- 9 处失败分支统一改用共享 `formatApiError`：catch 里读 `err.response.data.message`，保留后端可读原因；原 `data.message` 分支改为「异常 2xx（如 dev 代理回退 HTML）」的兜底，MUST NOT 直接删除
- `error` 由裸字符串改为带来源（`{ message, source }`，source ∈ 设备列表 / 快照列表 / 快照详情 / 结构分析）；成功路径清空对应错误；`ErrorState` 的「重试」改为重发该 source 对应的请求
- `deleteSnapshot` 在删除的是当前快照时，同时清 `analysis` 与 `selected`，使元素表格、页面分区、工具条计数立即回到空态
- 「历史快照」抽屉显示总数并明示展示范围（形如「共 309 条 · 已显示最近 100 条」），消费 `snapshotTotal`
- 新增本模块首个 store 单测 `frontend/tests/device-inspector/p0/store.spec.ts`（错误净化 / 重试重发 / 删除当前快照后回到空态），补齐 `frontend/tests/README.md` 中 device-inspector 的空缺行
- **BREAKING**：无（错误文案由「4 字通用」变为「后端原因」，属缺陷修复不是破坏性变更）

## 明确移出本变更范围

- `SavedPagePicker.vue`（单 2 `fix-saved-page-shot-basis` 与已归档的 `align-inspector-spec-drift` 各自负责）
- `ScreenshotView.vue`（单 2 负责截图基准；watcher 合并已约定移入单 2）
- 已保存页面回看的 `alias` 显示与只读改名（单 3 `fix-inspector-saved-page-alias`）
- 悬空媒体 404 与「删除快照保全被引用文件」（④，待磁盘取舍决策）
- 零消费死代码清退（`purge-inspector-dead-code`，本变更只把 `snapshotTotal` 变为被消费项）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 先例要求：`element-locator-page-workbench`「工作区展示中文错误信息与重试入口」
- 契约依据：`shared/renderers.py`（错误体 `{status:false,message}` 供 `formatApiError` 消费）、`shared/types/api-error.ts`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-page`: 新增「请求失败如实呈现原因」与「快照列表如实反映总量」两条要求；修改「快照删除需二次确认」补删除当前快照后的空态口径

## Impact

- `frontend/src/modules/device-inspector/store.ts`（9 处错误分支、error 结构与重试、删除后清 analysis/selected）
- `frontend/src/modules/device-inspector/index.vue`（ErrorState 的 retry 绑定）
- `frontend/src/modules/device-inspector/components/SnapshotListDrawer.vue`（总数与展示范围）
- 新增 `frontend/tests/device-inspector/p0/store.spec.ts`；更新 `frontend/tests/README.md` 该模块的覆盖状态行
- 后端 / 端点 / 路由 / 迁移：零改动（`snapshotTotal` 消费的是既有 `total` 字段）
- 规格：`device-inspector-page` 1 份 delta（1 改 2 增）