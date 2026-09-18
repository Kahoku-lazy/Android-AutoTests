## Context

动机见 `proposal.md` - Why。现状（已核对）：

- `DashboardView.style.css` 以 `scoped` 引入（`dashboard/index.vue:297`），其中 `.doc-page`（`:6`）、`.doc-body`（`:14`）为行首裸选择器；编译后为 `.doc-page[data-v-x]` = 权重 2。
- dashboard 页面根为 `class="doc-page doc-page--fixed wb-shell"`（`index.vue:52`），**无 modifier**。
- 失效证据（静态可证，与 CSS 顺序无关）：`App.vue` 的 `.main-content__body :deep(.doc-page)` 编译为 `.main-content__body[data-v] .doc-page` = **权重 3** > 模块的 **2** → 模块 `.doc-page { height:100%; overflow:hidden }` 恒被压过。
- 死类核对（全仓子串检索，含动态拼接）：`.wb-chip`（css 3 处）· `.wb-status-pill`（1）· `.wb-spinner`（1）· `.wb-btn--teal`（2）· `.wb-btn--berry`（2）· `.wb-btn--sky`（2）—— 除定义外 0 命中；同文件/同族的 `wb-btn--sunset`（`dashboard/index.vue` 在用）与 `wb-loader`（`WbLoader.vue` 在用）**必须保留**。

约束：只碰必须碰的；不做可见改动；不扩大到块级覆写与其它死代码。

## Goals / Non-Goals

**Goals:**

- dashboard 的容器覆写经 modifier 限定，使 `frontend-l3-container` 的「裸选择器命中 0」Scenario 成立
- 删除 6 个零消费 `wb-*` 类
- 顺带清掉 dashboard `.doc-page` 块中已确证失效的 2 个属性

**Non-Goals:**

- 不改 dashboard 的 `.doc-section` / `.doc-section__title` 等**块级**覆写（归 `frontend-l3-content-block` 管辖，不属容器口径）
- 不删 `.agent-card`（同为 0 消费，未纳入本次范围，留作后续）
- 不动 `.el-message--top`（EP 是否渲染该类需单独确认）
- 不做 P2（`animations.ts` 25 个死导出）、P3（111 个死令牌）、P4（其余 6 处 `.doc-page{height:100%}` 死声明）

## Decisions

### 1. dashboard 页面根 modifier 取名 `dashboard-workbench`

- **选择**：与既有 `device-workbench` / `ai-workbench` / `report-workbench` 同族
- **理由**：命名一致，便于 `rg` 检索与后续统一

### 2. 只收窄容器选择器，不碰块级选择器

- **选择**：仅 `.dashboard-workbench .doc-page` 与 `.dashboard-workbench .doc-body`
- **理由**：`frontend-l3-container` 的 Requirement 只约束容器（`.doc-body` / `.doc-page`）；`.doc-section*` 属内容块，若一并收窄会超出本变更的验收依据
- **备选**：一并收窄该文件全部裸选择器 —— 扩大 diff 且无对应 Requirement，否决

### 3. 删除 `.doc-page` 块中的 `height:100%` 与 `overflow:hidden`，保留其余属性

- **选择**：删 2 个属性；保留 `display: flex` / `flex-direction: column` / `background-color: var(--paper)`
- **理由**：被删的 2 条权重 2 < 3 恒被 `:deep(.doc-page)` 压过，删除 = 行为不变；而若**保留**并随选择器升到权重 3，会与 `:deep` 打平、由 CSS 加载顺序决胜（模块 chunk 后加载 → 模块胜），**反而让死声明复活**并改变 dashboard 的滚动归属
- **保留 `background-color` 的理由**：它当前生效并遮蔽主区涂鸦；删除会让 `PaperDoodles` 在 dashboard 显形，属可见变化，不在本次范围
- **备选**：整块删除 —— 同样会改变 dashboard 纸面观感，否决

### 4. P1 的删除判据 = 「定义之外全仓 0 命中」

- **选择**：逐个类做全仓子串检索（覆盖 `.vue` / `.ts` / `.css` / 动态拼接），0 命中才删
- **理由**：避免误伤运行期拼接的类名（如 `.ac-card--` + color 这类动态构造）
- **备选**：连 `.agent-card` 一起删 —— 未在约定范围，留作后续

## 模块防火墙自检

- 跨 App import：不涉及（纯前端样式与类名）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [dashboard 容器覆写权重 2→3] → 与全局 `.doc-page--fixed .doc-body`(2) 的关系由「顺序决胜」变为「确定性胜出」，结果与现状一致（模块 CSS chunk 本就后加载）；需 dashboard 目视复核
- [删类误伤动态拼接] → 已用全仓子串检索确认 0 命中；删后构建 + `vue-frontend-check` 复验
- [dashboard 涂鸦遮蔽行为] → 本变更**不动** `background-color`，遮蔽现状不变
- [无登录态无法自测] → dashboard 目视由用户代验（同 ① ② 先例），并在任务中注明

## Migration Plan

1. 复核 6 个类与 dashboard 覆写现状
2. 补 modifier + 收窄 2 个选择器 + 删 2 个失效属性
3. 删 6 个死类
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. dashboard 三档目视（纸面与涂鸦遮蔽 / 滚动 / 左边缘 / 无裁剪）
6. 回滚：`git checkout` 两个 CSS + 一个 `.vue`，无数据迁移
