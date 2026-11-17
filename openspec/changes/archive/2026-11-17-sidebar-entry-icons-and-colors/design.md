## Context

侧栏由 `AppSidebar.vue` 渲染，图标走 `data-lucide="<name>"` + `main.ts` 注入的 `createIcons({ icons: lucideIconSubset })`；图标底色与 active 书签条取 `--mod-color`（由 `sidebarNavConfig.ts` 的 `MOD_COLORS[path]` 给出）。

两个既有缺陷：

- `lucideIconSubset` 只登记了 18 个名字，`users` / `cpu` 不在里面，`createIcons` 找不到图标就只留一个色块 —— 页面上表现为「用户管理 / 模型配置 前面是空方块」，且**没有任何报错**。
- `MOD_COLORS` 按「模块」配，不按「入口」配：运营三项共用 `--c-ops`、设备与串口共用 `--c-device`，并排时无法靠颜色区分。

调色板受 `frontend-l0-design-tokens` 约束：颜色原子「以调色板为准且只降不增」，`frontend/tests/check-style-gates.mjs` 的 `PALETTE` 白名单会硬拦新原子（实测新增 `--color-lime-62` 直接被 G8 拦下）。

## Goals / Non-Goals

**Goals:**

- 两个空方块有图标，且与既有 lucide 图标同网格、同线宽。
- 同一分组内的入口颜色两两不同。
- 用测试挡住「图标名漏登记」这类静默缺陷。

**Non-Goals:**

- 不给侧栏新增入口，不改分组顺序与可见性（`requiresOperator` 等）。
- 不替换既有 10 个入口的 lucide 图标为自绘（保持一套图标来源，避免两套画法混排）。
- 不改调色板白名单，不新增颜色原子。
- 不动 `AppSidebar.vue` / `AppSidebar.style.css` 的模板与样式。

## Decisions

**1. 自绘两个图标并登记进 lucide 子集，而不是简单补 `Users` / `Cpu`。**
需求方要求「设计一个、贴合主题」。自绘能贴 Doodle Craft 的手感，且登记进 `lucideIconSubset` 后模板零改动 —— 仍然只写 `data-lucide` 名，不引入第二套组件引用方式。
备选：在 `lucideIconSubset` 补 `Users` / `Cpu`（最省事，但就是通用图形，谈不上设计）；在模板里用 `<component :is>` 引 `shared/icons` 的 Vue 图标（两套渲染路径混排）——均否决。

**2. 网格与线宽对齐 lucide（24 / 2 / 圆头圆角）。**
侧栏同一列里既有 lucide 图标又有自绘图标，重量不一致会一眼看出两套语言。

**3. 入口配色用「别名 + 复用原子」，不碰调色板。**
`--c-account` 复用 `--color-blue-68-s64`（`#7A8FE2`，已成调色板原子且此前无消费方），`--c-task` 复用 `--color-purple-56`（`#6FBA2C`）。理由：调色板只降不增是硬门禁；这两个原子本来就闲置/近用途，包一层 `--c-*` 别名既满足语义又不扩调色板。
备选：新增两个调色板原子（被 G8 硬拦）；直接写色值（违反「颜色一律 var()」）——均不可行。

**4. 任务清单与 AI 助手分开是需求方明确要求的「顺带」项。**
`--c-ai` 原来同时服务两处；改成 `--c-task` 后 `--c-ai` 只归 AI 助手。前端旧测试里 `MOD_COLORS["/tasks"] === "var(--c-ai)"` 的断言同步改。

**5. 「图标必须已登记」写成断言，而不是写进文档。**
这次的缺陷是静默的（不报错、只空着）。在 `sidebarNavConfig.spec.ts` 里遍历 `NAV_CATEGORIES` 按 PascalCase 反查 `lucideIconSubset`，新增入口漏登记立刻红。

## 模块防火墙自检

- 只改 `frontend/src/shared/**` 的配置、图标注册与令牌声明，不跨模块 import，不新增跨 App 依赖。
- 不涉及后端 / 数据库 / 接口；`MOD_COLORS` 仍是纯前端静态映射。
- 新增令牌只进 `tokens.css` 的模块色别名段，值全部 `var(...)` 指向已有原子。

## Risks / Trade-offs

- [自绘图标在 14px 下细节糊掉] → 两个图标都只保留 3-4 个笔画元素，24px 大图与 14px 行内都过了一遍目视确认。
- [`--color-blue-68-s64` / `--color-purple-56` 将来被别的用途占用] → 别名只是引用，冲突时改别名指向即可，不动调用方。
- [调色板里 `--color-blue-68-s64` 是无主原子，可能被清理] → 现在有 `--c-account` 消费，反而保住了它；清理清单若扫「无消费原子」不会再误删。
- [紫 `#C050D0` 比其它彩笔饱和] → 它只出现在「任务清单」一处，紧邻的青绿与桃粉足够拉出层次；若嫌重，可换 `--color-orange-63`，只改一行别名。
