# 抓取与解读的坑（都有实证）

写这份清单的目的：这些坑都会「看起来读到了」，但读的是错的东西或错的版本。

## 1. 「Content truncated」不等于没读完

抓 `guide/components/events.html` 时，响应末尾仍带 `(Content truncated. Fetch a more specific URL or section for the full text.)`，
但正文四个小节齐全、页尾「上一篇 Props / 下一篇 组件 v-model」也在——已经读完。

**做法**：判完整性看页尾（「…已经加载完毕」+ 上一篇/下一篇），不看那句截断提示；页尾缺失或正文断在半句，才换 Markdown 源。

## 2. 页面前半截是导航，不是内容

一次整页抓取会先返回主导航、生态链接、14 种语言的互链、整份侧栏、页内目录，然后才是 `# 组件事件` 正文。
**做法**：从「本页目录」之后、以 `# 标题` 开始读正文；页内目录（锚点列表）与正文小节标题同名，别把目录当成正文写进摘要。

## 3. 双 API 分栏会把代码写两遍

页面用 `<div class="options-api">` / `<div class="composition-api">` 并排渲染两套示例，抓下来同一段代码出现两份（`js` 一份、`vue` 一份）。
**做法**：本仓库只用组合式 API + `<script setup>`，只读组合式那一列；引用时说明取的是组合式。

## 4. 版本徽标会「消失」在文本里

`api/composition-api-helpers.html` 的三种版本写法，抓成纯文本后只剩第一种：

- 正文一句：`useModel()` 写「仅在 3.4+ 版本中可用」——能抓到；
- 标题徽标：`## useTemplateRef() <sup class="vt-badge" data-text="3.5+" />`——徽标文字在 `data-text` 属性里、由 CSS 渲染，转文本时整段丢失；
- 同页 `useId()` 也是 `data-text="3.5+"`，同样抓不到。

**做法**：判版本别只看抓下来的正文。看 raw Markdown 的 `data-text`、或看页面源码里的 `vt-badge`，再配合安装包探测。
「文本里没有版本」不等于「没有版本标注」，更不等于「当前版本支持」。

## 5. 仓库版本口径三处不一致

- `frontend/AGENTS.md` 写「Vue 3.4」——手写说明，已滞后；
- `frontend/package.json` 写 `"vue": "^3.4.0"`——范围，不是实际值；
- `frontend/node_modules/vue/package.json` 是 **3.5.44**——实际安装，能力问题以此为准。

**做法**：每次回答先跑一次版本探测；`package.json` 或 lockfile 变动后，旧结论作废。

## 6. 没有按小版本切分的 URL

站点只有 `cn.vuejs.org`（最新 3.x）与 `v2.cn.vuejs.org`（Vue 2）两个域，没有 `/v3.4/` 这类路径。
同一个链接今天指 3.5、下个月可能指 3.6，所以引用必须带「本次对照的版本」一句话。

## 7. `.html` 可以省，但引用别省

`/guide/essentials/reactivity-fundamentals` 与 `...html` 都返回 200（实测两例）。
**做法**：抓取时可省；写进回答的链接统一带 `.html`，读者点开才稳定。

## 8. 锚点不影响抓取

抓 `...events.html#events-validation` 仍然返回整页 HTML。
**做法**：定位小节靠读正文；锚点只在引用时补上，让读者直接落到那一段。

## 9. 页面内链接是站内绝对路径

HTML 里是站内绝对路径（`/api/sfc-script-setup.html#defineprops-defineemits`），Markdown 源里连 `.html` 都没有（`/api/sfc-script-setup#defineprops-defineemits`）。
**做法**：统一补 `https://cn.vuejs.org` 与 `.html` 再贴给用户。

## 10. 锚点名不能凭直觉

`defineEmits()` 的官方链接是 `#defineprops-defineemits`（与 `defineProps` 合并成一个小节），
凭直觉写 `#defineemits` 未必命中。
**做法**：用页面内实际给出的锚点；`references/page-map.md` 的「已验证深链接」只收录页面里出现过的。

## 11. 中文翻译可能滞后英文

中文站由 `vuejs-translations/docs-zh-cn` 维护，可能比英文 `vuejs/docs` 晚一截。
**做法**：中文页缺某段、而英文页有时，抓英文 Markdown 对照；不要因此断言中文文档「错」——先看是不是还没翻译。

## 12. 演练场的「结果展示」不是运行时证据

页面里内嵌的 `play.vuejs.org` 示例，抓下来只有构建时预渲染的初始状态；交互后的 DOM 变化读不到。
**做法**：涉及「运行时到底怎样」的问题，用本仓库/临时脚本实测，或只引用文档的规则性描述。

## 13. 整页抓取很贵

一页常带上 51 条侧栏 + 页内目录，token 成本主要在导航。
**做法**：只抓需要的页；要通读或反复 grep 时改抓 `raw.githubusercontent.com` 的 `.md`，无导航、可整页取。

## 14. 别把「Vue 文档」当 Element Plus / Router / Pinia 的文档

`element-plus`、`vue-router`、`pinia` 各有自己的文档与版本。
**做法**：本技能只对 Vue 核心与 SFC 编译器宏负责；其它库另查，并在引用里标明来源。
