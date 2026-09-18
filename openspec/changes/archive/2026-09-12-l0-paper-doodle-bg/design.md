## Context

动机见 `proposal.md` - Why。

当前背景叠了三层不同口径：

1. L0 `body`：`--paper` + `radial-gradient` 点阵（`frontend/src/style.css`）
2. L1 `.app-shell`：实色 `--doodle-bg` `#faf5ee`（`frontend/src/App.vue`）
3. 工作台 `.doc-page--fixed .doc-body`：另一套点阵（`frontend/src/style.css`）

原型 `temps/hand-drawn-doodle-sidebar.html` 口径是：`--paper: #fffef5` 纯色 + `.bg-doodles` 绝对定位稀疏 SVG（注释明确 no ruled lines）。涂鸦挂在 `.stage-body`，不进侧栏。

约束：不破坏 L0 高度/`overflow` 链；颜色走令牌；涂鸦不硬编码散落业务模块。

## Goals / Non-Goals

**Goals:**

- L0 纸面改为暖白实色
- 主区增加可复用涂鸦装饰层
- 去掉工作台内层点阵
- 文档/技能口径与实现一致

**Non-Goals:**

- 不改侧栏/顶栏结构与整壳 `#fffdf8` 对齐（方案 C）
- 不改模块业务组件、字体族、按钮/卡片样式
- 不引入运行时 Canvas/动画粒子作为背景

## Decisions

### 1. 涂鸦挂在 `.main-content`，不挂 `body`

- **选择**：在 `App.vue` 的 `<main class="main-content">` 内放一层装饰组件；该层 `position:absolute; inset:0; pointer-events:none; z-index:0`，`router-view` 内容相对定位且 `z-index:1`，滚动行为保持现状
- **理由**：对齐原型结构；侧栏自然不被涂鸦污染
- **备选**：挂 `body` / `#app` — 会被侧栏盖住或侵入侧栏，z-index 更难控

### 2. SVG 资源收敛到 shared 静态层

- **选择**：从 temps 抽取 `.bg-doodles` 的 SVG，做成 `frontend/src/shared/components/PaperDoodles.vue`，描边/填充色优先用令牌（`--ink`、黄/红/青强调色、咖啡渍棕）
- **理由**：复制不发明；单点维护；模块不各自贴背景
- **备选**：整段 CSS `background-image: url(data:svg)` — 难维护、难调 opacity

### 3. 令牌：统一纸色，L0/工作台停用点阵

- **选择**：`--paper` / `--doodle-bg` 收敛到原型暖白（`#fffef5` 或极近值）；`--dot` / `--app-paper-dot` 可保留但 L0 与 `.doc-body` 背景不再消费
- **理由**：减少三色纸面并存
- **备选**：只改 `body`、保留 `--doodle-bg` — 外壳仍偏黄灰，观感不齐

### 4. 登录页策略

- **选择**：登录页跟随 L0 纸色；`App.vue` 在无侧栏（`/login`）时不挂 `PaperDoodles`
- **理由**：登录已有独立视觉；避免涂鸦与登录 hero 抢戏
- **备选**：登录也挂涂鸦 — 可后续加，不阻塞本变更

### 5. 涂鸦层滚动策略

- **选择**：涂鸦层相对 `.main-content` 绝对定位铺满，**不随页面内容滚动**（纸面水印感）
- **理由**：更接近「纸本身」；内容再长也不会露出空白区缺涂鸦
- **备选**：放进滚动内容流随滚 — 长页底部会空洞

### 6. 文档同步

- 更新 `frontend/AGENTS.md` L0「纸面点阵」表述
- 更新 `.agents/skills/doodle-craft/references/layout.md` §4.2：由「强制点阵 / 禁止纯色」改为「暖白纸面 + 主区稀疏涂鸦；禁止点阵/横线本作为全站背景」

## 模块防火墙自检

- 跨 App import：不涉及后端
- 禁止跨 App import service/runner/…：不涉及
- 写库收敛 api.py：不涉及
- 前端不直连数据库；仪表盘不做写操作：本变更仅样式/装饰层，无写操作

## Risks / Trade-offs

- [涂鸦在密集表格页显得吵] → 控制数量与 opacity（对齐原型）；必要时后续加「低装饰」开关，本变更不做
- [绝对定位层影响点击] → `pointer-events:none` + 内容层更高 z-index
- [与现有白卡片对比度变化] → 卡片仍白底粗边，风险低；目视验收仪表盘/设备池/登录即可
- [技能文档与实现短暂不一致] → tasks 强制同变更改 layout.md / AGENTS.md

## Migration Plan

1. 改令牌与 L0/工作台背景 CSS
2. 新增并挂载 `PaperDoodles`
3. 更新文档口径
4. 本地目视：登录、仪表盘、带 `.doc-page--fixed` 的工作台
5. 回滚：还原 CSS + 移除组件挂载即可，无数据迁移
