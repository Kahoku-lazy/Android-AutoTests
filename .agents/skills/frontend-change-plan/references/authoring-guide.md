# 方案原型编写手册

> 配套 `assets/plan-prototype-template.html`（1491 行 / 58KB，自包含：CSS 全在 `<style>`，交互全在文末 `<script>`，无构建、无 CDN 依赖，双击即可看）。
> 用法：**整份复制**，只改章节内容与配色变量，保留骨架。下文行号对应当前 `assets` 副本。

## 1. 拷贝与落位

```powershell
Copy-Item .agents/skills/frontend-change-plan/assets/plan-prototype-template.html temps/<name>-proto.html
```

命名同族（既有 7 份原型都在 `temps/`）：`doodle-<topic>-proto.html`、`frontend-<topic>-proto.html`、`<topic>-prototype.html`。
方案若要同时交一份正式文档，按项目文档位置约定存放；**原型 HTML 本身留在 `temps/`**，与既有原型一致（它明示"不改平台代码"）。

## 2. 章节契约

新增一个章节必须同时改三处，缺一就会出现空白页或 `undefined` 标题：

1. 加 `<section class="page" id="page-x">`（页面容器）
2. 加 `.nav-item[data-page="x"]`（侧栏按钮）
3. 在文末 `PAGES`（1337-1343）加 `x: ["KICKER", "标题"]`

| 章节 | `id` | 何时必有 | 内容 |
| --- | --- | --- | --- |
| 总方案 | `page-plan` | 必有 | 信息架构表 `table.map` + 版式变体 `.grid-4 > .mini` + Do/Don't `.sticky.do/.dont` + 落地顺序 `.prio-p0/1/2` |
| 子页导航 | `page-nav` | 涉及 L2+ 深度 | 三种导航模版卡 + 面包屑规范片段（`.wb` 里放 `.back-chip` + `.crumbs`） |
| 可点原型 | `page-*` | 必有 | 每个改版主题一节，`.wb` 壳 + `data-accent` + 交互 |
| 其它模块 | `page-matrix` | 多模块时 | 每模块一个小原型 |
| 与已有方案的关系 | 并入 `page-matrix` 末尾 | 必有 | 声明本方案**不重复**哪几份既有原型 / spec |

顺序语义：先说清"改哪些、为什么"（总方案），再给"导航怎么走"，然后才是可点原型，最后一览与去重。

## 3. 配色：区分模块色与示意色

模板 `:root`（11-31）里两套值来源不同，**写方案时不能混为一谈**：

| 类别 | 变量 | 是否等于产品真相源 |
| --- | --- | --- |
| 8 个模块色 | `--c-dashboard` `--c-device` `--c-element` `--c-case` `--c-runner` `--c-report` `--c-ai` `--c-workflow` | **是**，与 `doodle-craft` skill 的模块色表逐值一致 |
| 通用涂鸦色 | `--ink` `#2c2c2c`、`--yellow` `#ffd93d`、`--red` `#ff6b6b`、`--teal` `#4ecdc4`、`--paper-card` `#fffdf0` | **否**，仅原型局部 |

产品真相源是 `frontend/src/shared/styles/tokens.css`：`--ink` = `--color-indigo-13`（`#1e1e24`）、`--paper` = `--color-lime-94`（`#fffef5`）、`--app-bg-card` = `--color-white`。
所以在方案里描述颜色时，请引用**令牌名**（`var(--c-device)`）而不是原型里的字面色值；原型只是示意图。

## 4. CSS 片段速查

| 类 | 用途 | 模板行 |
| --- | --- | --- |
| `.marker` | 黄马克笔高亮（行内强调） | 47-50 |
| `.wavy-teal` / `.wavy-red` | 波浪下划线（正/反例强调） | 51-62 |
| `h2` | 章节标题，自带黄荧光下划线 | 185-192 |
| `.page-lead` / `.sub` / `.meta` | 导语 / 次级说明 / 元信息 | 183-194 |
| `.panel` / `.panel.flat` / `.pin` | 内容面板 + 图钉（`.pin.teal/yellow/green/purple`） | 199-222 |
| `.grid-2` / `.grid-3` / `.grid-4` | 响应式网格 | 224-226 |
| `.mini` | 小卡（自带 `:nth-child` 微倾与轮转阴影） | 228-239 |
| `.sticky.do` / `.sticky.dont` | Do / Don't 对照卡（✓ / ✕ 列表） | 241-248 |
| `.btn` + `.btn-yellow/teal/device/ghost` | 涂鸦按钮（hover 抬升、active 下压） | 250-270 |
| `.chip` + `.chip-ok/busy/mod` | 状态徽标 | 272-283 |
| `table.map` + `.depth-1/2/3` | 信息架构表 + 深度着色 | 285-314 |
| `.wb[data-accent]` / `.wb-head` / `.wb-body` | 工作台壳 + 页头 + 体 | 317-370 |
| `.crumbs` / `.back-chip` | 面包屑（祖先可点 + `.here` 当前项）/ 返回芯片 | 341-369 |
| `.wb-split` / `.tree-pane` / `.content-pane` | 分栏台（`.inspector` 变体左右互换） | 371-411 |
| `.proj-grid` / `.proj-card` / `.tape` | Hub 撕纸入口卡 + 胶带 | 413-441 |
| `.sheet` | 表纸（列表/详情表） | 443-470 |
| `.ai-tabs` / `.ai-tab` | 侧栏子项式页内 Tab | 472-492 |
| `.canvas-mock` / `.node` | 流程图示意画布（节点 + 连线段） | 494-535 |
| `.insp-shot` / `.insp-list` / `.insp-el` | 相纸框 + 元素列表 | 537-563 |
| `.excel-mock` | Excel 纸（带网格线，与 `.sheet` 不同） | 565-581 |
| `.step-rail` / `.step` | 步骤条，标示当前深度 | 583-601 |
| `.hidden` / `.toast` | 显隐开关 / 右下角提示 | 603-617 |
| `.prio-p0/p1/p2` | 落地优先级标签 | 619-629 |

## 5. 已知坑（照抄前先看）

1. **`.wb` 默认阴影是紫色**：`.wb` 用 `--c-element`（320），`data-accent` 只登记了 `ai/case/report/workflow/device`（324-328）。要 `dashboard`/`runner` 必须自己补一条 `[data-accent="..."]`，否则**静默**用紫，看不出报错。`data-accent="element"` 依赖默认值，写法上合法但容易被误读为"已登记"。
2. **`.mini` 的微倾依赖兄弟序号**：`:nth-child(4n+k)`（236-239）只在同一父网格内成立；单独一个 `.mini` 会拿到 4n+1 的 `-0.6deg` 与红阴影。
3. **`prefers-reduced-motion` 只覆盖了一部分**：637-639 只处理 `.nav-item .mini .proj-card .sticky`。`.panel`/`.wb` 本身无 transform 所以无碍，但若你给新片段加了倾角，记得同步加进这条媒体查询。
4. **`.pin` 缺 `pointer-events: none`**（208-218）：产品侧的 `.ac-card__pin` 是有的。图钉若压在可点元素上会吃掉点击——照抄时建议补一行，别让原型出现"点不动"的假象。
5. **`.chip-ok`/`.chip-busy` 重复声明**（196-197 与 281-282，同值）：无害冗余，不必清理。
6. **表体 / 画布 / Excel 区不得旋转**：`.sheet`、`.canvas-mock`、`.excel-mock` 一律不加 transform。长文本与网格一斜就不可读，这是产品硬约束（`frontend-doodle-sketch-table`），原型也必须守，否则方案会给落地方错误示范。

## 6. JS 交互模式

全部基于 `.hidden` 与 class 切换，无框架、无依赖。五种模式：

| 模式 | 位置 | 机制 |
| --- | --- | --- |
| 章节切换 | 1345-1355 | `.nav-item` 的 `data-page` → `#page-*` 加 `.active`；同时改 `#kicker`/`#title` |
| 轻提示 | 1357-1362 | `toast(msg)`，1.4s 后自动消失 |
| 步骤条 | 1364-1371 | `setHubStep(n)`：`.step` 的 `on` + `#hub-N` 互斥显隐 |
| Tab 组 | 1415-1450 | `showAiMain(key)` 切 `#ai-view-*` 与 active 态；深链 `showAiTask()` 改为换页头 |
| 列表→详情 | 1452-1488 | 页头与体**成对**显隐（`rep-head-list`/`rep-detail`、`wf-list`/`wf-canvas`） |

**硬性约束**：任何"进入下一层"的原型都必须提供可见回退——`.back-chip` 或 `.crumbs` 里可点的祖先。不得把浏览器 history 当唯一导航。这是要在方案里固化的产品口径（`frontend-doodle-subpage-nav`）。

## 7. 交付前自检

```
[ ] 章节三处同步：section / nav-item / PAGES 都已加
[ ] 每张图都从真实路由或真实代码读出，没有"大概/应该"的页面
[ ] 所有可点原型都有可见回退（back-chip 或可点祖先面包屑）
[ ] "与已有方案的关系"一节已写明去重结论
[ ] 表体 / 画布 / Excel 区无 transform
[ ] 新增倾角片段已加入 prefers-reduced-motion 媒体查询
[ ] 颜色以令牌名描述（var(--c-*)），未把示意色值说成产品色值
[ ] 落地顺序已给 P0/P1/P2 分批，可直接当 OpenSpec change 的范围输入
[ ] 已确认 frontend/ 零改动（git status 里没有 frontend/ 的改动）
[ ] 文件落在 temps/，命名在同族里
```
