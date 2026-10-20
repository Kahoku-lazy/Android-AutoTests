## Why

设备检查器与元素定位两个模块整体不再需要，页面流里「关联元素定位页面 / 挑选元素作为端口」的能力也一并去掉。当前这两个模块占 2 个 App、6 张表、2 个前端模块（元素定位 18 个文件），并与仪表盘统计、页面流编辑器、侧栏导航互相耦合；保留它们会让规格与代码长期维护一份没人使用的能力，页面流也无法独立演进。

## What Changes

- **删除后端两个 App**：`apps/device_inspector`（`di_snapshots`）与 `apps/element_locator`（`el_locator_projects` / `el_locator_directories` / `el_pages` / `el_elements` / `el_page_flows`），注销 `INSTALLED_APPS`、`config/urls.py` 两条路由与架构统计表前缀映射。
- **删除数据**：6 张表随退役直接 drop（**BREAKING**，数据不保留、不导出）。
- **删除前端两个模块**：`modules/device-inspector`、`modules/element-locator`，含路由、`main.ts` token 引入、侧栏两项导航与模块色映射；`SaveToElementsDialog` 一并删除。
- **页面流解绑元素关联**：删除 `workflow/api.ts` 对 `/elements/pages/` 与 `/elements/pages/{id}/items/` 的调用、`workflowStore` 的 `linked_elements` / `linked_page_domain` 与「已关联页面…添加元素」提示、节点上下文菜单的元素挑选面板、`PageFlowVueFlow` 的关联元素池读取；后端 `workflow/semantics.py` 与 `semantics_paths.py` 去掉 `element_id` / `trigger_element` / element domain 产出，并保证旧文档缺这些字段时仍能读取。
- **清理存量文档属性**：页面流文档 JSON 里的 `linked_elements` 与 `linked_page_domain` 由迁移清空（只删这两个键，文档本身保留）。
- **删除只服务这两模块的工具**：`utils/xpath.py`、`utils/element_layers.py`。
- **仪表盘**：移除「Android元素」统计卡与页面计数。
- **删除测试**：`tests/device_inspector/`。
- **BREAKING**：`/api/inspector/*` 与 `/api/elements/*` 全部端点消失。

## 关联文档

无 PRD 需求编号：需求来自 2026-10-20 会话确认——两个功能不再需要、数据全部删掉、`utils/xpath.py` 与 `utils/element_layers.py` 一并删。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

**整份退役（8 份，全部 Requirement 移除）**

- `device-inspector-page`: 检查器页面契约整体退役
- `device-inspector-snapshots`: 快照与媒体生命周期契约整体退役
- `device-inspector-layers`: 分层查询契约整体退役
- `element-locator-projects`: 元素定位项目工作台契约整体退役
- `element-locator-page-workbench`: 页面元素工作台契约整体退役
- `element-locator-element-fields`: 元素字段集合契约整体退役
- `inspector-save-to-elements`: 「勾选元素保存到元素定位」契约整体退役
- `element-layering`: 元素分层契约整体退役

**需求级修改（2 份）**

- `ai-page-flow-capture`: 整份退役——别名写入、跳转边落 `el_page_flows`、AI 采集生成页面流文档三条要求的上游全部是元素定位库
- `ai-screen-vision`: 「截屏复用检查器链路」改为「截屏只经 adb 取帧」，并去掉「检查设备检查器公开能力」的场景表述
- `serial-log-page`: 侧栏「数据」分组的顺序去掉「设备检查器」「元素定位」两项

## Impact

- 后端：`apps/device_inspector/`、`apps/element_locator/`（删除）、`apps/dashboard/views.py`、`apps/workflow/semantics.py`、`apps/workflow/semantics_paths.py`、`config/settings.py`、`config/urls.py`、`tools/gen_arch_stats.py`、`utils/xpath.py`、`utils/element_layers.py`；新增一条删表迁移（`element_locator` 与 `device_inspector` 各自）。
- 前端：`modules/device-inspector/`、`modules/element-locator/`（删除）、`main.ts`、`router.ts`、`shared/components/sidebarNavConfig.ts`、`modules/workflow/`（api / store / 两个组件 / types）。
- 媒体：检查器 `media/inspector/` 下的截图与缩略图目录失效，随删表一并视为废弃资产，不在本单清理磁盘。
- 规格：8 份退役 + 3 份修改。**Non-Goal**：其余把这两个模块当「举例/承载页」引用的视觉与布局类规格（`frontend-doodle-button`、`frontend-doodle-sketch-table`、`frontend-doodle-subpage-nav`、`frontend-doodle-sketch-card`、`frontend-split-pane`、`case-manager-workspace-preview`、`frontend-l0-design-tokens`、`frontend-l2-page-region`、`frontend-l3-container`、`frontend-l4-data-surface`、`frontend-l5-overlay`）本单不改，另立一单清理举例引用——它们约束的是共享视觉件与布局，不因页面删除而失效，但举例文字会指向已删页面。
