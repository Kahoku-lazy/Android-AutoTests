## Context

- --paper 来自 --color-lime-94（#fffef5），--app-bg-card 来自 --color-white（#ffffff）。
- 仍有 13 处 ackground: #fff 字面量（侧栏、KPI 卡、SketchCard、全局 style.css）。

## Decisions

### 1. 改原子而不是逐组件覆盖

只改两个颜色原子的值，所有引用 --paper / --app-bg-card / --el-bg-color / --el-fill-color-blank 的表面自动跟随，避免 70+ 处局部覆盖。

### 2. 页面与卡片保留一档差异

页面 #f3efe2、卡片 #f7f3e8（亮 4%），不采用完全同色：平台卡片依赖硬阴影与描边，保留一档亮度差能在低对比显示器上仍看出边界。

### 3. 字面量收敛到令牌

13 处 ackground: #fff 改为 ar(--color-white)，后续再调色只需改原子。

## Risks

- [纯白文本色也被改成米色] → 白色文字只出现在深色/彩色底上（如退出按钮），米色仍满足对比。
- [图表/画布里的白色不跟随] → 画布色属 JS 例外，本次不动。
