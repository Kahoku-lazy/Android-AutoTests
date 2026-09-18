## 1. 等价展开形式（零视觉变化）

- [x] 1.1 `4px 8px 4px 8px`（含 `!important` 变体）→ `var(--app-radius-sm)`；验证：该字面量命中数为 **0**
- [x] 1.2 `6px 10px 6px 10px` → `var(--app-radius-md)`；验证：命中数为 **0**
- [x] 1.3 `3px 6px 3px 6px`（含 `!important`）→ `var(--el-border-radius-small)`；验证：命中数为 **0**
- [x] 1.4 `2px 6px 2px 4px` → `var(--comp-sheet-radius)`；验证：命中数为 **0**；四类等价展开合计命中数 **0**

## 2. 对称单值 → 不对称令牌

- [x] 2.1 `999px`（含 `!important`）→ `var(--app-radius-pill)`；验证：`border-radius: 999px` 命中数为 **0**，`var(--app-radius-pill)` 引用数由 **0 → 20**
- [x] 2.2 `4px` / `6px` → `var(--app-radius-sm)`；验证：对称单值命中数 **0**
- [x] 2.3 `8px` / `10px` / `12px` → `var(--app-radius-md)`；验证：同上
- [x] 2.4 `14px` / `18px` → `var(--app-radius-lg)`；验证：同上
- [x] 2.5 `!important` 后缀原样保留；验证：全仓 `!important` 计数 **157**，未下降
- [x] 2.6 汇总：脚本共改动 **41 个文件 / 135 条 border-radius 声明**；验证：改动后"对称单值字面量"合计 **0**、四类等价展开合计 **0**、`999px` 合计 **0**

## 3. 门禁与验收

- [x] 3.1 保留项计数不变：`2px` 19 + `2px !important` 2 = **21**；`50%` 11 + `50% !important` 1 = **12**；`1px` 3、`3px` 3、`5px` 1、`0` 与 `0 !important`、方向性几何 `0 3px 3px 0` / `0 4px 0 0`、登录页 `14px 20px 14px 20px` 与 `18px 26px 18px 26px`、`WorkbenchHeader` 的 `8px 16px 6px 14px` 与 `SkeletonCard` 的 `3px 5px 3px 5px`（后两者按设计 Non-Goals 推迟）；验证：改动后审阅清单逐项符合
- [x] 3.2 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿，别名 48 条与裸色字面量 33 处均未上升
- [x] 3.3 `npx vite build --mode development` 通过（`built in 34.29s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增
- [x] 3.4 编码安全：批量脚本使用 .NET `File.ReadAllLines/WriteAllLines` + `UTF8Encoding($false)`，脚本内容为**纯 ASCII**（吸取变更 12 的编码事故教训）；验证：乱码扫描命中 **0**
- [x] 3.5 Chromium 断言（真实 `tokens.css` + `workbench-theme.css` + 组件样式 + 复刻 DOM，共 **6 项全 PASS**）：`.skeleton-card__bar` 计算为 `4px / 8px / 4px / 8px`（单值 4px 已转不对称）、`.case-card` 为 `6px / 10px`、`.ac-card` 保持登记的 2px 纸角、`--app-radius-pill` 解析为 `4px 10px 6px 8px`、`50%` 圆点例外保留、三者均**不对称**。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 3.6 `git diff --name-only` 清单覆盖 41 个样式文件；建议对 workflow 节点/菜单与 ai-assistant 卡片做页面目视确认（本变更改动面最大的部分在 workflow 的 21 处 `8px` → `6px 10px`）
