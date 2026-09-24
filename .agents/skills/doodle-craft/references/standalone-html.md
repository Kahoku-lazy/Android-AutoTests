# 场景二：单文件 HTML（预览稿 / 原型 / 报告）

需求方说"给我个 HTML 看看"、要原型、要一次性报告时走这条路：**一个自包含 `.html`，不联网、不构建**，用浏览器的 hover / 微倾效果让人直接感受。

产出的临时文件放 `temps/`（仓规）；要长期留档才挪到 `dev_docs/`。

## 1. 铁律：令牌值从 `tokens.css` 抄，不发明

单文件页没有构建步骤，所以要把**用到的**那部分令牌抄进 `:root`。抄的时候逐值对齐 `frontend/src/shared/styles/tokens.css`，**不要凭印象调色**，也不要新增令牌——这个页面代表的是平台现有视觉，色差一点就不是同一套设计了。

```css
:root {
  /* 颜色原子（只抄用到的） */
  --color-white: #ffffff;
  --color-lime-94: #fffef5;   --color-orange-76: #d8d2c4;
  --color-indigo-13: #1e1e24; --color-indigo-76: #a78bfa;
  --color-yellow-70: #fcdc6b; --color-yellow-63: #f7c948; --color-yellow-62: #ffd93d;
  --color-green-61: #6bcb77;  --color-green-87: #c8f5d0;  --color-green-33: #2d7a31;
  --color-teal-49: #4ecdc4;   --color-cyan-74: #89cff0;   --color-red-83: #ffb5a7;
  --color-red-69: #f56b6a;    --color-red-95: #ffe9e8;    --color-red-46: #b23838;
  --color-purple-73: #e879f9; --color-ink-47: #7c6f83;    --color-ink-57: #96918c;
  --color-ink-79: #c9cacc;    --color-ink-34: #5d5950;
  /* 核心色与模块色 */
  --ink: var(--color-indigo-13);  --paper: var(--color-lime-94);
  --app-bg-card: var(--color-white); --app-bg-subtle: var(--color-lime-94);
  --app-highlight: var(--color-yellow-70);
  --app-text-secondary: var(--color-ink-57); --app-stat-text: var(--color-ink-34);
  --c-dashboard: var(--color-yellow-63); --c-device: var(--color-green-61);
  --c-element: var(--color-indigo-76);   --c-case: var(--color-teal-49);
  --c-runner: var(--color-red-83);       --c-report: var(--color-ink-47);
  --c-ai: var(--color-purple-73);        --c-workflow: var(--color-cyan-74);
  /* 状态色 */
  --app-status-success-bg: var(--color-green-87); --app-status-success-text: var(--color-green-33);
  --app-status-danger-bg: var(--color-red-95);    --app-status-danger-text: var(--color-red-46);
  --app-marker-red: var(--color-red-69);          --app-offline: var(--color-ink-79);
  /* 字体 / 字号 / 间距 / 圆角 / 阴影 / 动效 */
  --app-font: "Cascadia Mono", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", monospace, sans-serif;
  --app-font-mono: "Cascadia Mono", "Consolas", monospace;
  --app-size-xs: 12px; --app-size-sm: 14px; --app-size-md: 16px;
  --app-size-lg: 20px; --app-size-xl: 24px; --app-size-2xl: 32px; --app-size-3xl: 48px;
  --app-space-xs: 4px; --app-space-sm: 8px; --app-space-md: 16px;
  --app-space-lg: 24px; --app-space-xl: 32px; --app-space-2xl: 48px;
  --app-radius-sm: 4px 8px; --app-radius-md: 6px 10px; --app-radius-lg: 8px 14px;
  --app-radius-pill: 4px 10px 6px 8px; --app-radius-table: 4px 10px;
  --app-shadow-sm: 2px 2px 0 rgba(0,0,0,.04);
  --app-shadow-md: 2px 3px 0 rgba(0,0,0,.05);
  --app-shadow-lg: 3px 4px 0 rgba(0,0,0,.06);
  --app-duration-fast: .12s; --app-duration: .15s; --app-duration-slow: .25s;
  --app-ease: cubic-bezier(.25,.1,.25,1);
  --app-topbar-h: 96px; --side-w: 260px;
}
```

> ⚠️ **未声明的 `var()` 会静默失效**：写成 `stroke="var(--comp-paper-mark-teal)"` 却忘了在 `:root` 里声明它，SVG 描边会**整条消失**（`stroke` 回到初始值 `none`），而且控制台不报错。抄令牌时把用到的每一个都声明齐。

## 2. 页面骨架

```html
<div class="shell">
  <aside class="sidebar">…品牌区 + 导航 + 退出…</aside>
  <div class="main">
    <div class="main__doodles" aria-hidden="true"><svg>…稀疏手绘线条…</svg></div>
    <div class="main__body">
      <header class="wb-header">…标题 + 动作区…</header>
      <div class="doc-body">…doc-section 逐个排…</div>
    </div>
  </div>
</div>
```

```css
body { margin: 0; font-family: var(--app-font); font-size: var(--app-size-sm);
       color: var(--ink); background: var(--paper); }          /* L0 暖白实色，禁点阵/横线本 */
.shell { display: flex; min-height: 100vh; }
.sidebar { width: var(--side-w); flex-shrink: 0; height: 100vh; position: sticky; top: 0;
           background: var(--paper); border-right: 2.5px solid var(--ink); }
.main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; position: relative; }
.main__doodles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.main__body { position: relative; z-index: 1; flex: 1 1 0; min-height: 0; overflow-y: auto; }  /* 唯一纵向滚动 */
.wb-header { position: sticky; z-index: 10; min-height: var(--app-topbar-h);
             padding: var(--app-space-sm) var(--app-space-lg); background: var(--paper);
             border-bottom: 2.5px solid var(--ink); display: flex; align-items: center; gap: var(--app-space-md); }
.doc-body { padding: var(--app-space-lg) var(--app-space-xl) var(--app-space-2xl); }
```

> ⚠️ **滚动条落在 `.main__body`，不是 window**。写页面没事，但用脚本截图/调试时会踩：`document.scrollHeight` 恒等于视口高、`full_page=True` 只截到首屏。要滚就滚内层：`document.querySelector('.main__body').scrollTop = y`。

## 3. 组件配方（三件套：描边 / 圆角 / 硬影）

**纸片按钮（DoodleBtn）**

```css
.btn { min-height: 32px; padding: 0 14px; border: 2.5px solid var(--ink); border-radius: 2px;
       background: var(--paper); font: 800 var(--app-size-sm)/1 var(--app-font); color: var(--ink);
       box-shadow: 3px 3px 0 0 var(--ink); cursor: pointer;
       transition: transform var(--app-duration-fast) var(--app-ease), box-shadow var(--app-duration-fast) var(--app-ease); }
.btn:hover { transform: translate(-1px,-1px); box-shadow: 4px 4px 0 0 var(--ink); }
.btn:active { transform: translate(2px,2px); box-shadow: 1px 1px 0 0 var(--ink); }
.btn--teal { background: var(--c-case); }  .btn--yellow { background: var(--c-dashboard); }
.btn--danger { background: var(--app-marker-red); color: #fff; }
```

**页头按钮（wb-btn）**：`border: 2px solid var(--ink); border-radius: var(--app-radius-sm); background: var(--app-bg-card); box-shadow: var(--app-shadow-sm);`，hover 底 `--c-dashboard` + `translate(1px,1px)`；primary 底 `--c-dashboard`，success 底 `--c-device`。

**钉板卡（AppCard）/ 撕纸卡（SketchCard）/ 指标卡（KpiCard）/ 胶带卡（DoodleNote）**

```css
.ac-card { position: relative; background: var(--app-bg-card); border: 2.5px dashed var(--ink);
           border-radius: 2px; padding: var(--app-space-md);
           box-shadow: 4px 4px 0 0 var(--ac-accent, var(--c-dashboard));
           transform: rotate(var(--ac-tilt, .3deg)); }
.ac-card:hover { transform: rotate(0) translate(-1px,-1px); box-shadow: 5px 5px 0 0 var(--ac-accent); }
.ac-card__pin { position: absolute; top: -7px; left: 50%; margin-left: -7px; width: 14px; height: 14px;
                border: 2px solid var(--ink); border-radius: 50%; background: var(--ac-accent); pointer-events: none; }
.sketch-card { min-height: 168px; padding: 16px 16px 28px; background: #fff; border: 2.5px dashed var(--ink);
               border-radius: 2px; box-shadow: 4px 4px 0 0 var(--sketch-accent); transform: rotate(-1.2deg); }
.kpi { text-align: center; background: #fff; border: 2.5px dashed var(--ink); border-radius: 2px;
       padding: var(--app-space-md); box-shadow: 4px 4px 0 0 var(--kpi-accent); transform: rotate(-.8deg); }
.kpi__value { font-size: var(--app-size-2xl); font-weight: 800; }
.note { background: var(--paper); border: 2.5px dashed var(--ink); border-radius: 2px; padding: var(--app-space-md);
        box-shadow: 4px 4px 0 0 var(--note-accent); transform: rotate(-.8deg); }
.note__tape { position: absolute; top: -9px; left: 50%; margin-left: -32px; width: 64px; height: 18px;
              background: color-mix(in srgb, var(--note-accent) 55%, transparent);
              border: 1px solid var(--ink); transform: rotate(-3deg); pointer-events: none; }
```

微倾按序号轮转（`--ac-tilt` 逐个换 `-.6 / .8 / -1.1 / 1.2deg`），别全都 0°。

**表纸表格**：虚线墨框 + `border-radius: 2px 6px 2px 4px` + `box-shadow: 4px 4px 0 0 <accent>`；表头底 `--app-bg-subtle`、字 `--app-size-xs` / 700 / `uppercase` / `letter-spacing .04em` / 下框 `2px solid var(--ink)`；单元格下框 `1px solid transparent`（**不画网格线**）；hover 行底 `--paper`；斑马纹 `color-mix(in srgb, var(--color-orange-76) 25%, #fff)`；选中行 `color-mix(in srgb, var(--c-element) 18%, #fff)`。

**表单**：输入框 `border: 2px solid var(--ink); border-radius: var(--app-radius-sm); background: #fff;`，focus 边框 `--c-dashboard` + `0 0 0 3px color-mix(in srgb, var(--c-dashboard) 20%, transparent)`；开关开态 `--c-device` 关态 `--app-offline`；分段控件选中底 `--c-dashboard`。

**三态**：骨架条 `rgba(0,0,0,.05)` + `--app-radius-sm`；错误件底 `--app-status-danger-bg` + 框 `2px solid var(--c-runner)` + 字 `--app-status-danger-text`；空态无框、`padding: 48px 24px`、图标 40px / opacity .5。

**弹窗**：`border: 2.5px dashed var(--ink); border-radius: 6px 10px 6px 10px; box-shadow: 4px 4px 0 0 var(--ink); background: #fff;`

**收尾**：动 `transform` 的类统一加降级块。

```css
@media (prefers-reduced-motion: reduce) {
  .btn, .wb-btn, .ac-card, .sketch-card, .kpi, .note { transition: none; transform: none; }
}
```

## 4. 交付前自检（单文件版）

```
[ ] 令牌逐值对齐 tokens.css，用到的每个 var() 都已声明（含 SVG 描边色）
[ ] 暖白纸面 + 稀疏涂鸦；无点阵/横线本；无模糊阴影；无对称大圆角（999px/50px）
[ ] 卡片有微倾且 hover 回正；字号 ≥12px；间距取刻度
[ ] 三态齐备（加载/失败/空）；危险操作用马克笔红而非 primary
[ ] 动 transform 的类有 prefers-reduced-motion 降级
[ ] 文件放 temps/；标题里写清是"预览稿"，不冒充平台真实页面
```
