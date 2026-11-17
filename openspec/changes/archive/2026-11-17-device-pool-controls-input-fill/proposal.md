# 设备页控制条：筛选与搜索改成输入件皮肤（135° 渐变填充）

## Why

设备管理页控制条里，「全部设备 · N」下拉与「搜索设备名称 / 序号 / 地址」搜索框套的是**按键皮肤**（`2px` 墨边 + `2px` 硬偏移影 + 粗字，与「刷新」「上一页」同一套几何），几个控件并排看过去分不出哪个能点、哪个要填。需求方要求这两件改成**输入框**的观感，并给与 135° 斜向、浓度 45% → 20% 的颜色渐变填充。

## What Changes

- 「全部设备」下拉与名称搜索框从按键皮肤改为输入件皮肤：墨边保留 `2px`、圆角换成输入框的 `--app-radius-sm`、**撤掉硬偏移影**、字重回到常规。
- 两件的底色改为渐变填充 `--comp-device-field-fill`：`linear-gradient(135deg, color-mix(--c-device 45%), color-mix(--c-device 20%))`，色相取模块色薄荷绿 `--c-device`。
- hover / focus 沿用主题输入框语言（边框转 `--c-dashboard` 柠黄 + focus 扩散环），不再有按键的位移与阴影反馈。
- placeholder 与下拉箭头提到 `--app-text-secondary`：渐变抬亮底色后 EP 出厂灰只剩约 `1.7:1`。
- 「局域网」「刷新」「上一页」「下一页」四个按键**不动**，继续走按键皮肤。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `device-pool-list-controls`：新增「控制条的筛选与搜索是输入件皮肤」要求。

## Impact

- 前端 `device-pool`：`DevicePoolView.style.css`（控制条皮肤块）；`index.vue` 模板不变（`filter-select` / `device-search` 两个类名照旧）。
- 令牌：`shared/styles/tokens.css` 新增一条派生令牌 `--comp-device-field-fill`（两端均 `color-mix` 自 `--c-device`，不新增颜色原子）。
- 样式登记：`.agents/skills/doodle-craft/references/tokens.md` §1.19 与 `references/components/form-controls.md` §1 记录这条已批准的渐变偏离。
- 不动接口、不动后端、不动筛选/搜索逻辑。
