## 1. EP 样式去重

- [x] 1.1 先试激进方案：删 `main.ts` 全量 import、只走按需 → 构建后产物**缺 `.el-message-box`**（30 个文件显式 import 的函数式 API 拿不到 resolver 注入的样式）
- [x] 1.2 改保守方案：保留全量 + `ElementPlusResolver({ importStyle: false })`（两处），样式只下发一份
- [x] 1.3 结论写进 `frontend/AGENTS.md`「EP 样式口径（改前必读）」：改回按需前必须先解决显式 import 的样式缺失

## 2. 高度链与滚动链

- [x] 2.1 `App.vue`：`.app-shell` `100vh` → `height:100%`（顺 L0 百分比链）
- [x] 2.2 `App.vue`：`.main-content` 补 `overscroll-behavior: contain`
- [x] 2.3 `LoginView.style.css` / `NotFound.vue`：`100vh` → `100%`
- [x] 2.4 `style.css`：`#app` 兜底注释里的「恰好 100vh」改为「height:100% 与 #app 等高」

## 3. lucide 本地化

- [x] 3.1 `npm install lucide`（^1.45.0，lockfile 锁定）
- [x] 3.2 `index.html` 删除 `<script src="https://unpkg.com/lucide@latest">`
- [x] 3.3 新增 `shared/icons/lucide-registry.ts`：登记 14 个实际使用的图标名（侧栏 12 + 页头 literal 去重）
- [x] 3.4 `main.ts` 注入 `window.lucide = { createIcons: () => createIcons({ icons: lucideIconSubset }) }` + `declare global` 补 `Window.lucide` 类型
- [x] 3.5 先试全量 `icons`（入口 +~700 KB）后改子集（入口回到小体积）

## 4. 基线补充

- [x] 4.1 `style.css` L0 段补 `html { color-scheme: light }`
- [x] 4.2 未做（会复制令牌值、制造第二真相源）：L0 段 5 处 `var()` 兜底值

## 5. 验证与文档

- [x] 5.1 `eslint` 0 problem；`vue-tsc --noEmit` 35 条既有错误不变
- [x] 5.2 `vite build` 成功；CSS 735 → 578 KB、JS 2854 → 2839 KB、`el-*.css` 分包 0 个
- [x] 5.3 `temps/l0-fix-verify.mjs` 16 项**全部 PASS**（含真实浏览器：高度链、overscroll、color-scheme、14/14 图标、0 外部 CDN 请求、0 console 错误）
- [x] 5.4 `frontend/AGENTS.md` L0 节同步（8 处：链图、四行代码范围、能写什么、⑤ 表、⑥ 缺口与 EP 口径）