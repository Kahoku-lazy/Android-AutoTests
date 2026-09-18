## 1. report-generator 分区皮肤收敛

- [x] 1.1 删除重复全局属性的裸 `.doc-section` / `.doc-section__header` / `.doc-section__label`、`.doc-section__title` 字号字重覆写与 `.doc-section__title .doc-tag` 整条；只保留 `.report-workbench .doc-section__title`（`display:inline-block; position:relative`）及其 `::after` 波浪下划线；顺带删除因本次收敛而零消费方的 `--rg-shadow-soft`；验证：模块内行首即 `.doc-section`（不含 `--` 修饰符）或 `.doc-section__` 的选择器命中数为 **0**
- [x] 1.2 模板两处行内 `style` 覆写改为类选择器：`.report-workbench .report-table-section` 与 `.report-workbench .report-table-section .doc-section__header`，内边距取令牌；验证：全仓 `doc-section…style="padding` 命中数为 **0**
- [x] 1.3 `doc-tag` 描边恢复可见（改用全局 `.doc-tag` 皮肤）；验证：Chromium 实测该标签 `border-top-color` 为 `rgb(30,30,36)`（墨色），改动前为白色

## 2. ai-assistant 两处裸重定义

- [x] 2.1 `EvaluatorTab.vue` 删除裸 `.doc-section` 与 `.doc-section__title` 两条规则；验证：Chromium 实测该页 `.doc-section` 描边恢复为墨色实线（`rgb(30,30,36)`，对照旧写法为 `1px rgb(255,254,245)` 近白线）
- [x] 2.2 `index.style.css` 的 `.doc-section__header` 改为 `.ai-workbench .doc-section__header`，只保留 `align-items: baseline` 与 `flex-shrink: 0`；验证：文件内不再出现裸 `.doc-section__header`

## 3. 门禁与验收

- [x] 3.1 全仓检索裸 `.doc-section` / `.doc-section__` 选择器命中数为 0；保留的 5 处 `.doc-section--board` 属 `dashboard` 的合规 BEM modifier（本变更不动）；验证：检索结果符合上述区分
- [x] 3.2 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿，别名 48 条与裸色字面量 33 处均未上升
- [x] 3.3 `npx vite build --mode development` 通过（`built in 33.99s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增
- [x] 3.4 Chromium 断言（真实 `tokens.css` + `style.css` + `workbench-theme.css` + 两个模块的真实 style 块 + 复刻 DOM）：**10 项全 PASS** —— **改动前反证**：仿真旧写法（scoped 编译后同为 (0,2,0) 且后置）得到 `1px rgb(255,254,245)` 近白线，即"粗墨纸边消失"；改动后 `/reports` 与 `/ai-assistant/evaluator` 的 `.doc-section` 在描边宽度与颜色、圆角、阴影、内边距上**逐项相同**；标题字号同为 `16px`；`/reports` 的波浪下划线 `::after` 仍在（`background-image` 为 `url(data:image/svg+xml,…)`）；`doc-tag` 描边为墨色。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 3.5 `git diff --name-only` 本变更部分为 3 个文件：`modules/report-generator/index.vue`、`modules/ai-assistant/EvaluatorTab.vue`、`modules/ai-assistant/index.style.css`，与 `proposal.md` 的 Impact 段一致

## 4. 过程中修正的两处我自己的口径问题（如实登记）

- [x] 4.1 **spec 措辞过宽**：初版要求写"SHALL NOT 以裸 `.doc-section…` 选择器覆写"，会误伤 `dashboard` 的**合规** BEM modifier `.doc-section--board`（以附加类与 `.doc-section` 同挂一元素，是规格允许的变体方式）。已改为：允许 `.<模块根类> .doc-section…` 与 BEM modifier 两种登记形式，只禁止裸的块本体 / BEM 部分覆写
- [x] 4.2 **断言不可验证**：初版断言 `border-top-width === '2.5px'`，但 Chromium 的 `border-*-width` computed 值会**向下取整为整数**（实测 DPR=1 与 DPR=2 均返回 `2px`）。已把断言改为可验证形式（两处描边宽度相同且非旧值 `1px` + 颜色为墨色），并同步把 spec 场景措辞由"同为 2.5px 墨色描边"改为"同为墨色实线描边，而非 1px 近白线"