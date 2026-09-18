# 统一卡片语言：消除自建壳与剥壳

## Why

《前端UI风格一致性分析-2026-09》§3.7「卡片语言三种并存」记录了三套并存的卡片实现，而 `openspec/specs/frontend-doodle-appcard-panel` 已明确要求：

> 系统 MUST 通过共享 `AppCard` 呈现可复用数据块……SHALL NOT 再使用实线大圆角 + 彩色顶条作为默认壳。

现状违反该要求的三处：

| 位置 | 现状 | 违反点 |
| --- | --- | --- |
| `report-generator/CaseBreakdown.vue` | `.case-group`/`.bug-case-group` 自建 2.5px **实线** + `--app-radius-lg` 大圆角壳，内部再套 `AppCard`，并用 `:deep(.el-card){border:none!important;box-shadow:none!important;border-radius:0!important}` **剥掉** AppCard 自己的钉板壳 | 双壳叠加；主动剥离共享壳 |
| `device-pool/components/DeviceCard.vue` | 实线 2px + `--app-radius-md` + 2px 小阴影 + 左侧 4px 色条，无图钉、无微倾 | 自建壳，非 AppCard |
| `device-inspector` `index.vue` / `StructureAnalysisPanel.vue` / `SnapshotListDrawer.vue` | 各自实线 2–3px + 扁阴影 | 自建壳，非 AppCard |

## What Changes

- **report-generator**：删除 `.case-group`/`.bug-case-group` 的自建壳声明（含 hover）与两条 `:deep(.el-card)` 剥壳规则，让 `AppCard` 成为唯一壳。依据：`CaseBreakdown.vue:138` 的页根为 `doc-page wb-shell`，已在 `.wb-shell` 作用域内，`.ac-card` 钉板壳（2.5px 虚线墨色边、2px 近直角、`4px 4px 0 0 var(--ac-accent)` 硬阴影、图钉、微倾）本应生效。
- **device-pool**：`DeviceCard` 改用共享 `AppCard`，以其同排 cycle accent 取代自建左侧色条。
- **device-inspector**：3 处自建壳改用共享 `AppCard`。

## Impact

- report-generator：卡片外观由「实线大圆角 + 切角阴影」变为「虚线近直角 + 模块色硬阴影 + 图钉 + 微倾」，且 `.case-group` 的 `overflow:hidden` 一并移除——此前它把 AppCard 的图钉（`top:-7px`）裁掉了。**属有意的视觉变更**，即 spec 要求的外观。
- device-pool / device-inspector：卡片补上钉板特征（图钉 + 微倾 + 模块色硬阴影），失去自建色条/实线边框。
- 仅前端样式与模板层；无后端、无 API、无依赖变更。
