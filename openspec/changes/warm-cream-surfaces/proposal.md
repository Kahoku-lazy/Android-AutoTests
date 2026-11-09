## Why

平台里“白”的地方有两套：纸面 --paper 是暖白 #fffef5，卡片/输入框是纯白 #ffffff。纯白在暖色纸面上发冷，卡片与页面的层次也靠两种白硬撑。需求方给了参考图：整体背景是统一的暖米色，卡片靠描边与阴影区分，不再用纯白。

## What Changes

- 表面色原子改为暖米色系：--color-lime-94 #fffef5 → #f3efe2（页面/纸面/浅底），--color-white #ffffff → #f7f3e8（卡片/输入/浮层）。
- 清理残留的 ackground: #fff 字面量（4 个文件、13 处），统一走 ar(--color-white)。
- 模块级已加的柠檬黄/薄荷绿淡底保留，与新的暖米色底叠加后仍在同一暖色系。

## Capabilities

### New Capabilities

无（仅令牌取值与字面量收敛）。

### Modified Capabilities

无。

## Impact

- 前端：shared/styles/tokens.css、AppSidebar.style.css、KpiCard.vue、SketchCard.vue、style.css。
- 后端 / 接口：无。
