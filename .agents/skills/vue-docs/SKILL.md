---
name: vue-docs
description: >-
  Use whenever a Vue 3 answer must come from the official docs, not memory —
  「Vue 文档怎么说」「官方推荐哪种写法」「这个 API 是 3.4 还是 3.5 才有」「defineEmits / defineModel / useTemplateRef 怎么用」「升级会不会坏」，
  or when writing/reviewing frontend/** Vue code needs a doc citation.
  固定协议：先钉安装版本（frontend 声明 ^3.4.0、实际 3.5.44）→ 用侧栏地图定位页面 → HTML 截断就改抓 zh-cn Markdown 源 →
  结论带页面 URL 与版本口径。不要凭记忆回答 Vue 语义。Project-local skill for Android-AutoTests.
---

# Vue 3 官方文档读取规范

三类问题**必须**先读文档再答：API 语义与签名、某个特性在哪个版本可用、官方推荐或破坏性变更。
凭记忆答这三类，错一次就会写进 `frontend/`，再被下一个会话当成事实引用。

本技能只管「文档怎么读、读到什么程度算数」；写代码的模式与最佳实践查 `vue` 技能。

## 何时用 / 何时不用

**用**：

- 问「Vue 文档怎么说」「官方推荐」「这个写法对不对」
- 需要 API 的精确签名、参数、返回值、触发时机或生命周期顺序
- 判断「本仓库当前版本能不能用 X」
- 写/审 `frontend/**` 时，需要引用官方原文作为依据

**不用**：

- 只要代码模式、组件拆分、composable 写法 → `vue` 技能
- Element Plus / Vue Router / Pinia 的组件与 API → 各自官方文档，本技能只覆盖 Vue 核心与 SFC 编译器宏
- 纯仓库事实（某文件某行写了什么）→ `read` / `grep`

## 铁律一：先钉版本，再谈文档

站点没有版本化 URL（`cn.vuejs.org` 永远是最新 3.x；只有 Vue 2 在 `v2.cn.vuejs.org`）。同一个链接在不同时间指不同版本，所以「文档说了什么」必须配「对着哪个版本」。

本仓库的三处版本**可能不一致**，回答前先看实际值：

| 来源 | 当前值 | 能不能当准 |
| --- | --- | --- |
| `frontend/AGENTS.md` | 写「Vue 3.4」 | 手写说明，已滞后于安装版本 |
| `frontend/package.json` | `"vue": "^3.4.0"` | 只是范围，不是实际安装 |
| `frontend/node_modules/vue` | **3.5.44**（实测） | 能力问题以此为准 |

```powershell
node -p "require('./frontend/node_modules/vue/package.json').version"
Push-Location frontend; node --input-type=module -e "const v = await import('vue'); console.log(v.version, 'useTemplateRef' in v)"; Pop-Location
```

- 问「仓库能不能用 X」→ 用上面的 `'X' in v` 探测实际安装包，别只凭文档页。
- 问「X 从哪个版本开始」→ 文档 API 页 + [`/about/releases.html`](https://cn.vuejs.org/about/releases.html)。
- **不要**把「抓下来没看到版本」读成「当前版本支持」：版本标注有两种形态——正文一句话（`useModel()` 写「仅在 3.4+ 版本中可用」），或标题后的徽标（`useTemplateRef()`、`useId()` 是 `<sup class="vt-badge" data-text="3.5+">`）。徽标文字放在 `data-text` 里、由 CSS 渲染，**转文本时会整段丢掉**；判版本请看 raw Markdown 或页面源码里的 `data-text`，再配合安装包探测。

## 铁律二：页面从地图来，不猜路径

- 完整目录（指南 51 页 + API 28 页 + 入口页 + 已验证锚点）见 [references/page-map.md](references/page-map.md)。
- URL 形态固定：`https://cn.vuejs.org/guide/<path>.html`、`https://cn.vuejs.org/api/<path>.html`。去掉 `.html` 同样返回 200（实测），但**引用时保留 `.html`**。
- 地图里没有的页面：任一页面都带整份侧栏，抓一页就能重新读出目录；或用 `web_search site:cn.vuejs.org <关键词>`。

## 铁律三：读原文，两级来源

| 级别 | 来源 | 什么时候用 |
| --- | --- | --- |
| ① 站点页面 | `https://cn.vuejs.org/...html` | 默认。中文、与线上同步；代价是导航噪声 + 双 API 分栏 |
| ② 原始 Markdown | `https://raw.githubusercontent.com/vuejs-translations/docs-zh-cn/main/src/<path>.md`（英文 `vuejs/docs`） | 页面被截断、要整页通读、要精确 grep |

`<path>` 就是把站点路径去掉前缀和 `.html`：`/guide/components/events.html` → `src/guide/components/events.md`。

**判完整性看页尾，不看截断提示**：VitePress 页面以「…已经加载完毕」+「上一篇 / 下一篇」收尾，见到它才算读完；
响应末尾出现 `(Content truncated…)` 但页尾齐全，仍算读完（截断只吃掉页脚）；页尾缺失、正文断在半句，就换 Markdown 源。

## 铁律四：双 API 分栏只取一列

页面用两个 `<div>` 并排渲染选项式 / 组合式示例，抓下来同一段代码会出现两份。本仓库统一 `<script setup lang="ts">` + 组合式 API，**只读组合式那一列**；引用时说明取的是哪一列，别把两份拼成一份。

## 标准流程（五步）

1. **定版本**：读 `frontend/package.json` + `node_modules/vue/package.json`，一句话写明本次回答对着哪个版本。
2. **定页面**：从 [references/page-map.md](references/page-map.md) 选页与锚点；API 页优先，指南页补语义。
3. **抓原文**：站点页面 → 不完整就换原始 Markdown；一次只抓需要的页，不整站遍历。
4. **交叉验证**：涉及「本仓库能不能用 / 实际行为」→ 用安装包探测或 `frontend/` 现有用法佐证；文档与代码冲突时两边都摆出来。
5. **落引用**：每条结论配页面 URL（尽量带小节锚点）+ 版本口径；API 结论附「类型」里的签名。

## 引用格式

```markdown
`defineEmits()` 只声明事件、不做校验；校验要用对象语法，返回 `false` 时开发环境告警。
来源：[组件事件 · 事件校验](https://cn.vuejs.org/guide/components/events.html#events-validation)（文档对应 3.x 最新，本仓库安装 3.5.44）
```

- 链接指向**具体小节**，不丢到首页。
- 版本口径写一句就够，别在每段重复。
- 引用 API 时把签名抄成行内代码（`function useTemplateRef<T>(key: string): Readonly<ShallowRef<T | null>>`），避免转述走样。

## 不能做的事

- 把演练场（play.vuejs.org）的「结果展示」当运行时证据——那是构建时预渲染的初始状态，交互结果读不到。
- 用搜索引擎摘要或第三方博客替代原文。
- 把 Element Plus / Vue Router / Pinia 的行为说成「Vue 文档规定」。
- 拿 Vue 2 站点（`v2.cn.vuejs.org`）的内容回答 Vue 3 问题。
- 在 `frontend/package.json` 改动后沿用旧的版本结论——版本一变，本技能第一铁律就要重跑。

## 交付前自检

- [ ] 版本来源写明了（`package.json` / `node_modules` / releases 页）
- [ ] 每条结论有页面 URL，且尽量带锚点
- [ ] 完整性确认过：页尾齐全，或已换 Markdown 源
- [ ] 读的是组合式那一列，没混入选项式示例
- [ ] 没有把「未标注版本」当成「当前版本可用」
- [ ] 与仓库冲突之处（如 AGENTS 写 3.4、实际 3.5.44）已明说，而不是悄悄选一边

## 参考

- [references/page-map.md](references/page-map.md) — 指南 / API 全目录、已验证锚点、URL 模板
- [references/pitfalls.md](references/pitfalls.md) — 抓取与解读的坑，以及每个坑的实证
