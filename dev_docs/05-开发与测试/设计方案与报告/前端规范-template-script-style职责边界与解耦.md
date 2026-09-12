# 前端 template / script / style 职责边界与解耦规范

> 适用范围：`frontend/` 下所有 `.vue`（Vue 3.4 + Composition API + Doodle Craft）。
> 本规范是**可检查的禁令清单**：每条 = 规则 + 反例（文件:行号）+ 正例 + 依据（真实数据）+ 触发条件与边界。
> reviewer 对照时：先查「触发条件」判断是否命中，再对「反例」判，最后看「边界」是否有合法例外。

---

## 规则速查表

| # | 禁令 | 严重度 | 命中即查 |
|---|------|:---:|---------|
| R1 | 禁止 template 内联 `style=` | 🟠 | 任何新增/修改 template |
| R2 | 禁止 `:style` 做状态/条件切换 | 🟠 | `:style` 含 `?` / `&&` |
| R3 | 禁止内联箭头事件 | 🟡 | `@xxx="() =>"` |
| R4 | 禁止模板内链式 `.filter/.map/.join` | 🟡 | `{{ ... }}` 含方法链 |
| R5 | 禁止组件内直接 `fetch/axios/djangoClient` | 🔴 | 任何 .vue 的 script |
| R6 | 禁止 `catch` 静默吞错（写操作） | 🔴 | 写操作的 `catch` 体 |
| R7 | 禁止直接 `document.querySelector` / `el.style.` | 🟠 | script 内 DOM 访问 |
| R8 | 禁止 scoped 内硬编码色值 | 🟠 | `<style>` 内 `#hex` 主值 |
| R9 | 禁止硬编码字号 `<12px` 或非 `--app-size-*` | 🟠 | `font-size:NNpx` |
| R10 | 禁止非刻度间距 `padding/gap/margin:NNpx` | 🟡 | 15px/20px 等随意值 |
| R11 | 禁止 `:style` 静态样式字符串 | 🟠 | `:style="'...'"` |

---

## R1 禁止 template 内联 `style=`

**反例** `frontend/src/modules/ai-assistant/EvaluatorTab.vue:217`
```html
<div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap">
```

**正例**
```html
<div class="tab-toolbar">
```
```css
.tab-toolbar { display: flex; gap: var(--app-space-sm); margin-bottom: var(--app-space-lg); flex-wrap: wrap; }
```

**依据**：EvaluatorTab 独占 75 处内联 style，全前端 132 处 / 21 文件。

**触发条件**：新增/修改 template，出现 `style=` 即违规。

**边界**：动态数值绑定不属本规则（见 R2 边界）——进度条 `width`、动态图 `backgroundImage` 属合法例外。

---

## R2 禁止 `:style` 做状态/条件切换

**反例** `frontend/src/modules/report-generator/TaskReport.vue:222`
```html
<span class="case-status-text" :style="{ color: ci.fail > 0 ? '#e85f5f' : 'var(--c-workflow)', background: ci.fail > 0 ? 'rgba(232,95,95,0.12)' : 'rgba(111,186,44,0.1)' }">
```
**反例** `frontend/src/modules/report-generator/ReportDetail.vue:372`
```html
<h3 class="sec-title" :style="failedSteps.length > 0 ? { marginTop: '16px' } : undefined">
```

**正例**
```html
<span class="case-status-text" :class="{ 'is-fail': ci.fail > 0 }">
```
```css
.case-status-text.is-fail { color: var(--app-error); background: var(--app-error-bg); }
```

**依据**：6 处 `:style` 内做 `?`/`&&` 状态判断。

**触发条件**：`:style` 表达式中含 `?` 或 `&&` 即违规。

**边界**：**动态连续数值**例外——进度条宽度 `:style="{ width: (record.rate ?? 0) + '%' }"`（TaskReport.vue:308）、动态图片 `:style="{ backgroundImage: url(...) }"`（AgentRouteCard.vue:45）无法用 class 表达，允许。

---

## R3 禁止内联箭头事件

**反例** `frontend/src/modules/device-inspector/components/PageElementsPanel.vue:123`
```html
@change="() => store.toggleCheck(row)"
```

**正例**
```html
@change="toggleCheck"
```

**依据**：1 处（当前仅此一处，守住即可）。

**触发条件**：`@事件="() =>"` 即违规。

**边界**：无例外——内联箭头每次渲染重建，一律抽命名函数。

---

## R4 禁止模板内链式方法表达式

**反例** `frontend/src/modules/workflow/components/WorkflowDirTree.vue:298`
```html
<span class="badge">{{ lib.nodes.filter(n => n.type !== 'folder').length }}</span>
```
**反例** `frontend/src/modules/workflow/components/vueflow/PageFlowNode.vue:148`
```html
关联: {{ data.linkedPageName }} · 已选 {{ data.outputs.filter(o => o.el).length }} 个元素
```

**正例**
```ts
const folderCount = computed(() => lib.nodes.filter(n => n.type !== 'folder').length)
```
```html
<span class="badge">{{ folderCount }}</span>
```

**依据**：7 处（workflow 4 处、EvaluatorTab 1 处等）。

**触发条件**：`{{ }}` 内含 `.filter/.map/.join/.reduce` 即违规。

**边界**：单次属性访问/简单三元（`{{ x ? 'a' : 'b' }}`）允许；仅多级方法链需抽 `computed`。

---

## R5 禁止组件内直接 HTTP

**反例**（当前 0 处，以下为反例示意）
```ts
const data = await fetch('/api/xxx')          // ❌
const data = await axios.get('/api/xxx')      // ❌
```

**正例**
```ts
import { listAgents } from './api'
const data = await listAgents()
```

**依据**：本次扫描 `.vue` 内 `fetch/axios/djangoClient` = **0 处**（分层已达标，属守住型规则）。

**触发条件**：任何 .vue 的 script 出现 `fetch(` / `axios` / `djangoClient` 即 🔴。

**边界**：无例外——业务 HTTP 唯一出口是模块 `api.ts` → `djangoClient`（frontend/AGENTS.md §1.1）。

---

## R6 禁止 catch 静默吞错

**反例** `frontend/src/modules/ai-assistant/EvaluatorTab.vue:40`
```ts
try { const data = await listAgents(); if (data.status) agents.value = data.data?.agents || [] } catch (e) { console.error(e); }
```
（同类：EvaluatorTab.vue:34 / 46 / 122 / 159 / 172，共 6 处）

**正例**（项目内已有）`frontend/src/modules/ai-assistant/AgentDetail.vue:114`
```ts
} catch (err) { console.error('Failed to upload avatar:', err); ElMessage.error('头像上传失败，请稍后重试') }
```

**依据**：11 处静默吞错，EvaluatorTab 独占 6 处。

**触发条件**：写操作的 `catch` 体只有 `console`/空 → 🔴；读操作的 `catch` 无提示但有空态兜底 → 🟡。

**边界**：**读操作（GET）**失败且页面有 EmptyState/ErrorState 兜底，可仅 console（🟡）；**写操作**（增删改/提交）必须 `ElMessage.error`（🔴）。

---

## R7 禁止直接操作 DOM

**反例** `frontend/src/modules/case-manager/CaseFileSheet.vue:109`
```ts
const el = document.querySelector<HTMLTextAreaElement | HTMLInputElement>(`[data-edit-key="..."]`)
el?.focus()
```
**反例** `frontend/src/shared/components/AppSidebar.vue:139`
```ts
document.body.style.cursor = ''
```

**正例**
```ts
const inputRef = ref<HTMLInputElement>()
await nextTick(); inputRef.value?.focus()
```

**依据**：7 处（ScreenshotView 4 处、AppSidebar 2 处、CaseFileSheet 1 处）。

**触发条件**：script 内出现 `document.querySelector/getElementById` 或 `el.style.xxx =` 即违规。

**边界**：截图框按坐标缩放的几何定位（ScreenshotView 的 `box.style.width`）属「程序化布局」，可经 `ref` + 响应式绑定实现，仍不鼓励裸 `style` 赋值——除非是 canvas/坐标类无法声明式的场景。

---

## R8 禁止 scoped 内硬编码色值

**反例** `frontend/src/modules/case-manager/CaseFileSheet.vue:544`
```css
.sheet-tag--app { background: #e6faf8; color: #1a7a74; }
```

**正例**
```css
.sheet-tag--app { background: var(--c-case); color: var(--app-text); }
```

**依据**：硬编码色 207 处 / 36 文件（含 JS 图表字面量）。

**触发条件**：`<style>` 内 `color/background/border` 主值为 `#hex`（非 `var(--x, fallback)`）即 🟠。

**边界**：① ECharts/Canvas/动态 SVG 的 JS 配置字面量允许（如 `TrendBarChart.vue:45` `color:'#6BCB77'`），但改 tokens 后须同步 JS；② `var(--token, #fallback)` 主值已是 token，fallback 可忽略。

---

## R9 禁止硬编码字号 <12px 或非刻度

**反例** `frontend/src/modules/case-manager/CaseFileSheet.vue:538/541`
```css
font-size: 11px;   /* :538 */
font-size: 10px;   /* :541 */
```

**正例**
```css
font-size: var(--app-size-xs);   /* 12px */
```

**依据**：硬编码字号 18 处 / 7 文件，其中 CaseFileSheet 4 处含 10px/11px。

**触发条件**：`font-size: NNpx`（字面量）即违规；`<12px` 直接 🟠 无商量。

**边界**：**无例外**——12px 是硬下限，6 档 `--app-size-xs~2xl` 是唯一合法来源。

---

## R10 禁止非刻度间距

**反例** `frontend/src/modules/ai-assistant/EvaluatorTab.vue:217`
```html
<div style="display:flex;gap:8px;margin-bottom:20px;...">
```
（`20px` 不在 `--app-space-*` 刻度）

**正例**
```css
.tab-toolbar { gap: var(--app-space-sm); margin-bottom: var(--app-space-lg); }
```

**依据**：硬编码尺寸 689 处 / 64 文件（含间距 + 布局尺寸）。

**触发条件**：`padding/margin/gap: NNpx` 且 NN 不在刻度 {4,8,16,24,32,48} 即违规。

**边界**：**布局尺寸（width/height/min-height）不是间距**，可保留 px（骨架非皮肤）；只有间距类（padding/margin/gap）必须走刻度。就近映射带来 ±4px 位移是可接受的。

---

## R11 禁止 :style 静态样式字符串

**反例** `frontend/src/modules/workflow/components/vueflow/NodeContextMenu.vue:167`
```html
<span :style="'display:inline-block;padding:1px 6px;border-radius:4px;font-size:var(--app-size-xs);...;background:' + (ep.method === 'GET' ? '#6fba2c' : ...)">
```

**正例**
```html
<span class="api-method" :class="methodClass(ep.method)">
```
```css
.api-method.get { background: var(--success); }
```

**依据**：`:style` 把整段样式拼成字符串（R2 的升级版：连布局一起内联）。

**触发条件**：`:style="'css字符串'"` 即违规。

**边界**：同 R2——动态连续数值例外，但静态布局/色值必须进 class + token。

---

## 边界总表（守「不过度设计」红线）

| 场景 | 判断 | 理由 |
|------|------|------|
| ECharts/Canvas 字面量色 | ✅ 允许 | JS 画布不解析 CSS 变量 |
| `:style` 动态进度条宽度/动态图 URL | ✅ 允许 | 连续数值无法用 class 表达 |
| 布局尺寸 width/height px | ✅ 允许 | 骨架非皮肤 |
| 单次属性访问 `{{ x.a }}`、简单三元 | ✅ 允许 | 非方法链，不需抽 computed |
| 读操作 GET 失败 + 空态兜底 | 🟡 可 console | 有空态兜底 |
| 写操作失败 | 🔴 必须提示 | 静默=假成功 |

> 完整严重度量规见 `vue-frontend-check` skill `references/calibration.md` §2；主题值查 `tokens.css` 皮肤维度。
