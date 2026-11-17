## Context

- 需求方给出两张参考图：按钮五态（Primary 虚线墨边 / Danger 虚线红边 / Highlight 柠黄实心 + 硬影 / Disabled 浅灰虚线 / Teal 青绿实心 + 硬影），输入框四态（默认浅墨虚线 / 聚焦 / 禁用浅底虚线 / 多行 + 小字 label）。
- 主线皮肤与之有三处硬冲突：`DoodleBtn` 的描边态是 `2.5px solid` + `3px` 硬影；`danger` 是实心红底白字；`el-input` 是 `2px solid var(--ink)`。
- `doodle-craft` 把「虚线」限制为只有 `AgentRouteCard` 可用，门禁 `frontend/tests/check-dashed-whitelist.mjs` 存量基线为 0，任何新增虚线直接 `exit 1`。
- 需求方已授权：新增分类 `Sketched UI Kit`，虚线白名单扩到「按钮描边态 + 输入框」，并开本变更留档。

## Goals / Non-Goals

**Goals:**

- 让「按钮五态 + 输入四态」成为技能里有编号、有令牌、有门禁覆盖的**分类**，而不是某页面的就地特例。
- 落地方式做到**可局部启用**：不挂 `.sketch-kit` 的页面外观零变化。
- 首个消费方（运营后台「新建模型」抽屉）一次改完，不遗留第二套手写样式。

**Non-Goals:**

- 不做全站换肤：不把 `.sketch-kit` 挂到页面根，不改 `--el-*` 默认值。
- 不改 `DoodleBtn.vue` 组件本体与既有 tone 语义（组件仍是实线硬影那一套）。
- 不碰卡片、表纸、弹窗、抽屉外框这些容器的线型，也不把它们纳入虚线白名单。

## Decisions

### 1. 用一个作用域根类，而不是新组件或组件 prop

- 备选 A：新增 `SketchBtn.vue`。代价是第二个按钮组件，`: 一个零件一套皮肤」被彻底破掉。
- 备选 B：给 `DoodleBtn` 加 `skin` prop。代价是每个调用点都要改，且组件内部要分叉两套 CSS。
- 选中：作用域根类 `.sketch-kit` + 一份全局样式表。组件不动、未使用的页面零影响，一个类就切换。

### 2. 虚线边框组合值放在 `sketched-kit.css`，颜色原语放 `tokens.css`

门禁 `check-dashed-whitelist.mjs` 按**文件**放行虚线，`tokens.css` 不在白名单里；若 `1.5px dashed var(--comp-kit-line)` 写在张 `tokens.css`，等于要求把整个 T0 文件加进白名单——放行面过大。因此：颜色 / 半径 / focus 环留在 `tokens.css`（`--comp-kit-*`），**虚线组合值声明在 `sketched-kit.css` 的 `.sketch-kit` 作用域内**。

### 3. 选择器写 `.sketch-kit .doodle-btn.doodle-btn`

`DoodleBtn` 的样式是 `<style scoped>`，编译成 `.doodle-btn[data-v-*]`（特异性 0,2,0）；路由组件按需加载，其 CSS 注入时机晚于 `main.ts` 里 `import "./shared/styles/sketched-kit.css"`，同一特异性会输给"后注入者"。重复类名把特异性抬到 0,3,0，让结果与加载顺序无关。

### 4. 危险按钮只改描边色与文字色，不改语义

参考图里 Danger 是"纸底 + 红虚线 + 红字"。文字色取 `--color-red-46`（`--comp-kit-danger-ink`）而不是 `--app-marker-red`：后者在纸底上约 2.5:1，达不到 `tokens.md` §1.3 的 4.5:1 要求。禁用态文字豁免对比度（WCAG 对 disabled 控件的通行处理）。

### 5. label 停在 12px

参考图 label 约 10px，但仓内字号下限是 12px（门禁批 1）。用「12px + `letter-spacing: 0.08em` + 次级墨色」表达"小字标注"的观感，不破刻度。

## Risks / Trade-offs

- [作用域类被滥用成"全局换肤"] → 规格里写死 `MUST NOT` 挂页面根；`SKILL.md` 反模式清单同步。
- [虚线扩散到卡片/弹窗] → 门禁白名单只放行一个样式表，`grep dashed` 越界即失败。
- [作用域覆盖与组件 scoped 样式打架] → 决策 3 用重复类名固定胜出方，并在 CSS 文件头注释说明原因。

## 模块防火墙自检

- 改动只落在 `frontend/src/shared/styles/**`、`frontend/src/main.ts`、`frontend/tests/check-dashed-whitelist.mjs`、`frontend/src/modules/ops-console/model-configs.vue` 与技能文档；无后端、无接口、无 `engines/` 改动。
- 未新增颜色原子；`--comp-kit-*` 全部 `color-mix` / `var()` 派生。
