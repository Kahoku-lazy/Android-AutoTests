# 装饰规格 — 纸面涂鸦 / 微旋转 / 图钉胶带

装饰是这套风格的"手工感"来源：**用形状与偏移表达层次，不用模糊与渐变**。装饰一律 `pointer-events: none`，且 `aria-hidden`。

**以代码为准**：`shared/components/PaperDoodles.vue` + `shared/helpers/sketchCard.ts` + 各卡片自包含样式。令牌值见 [../tokens.md](../tokens.md)。

## 1. PaperDoodles 纸面涂鸦（L0 装饰）

- `position: absolute; inset: 0; overflow: hidden; z-index: 0; pointer-events: none`，根带 `aria-hidden="true"`
- **挂载点**：`App.vue` 的 `main.main-content` 内（`.main-content` 提供定位上下文；滚动容器 `.main-content__body` 盖在涂鸦之上）
- **不进侧栏**；`/login` 不挂
- 内容：13 个内联 SVG（螺旋 / 双环 / 波浪 / 箭头 / 星形），描边取 `--comp-paper-mark-*`（brown / red / teal / yellow），opacity 手写在 0.07–0.7
- **纸面本身必须是暖白实色**（`--paper`）：禁止点阵纸纹、横线本、网格纹理充当装饰

## 2. 微旋转机制（卡片网格）

两种做法，**优先第一种**：

1. **共享卡（首选）**：父级用 `shared/helpers/sketchCard` 的 `sketchTiltAt(i)` / `sketchToneAt(i)` 按 `v-for` 下标注入。微倾取自 `SKETCH_TILTS`（`-1.5 / 1 / -0.6 / 1.2 / -1 / 0.8 / 0.4 / -0.9`，即 ±0.4°~1.5° 循环），accent 取 8 个 `--c-*` 轮转；hover 回正与位移由共享卡自己负责。
2. **自建网格**：用 `nth-child(3n+1/2/3)` 三值轮转，量级同档（实际用例 `-0.5 / 0.4 / -0.3deg`）。

```css
.cards > :nth-child(3n+1) { transform: rotate(-0.5deg); }
.cards > :nth-child(3n+2) { transform: rotate(0.4deg); }
.cards > :nth-child(3n+3) { transform: rotate(-0.3deg); }
.cards > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }
```

**禁止**网格中卡片全部 `0deg` 排排坐。微倾请走上面两种机制之一，**不要就地写行内 `transform`**——它会压掉 hover 回正。

## 3. 图钉与胶带

| 装饰 | 规格 | 用在哪 |
|------|------|--------|
| 图钉 `.ac-card__pin` | 14×14、居中置顶、2px 墨框、底 = accent | AppCard（`pin` 可关）|
| 图钉 `KpiCard` deco=`pin` | 12×12，同几何 | KpiCard |
| 胶带 `KpiCard` deco=`tape` | 64×18，斜置（`rotate(-4deg)`），`color-mix(accent 60%, transparent)` + `1px solid --comp-kpi-tape-border` | KpiCard |
| 胶带 `DoodleNote` | 顶中 64×18，`rotate(-3deg)`，色 = `--comp-note-tape` + `--comp-note-tape-border` | DoodleNote `variant="note"` |

三者都 `pointer-events: none`，只做视觉锚点，不承担交互。

## 4. 阴影与圆角的"手工感"边界

- 硬偏移阴影是唯一的立体手法：`--shadow-sm/md/lg`（`2px 2px 0`、`2px 3px 0`、`3px 4px 0`）与强调硬影 `4px 4px 0 0 <模块色或墨色>`；hover 抬起到 `5px 5px 0 0`。
- **模糊半径必须为 0**，禁外发光、禁大扩散。
- 圆角取令牌或登记例外（真实圆形 `50%`、纸角 `2px`）；禁止对称大圆角与等价四值展开。
- 禁 `backdrop-filter: blur()`。
