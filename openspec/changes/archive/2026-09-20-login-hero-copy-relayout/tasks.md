## 1. 设计令牌：新增 48px 品牌展示档

- [x] 1.1 `frontend/src/shared/styles/tokens.css` 排版原子区新增 `--font-size-3xl: 48px`，别名区新增 `--app-size-3xl`，并在声明处注明适用层级（品牌展示级、当前唯一消费点为登录页 Hero 标题）；验证：`cd frontend && npm run lint:styles` 通过，且文件中可同时检索到原子与别名两条声明。
- [x] 1.2 同步字号刻度说明 `.agents/skills/doodle-craft/references/tokens.md`（§1.4 由 6 档改为 7 档并补 3xl 行、§1.5 品牌文字字号范围）；验证：文档中 3xl 档取值与 `tokens.css` 一致。

## 2. 登录页 Hero 左栏改版

- [x] 2.1 `frontend/src/views/LoginView.vue`：删除 `p.hero__eyebrow` 整块；把 `p.hero__desc` + 两个 `span.hero__desc-line` 换成三个 `p.hero__tagline`（「实现让AI来做测试」「让测试工作摆脱重复的劳动」「专注于创造价值」）；版本徽标文本与 `aria-label` 改为 `v3.0`；验证：`cd frontend && npx vitest run tests/login` 通过，且渲染文本含四行文案与 `v3.0`。
- [x] 2.2 `frontend/src/views/LoginView.style.css`：标题改用 `--app-size-3xl`；新增 `.hero__tagline` 规则（`--app-size-2xl` + 既有行高/间距刻度）；`.hero__header` 与 `.hero__cta` 收敛到 520px 文本块内居中（`.hero__title-row` 一并居中）；删除 `.hero__eyebrow` / `.hero__desc` / `.hero__desc-line` 规则；同步 `≤768px` / `≤480px` 断点字号；验证：`cd frontend && npx vite build` 通过，且样式文件中无 `font-size` 字面量。
- [x] 2.3 同步 `frontend/src/views/AGENTS.md` 的登录页「前端UI设计」登记（左栏四行文案、字号档位、居中口径、版本徽标 v3.0、眉标移除）；验证：文档条目与实现一致，无残留旧描述。

## 3. 验证与收尾

- [x] 3.1 `frontend/tests/login/p0/LoginView.hero.spec.ts` 补充断言：三行副文案可见、版本徽标为 `v3.0`、左栏不存在独立成行的眉标文案；验证：`cd frontend && npx vitest run tests/login` 全绿（59 tests）。注：`npm run test:p0` 全量套件另有 3 个**先于本次改动**的失败文件（element-locator 表驱动断言与 `api.ts` 不一致等），与登录页无 import 交集，不在本次范围。
- [x] 3.2 浏览器实测（视口 1613×949、DPR=1，Playwright + 截图像素量测）：验证标题墨高落在 48–52px、副行墨高 30–34px、四行文字中心 x 落在 525–550、CTA 行与文案块同心居中。
- [x] 3.3 重跑登录页设计层标注图：`node temps/login-layer-map/login-layer-map.cjs`；验证：`node temps/login-layer-map/login-layer-map.cjs --check` exit 0。
- [x] 3.4 前端门禁自检：`cd frontend && npm run build:check` + `npm run lint:styles` + vue-frontend-check checklist 逐项；验证：全部通过且无新增硬编码色值 / 字号。注：`build:check` 的 `vue-tsc` 阶段有 30 个**先于本次改动**的类型错误（全部在 dashboard 等模块的测试文件，`views/` 命中 0）；`vite build` 本身通过。
