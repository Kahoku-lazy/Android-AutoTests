## Context

- 登录页左栏现状（真实渲染实测，视口 1613×949、DPR=1，Playwright 逐元素测量）：眉标 `p.hero__eyebrow`（12px，文本「AI 自动化测试」）、标题 `.hero-title`（32px，品牌字体，实测墨高 33px）、描述 `.hero__desc`（16px，两行）、CTA 行 `.hero__cta`（y 507–549）。
- 需求 2 给出的 XPath `//*[@id="app"]/div/main/div/div/div[2]/div[1]/p` 已用真实渲染核对：命中 `p.hero__eyebrow`（DOM 链 `#app > .app-shell > main.main-content > .main-content__body > .login-page > .hero(div[2]) > .hero__intro(div[1]) > p`），本次即删除该元素。
- 设计标注为**截图 + 红字批注**：红字字体是标注工具的衬线体，与页面品牌字体（`Ziku FeiYang`）不同，因此红字的**字宽不可直接照搬**，只能取它的**墨高（ink height）**与位置作为尺寸依据。
- 标注红字实测墨高：标题 50px、三行副文案各 31px；当前品牌字体在 32px 时墨高 33px（≈1.03×字号），故对照目标字号为 **48px（标题）** 与 **32px（副行）**。
- 约束：`frontend/AGENTS.md` 硬性规范 §7 要求字号只能取 `tokens.css` 刻度，禁止硬编码；现有刻度最大 32px，故标题尺寸必须新增刻度档。

## Goals / Non-Goals

**Goals:**

- 左栏文案按标注红字的内容、字号与对齐落地：4 行居中、标题 48px、副行 32px，CTA 同行居中。
- 版本徽标改为 `v3.0`；眉标整块移除。
- 新增字号刻度档后，令牌仍然是 `tokens.css` 的唯一真相源，消费处零字面量。
- 认证与右侧 Meeting doodle 行为零变化。

**Non-Goals:**

- 不追求与手绘标注逐像素吻合（标注是手工摆放的，页面块保持既有的视口垂直居中行为）。
- 不改动右栏 Meeting doodle、登录 / 注册表单、错误覆盖层、认证流程与任何接口契约。
- 不新增其它字号档，也不调整既有 6 档的值。

## Decisions

### D1 · 尺寸以「墨高」对齐，而不是「字宽」或标注字体的磅值

- **做法**：用标注红字的墨高反推目标字号 —— 标题 50px ÷ 1.03 ≈ 48px，副行 31px ÷ 1.03 ≈ 32px。
- **理由**：标注字体与页面品牌字体不是同一族，同一个磅值在两者上的字宽差约 15%；墨高（字符实际高度）才是人眼比较「文字大小」的依据，且 32px 正好是既有刻度档、48px 由新增档承接。
- **备选**：按红字字宽对齐（会把标题推到 ≈56px，视觉上比标注更高）——已否；让标注字体成为页面字体 ——违反「字体类型不变」的要求，已否。

### D2 · 新增 48px 刻度档，而不是硬编码或用 `clamp()`

- **做法**：`tokens.css` 排版原子区新增 `--font-size-3xl: 48px`，别名区新增 `--app-size-3xl`；消费处写 `font-size: var(--app-size-3xl)`。
- **理由**：项目硬性规范禁止文本字号字面量，`frontend/tests/check-style-gates.mjs` 批 1 亦按刻度口径校验；`clamp()` / `vw` 会把字号变成视口函数，脱离刻度语义。
- **备选**：标题压回 32px 档（与标注不符，已否）；在组件内声明局部 48px 变量（绕过共享刻度，与令牌唯一真相源冲突，已否）。

### D3 · 三行副文案建模为三个块级文案行，行距用既有的间距刻度

- **做法**：把原 `p.hero__desc` + 两个 `span.hero__desc-line` 换成三个 `p.hero__tagline`；行高取 1.7（沿用描述行既有口径），相邻行用 `--app-space-lg`（24px）分隔；标题行与首行副文案之间用 `--app-space-lg` 分隔。
- **理由**：标注实测相邻副行墨高间距 75–81px，`32px × 1.7 + 24px = 78.4px` 落在区间内；标题到首行副文案实测 90px，`48 × 1.15 + 24 + 行盒留白 ≈ 87px` 接近。全部取既有刻度，不引新值。
- **备选**：用单个 `<p>` 内 `<br>` 或 `<span>` 分行（行距只能是行高倍数，凑不出标注的松间距，且语义上三行是并列文案，已否）；按标注逐行绝对定位（破坏流式布局与响应式，已否）。

### D4 · 居中口径：文案块宽 520px，左边缘保持在 x≈279

- **做法**：`.hero__header` 与 `.hero__cta` 都取 `max-width: 520px`（沿用 `.hero__desc` 既有文本宽度口径），前者 `text-align: center` + 标题行 `justify-content: center`，后者 `justify-content: center`。
- **理由**：标注四行文字的中心实测在 x≈531–543，而「520px 文本块的中心」为 279 + 260 = 539，与标注吻合；若直接对 580px 的 `.hero__intro` 居中，中心会偏到 569。
- **备选**：整个 `.hero__intro` 用 `align-items: center`（中心偏右 30px，已否）；把文本块整体右移（会改动 Hero 栅格，超出本次范围，已否）。

### D5 · 眉标按「整块删除」处理，而不是留空元素

- **做法**：删除 `<p class="hero__eyebrow">AI 自动化测试</p>` 及其样式规则；不保留空 `<p>`。
- **理由**：需求措辞是「去掉该 p 的文本内容」，而该元素的唯一内容就是这段文本；留空元素会继续占用 `.hero__intro` 的 `gap` 形成无意义留白，属于死代码。
- **备选**：保留空元素（产生悬空间距，已否）；用 `visibility/display:none` 隐藏（DOM 里仍留着死文案，已否）。

## 模块防火墙自检

- 本次变更为纯前端展示层改动（`frontend/src/views/` + `frontend/src/shared/styles/tokens.css`），不涉及任何 App / ORM / 写库路径：无跨 App import、无 `api.py` 调用、无数据库接触、无新增接口。
- 未新增跨模块依赖，未触碰 L5 覆盖层（`LoginErrorOverlay`）与认证链路。
- 令牌改动落在共享层 T0 主 token，符合 `frontend-l0-design-tokens`「主 token 是颜色与规格的唯一登记处」与「命名只描述规格」两条需求。

## Risks / Trade-offs

- [字号刻度由 6 档变 7 档，可能被其它页面误用为大标题] → 在 `tokens.css` 注释中写明该档的适用层级（品牌展示级、当前唯一消费点为登录页 Hero 标题），并在 `frontend-l0-design-tokens` delta 中以场景约束。
- [标注是手工摆放的，页面块仍按既有视口垂直居中，纵向位置与标注相差约 60px] → 已在 Non-Goals 明确；验收以「字号、行距节奏、居中中心」为准。
- [改 `LoginView.vue` / `LoginView.style.css` 会让 `temps/login-layer-map/` 产物过期] → 按 `frontend/AGENTS.md` 的路由重跑生成器，并以 `--check` 确认已同步。
- [现有 P0 用例只断言包含标题文本，改动后可能漏检] → 在 `LoginView.hero.spec.ts` 补充四行文案、`v3.0`、眉标移除的断言。
- [旧文案（两行描述、眉标）在别处被复用] → 变更前已检索 `v2.1` / `hero__eyebrow` / `hero__desc` 引用，命中的只有登录页自身与其用例，无跨页依赖。
