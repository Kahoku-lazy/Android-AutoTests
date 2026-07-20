# Frontend Rules — Android-AutoTests

## 技术栈

Vue 3.4 + Vite 5.4 + Element Plus 2.7 + **animal-island-vue 0.2**（动森主题 UI） + **animejs 4.5**（动画引擎） + ECharts 5.5 + Pinia 2.1

## 主题系统

项目采用 **animal-island-ui**（任天堂《集合啦！动物森友会》游戏风格）作为视觉主题。

### 主题引入

```js
// main.js — 全局注册
import AnimalIslandVue from 'animal-island-vue'
import 'animal-island-vue/style'
app.use(AnimalIslandVue)
```

### 主题分层

| 区域 | UI 库 | 风格 |
|------|-------|------|
| 全局框架 | animal-island-vue | 暖木色、大圆角（24px）、布纹质感 |
| 业务模块（6 个） | Element Plus + animal-island-vue 混用 | 蓝白风格，CSS 变量覆盖为动物森友会色板 |
| AI 助手模块 | animal-island-vue 全组件 | 暖木色/大圆角，CSS 变量覆盖在 `animal-theme.css` |

### animal-island-vue 组件（22 个）

| 基础 | 容器 | 表单 | 装饰 | 特殊 |
|------|------|------|------|------|
| Button | Card | Input | Tooltip | Time |
| Title | Collapse | Select | Cursor | Typewriter |
| Divider | Modal | Switch | Loading | CodeBlock |
| Icon | Tabs | Checkbox | Footer | Phone |
| | Table | Radio | | WeddingInvitation |

> 详细组件 API 参考：[animal-island-ui 设计素材规则](.claude/rules/animal-island-ui.md)

### 动画引擎 animejs

```js
// shared/animations.js — ~30 个预设
import anime from 'animejs'

// 常用动画：
- stagger: 列表逐项弹入
- countUp: 数字滚动增长
- ripple: 点击涟漪效果
- cardTilt: 卡片 3D 倾斜
- pulse: 脉冲呼吸
- svgDraw: SVG 路径绘制
```

- 所有页面过渡、列表动画、交互反馈统一使用 animejs
- 预设集中在 `shared/animations.js`，组件通过 `import { xxx } from '@/shared/animations'` 引用
- App.vue 中通过 animejs 实现 blob 视差背景和导航过渡动画

## 目录结构约定

```
frontend/src/
├── main.js                  # Vue 入口：注册 Element Plus + animal-island-vue + router
├── App.vue                  # 根组件：侧边栏 + 内容区 + 全局 Cursor/blobs
├── router.js                # SPA 路由配置 + beforeEach JWT 守卫
├── style.css                # 全局 CSS 变量 + 毛玻璃 + 字体
├── views/
│   └── LoginView.vue        # 统一登录页（动森主题）
├── shared/                  # 跨模块共享（不归属任何业务模块）
│   ├── api-client.js        # Axios 实例 + JWT 拦截器 + formatApiError()
│   ├── event-bus.js         # mitt 事件总线
│   ├── animations.js        # ~30 个 animejs 动画预设
│   ├── components/
│   │   ├── AppSidebar.vue   # 侧边栏 + AnimatedMascot 吉祥物
│   │   ├── PageHeader.vue   # 页面 Hero Banner
│   │   └── AnimatedMenuIcon.vue
│   └── icons/
│       └── index.js         # 34 个自定义 SVG 图标（defineComponent + h()）
└── modules/                 # 7 个业务模块
    └── {module-name}/
        ├── index.vue        # 模块主页
        ├── routes.js        # 子路由定义（export default [{path, name, component}]）
        ├── api.js           # 模块专用 API 封装（基于 api-client.js）
        ├── store.js         # Pinia 或 composable 状态
        ├── composables/     # 可组合逻辑
        └── components/      # 模块内组件
```

## 组件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | `PascalCase.vue` | `AgentDetail.vue` `AppSidebar.vue` `ChatView.vue` |
| 模板中使用 | `kebab-case` | `<agent-detail>` `<app-sidebar>` |
| 路由入口 | `index.vue` | 每个模块的默认主页 |

## 路由定义模式

```js
// modules/{name}/routes.js
export default [
  { path: '/module-name', name: 'ModuleName', component: () => import('./index.vue') },
  { path: '/module-name/:id', name: 'ModuleDetail', component: () => import('./Detail.vue') },
]

// router.js 汇总
import moduleRoutes from './modules/module-name/routes.js'
routes.push(...moduleRoutes)
```

路由守卫 `beforeEach` 检查 JWT 存在和过期，未登录跳转到 `/login`。

## API 调用模式

```js
// modules/{name}/api.js — 基于 shared/api-client.js
import { apiClient } from '@/shared/api-client'

export function listDevices() {
  return apiClient.get('/api/devices/')
}
export function lockDevice(serial) {
  return apiClient.post(`/api/devices/${serial}/lock`, {})
}
```

**JWT 处理**（api-client.js 拦截器）：
- 请求拦截：自动附加 `Authorization: Bearer <token>`
- 响应拦截：401 时自动用 refresh token 换取新 access token，失败则跳转登录页
- AgentScope SSE 调用：使用独立 client 指向 `:8000`

## 状态管理

- 简单状态：`composables/` 中的 `ref()` / `reactive()`
- 跨组件共享：mitt `event-bus.js`
- 持久化（用户偏好/最近打开）：Pinia store

## 主题与样式

| 区域 | 主题 | CSS 变量来源 |
|------|------|-------------|
| 业务模块（6 个） | Element Plus 蓝白风格 | `style.css` 全局变量 |
| AI 助手模块 | animal-island-vue 暖木色/大圆角 | `animal-theme.css` 覆盖 |

**CSS 变量约定**：
- 全局定义在 `style.css` 的 `:root` 块
- 模块覆盖通过独立的 `*-theme.css` 文件
- 命名使用 kebab-case：`--bg-primary` `--text-secondary`

## SSE 流式对话

```js
// modules/ai-assistant/ChatView.vue 模式
// 1. 创建 AgentScope session → 获取 session_id
// 2. 发送消息到 AgentScope SSE 端点
// 3. 根据 EventType 处理流式事件：
//    TEXT_BLOCK_DELTA → 追加显示
//    TOOL_CALL_START → 显示工具调用提示
//    TOOL_RESULT_END → 显示工具结果
//    REPLY_END → 结束流，调用 save-message 持久化
// 4. 使用 EventSource 或 fetch + ReadableStream
```

## 🔴 使用 animal-island-vue 组件的铁律

**animal-island-vue 的 API 与 Element Plus 不同，禁止凭 Element Plus 经验编写代码。每次使用 animal-island-vue 组件前，必须逐项对照 API。**

### 强制流程（不可跳过）

```
决定使用 animal-island-vue 组件
  ↓
1. 打开 .claude/rules/animal-island-ui.md，找到该组件的 API 表格
  ↓
2. 逐项核对：属性名、合法值、布尔属性 vs 字符串属性的区别
  ↓
3. 搜索已有正确用法作为参考：
     grep -r "<组件名" frontend/src/modules/
  ↓
4. 写完代码后 grep 搜索常见错误模式（见下方速查表）
  ↓
5. 提交前必须 npx vite build 编译通过
```

### animal-island-vue ≠ Element Plus：API 差异速查

| 需求 | ❌ Element Plus 思维（错误） | ✅ animal-island-vue（正确） |
|------|--------------------------|---------------------------|
| **红色按钮** | `type="danger"` | `type="primary" danger`（danger 是布尔属性） |
| **红色描边按钮** | `type="danger" plain` | `danger plain` 或 `type="primary" danger plain` |
| **Tabs 内容区** | 自闭合 + 内容放外面 | 必须用具名 slot `#[tab.key]` 放内部 |
| **Modal 确认** | `@confirm` 事件 | `@ok` 事件 |
| **Switch 双向绑定** | `v-model` | `:model-value` + `@update:model-value` |
| **Modal 内用 Select** | `Select` 组件 | `el-select`（Select 下拉被 Modal clip-path 裁剪） |

### 写完代码后自查命令

```bash
# 检查是否用了 type="danger"（应该是 danger 布尔属性）
grep -rn 'type="danger"' frontend/src/modules/

# 检查 Tabs 是否自闭合（应该用 slot）
grep -rn '<Tabs.*/>' frontend/src/modules/
```

## animal-island-vue 组件常见陷阱

### Button：danger 是布尔属性，不是 type 值

```html
<!-- ❌ 错误：animal-island-vue 没有 type="danger" -->
<AnimalButton type="danger">删除</AnimalButton>
<AnimalButton type="danger" plain>删除</AnimalButton>

<!-- ✅ 正确：danger 是独立布尔属性，红色需要配合 type="primary" -->
<AnimalButton type="primary" danger>实心红色按钮</AnimalButton>
<AnimalButton type="primary" danger plain>红色描边按钮</AnimalButton>
```

> **为什么**：库的红色样式需要 `.animal-btn--danger.animal-btn--primary` 两个 class 同时存在。只写 `type="danger"` 生成的是 `.animal-btn--danger` 单 class，不会触发红色样式。

### Tabs 必须用具名 slot，禁止自闭合

animal-island-vue 的 `Tabs` 与 Element Plus `el-tabs` 一样：标签头 + 内容面板是两部分，**内容必须通过具名 slot 放到组件内部**，否则内容会渲染在 `.animal-tabs` 外面成为兄弟节点。

```html
<!-- ❌ 错误：自闭合，内容在 Tabs 外面 -->
<Tabs :items="tabs" v-model="activeTab" />
<div class="card-grid">...</div>

<!-- ✅ 正确：内容通过 #[tab.key] slot 放入 Tabs 内部 -->
<Tabs :items="tabs" v-model="activeTab">
  <template v-for="tab in tabs" #[tab.key] :key="tab.key">
    <div class="card-grid">...</div>
  </template>
</Tabs>
```

**检查方法**：在浏览器 DevTools 中验证内容是否位于 `div.animal-tabs > div.animal-tabs__content` 内部。如果内容在外面就是自闭合导致的。

### 写组件前先看已有正确用法

改 animal-island-vue 组件前，搜索其他模块中同一组件的用法作为参考模板：

```bash
grep -r "<Tabs" frontend/src/modules/  # 看正确写法
```

## 🔴 Element Plus 组件默认值陷阱

Element Plus 部分组件的默认行为与直觉相反，**使用前必须查文档确认关键 prop 的默认值**。以下为已验证的陷阱：

### el-cascader：v-model 默认绑定路径数组，不是叶子值

```html
<!-- ❌ 错误：默认 emitPath=true，v-model 绑定的是路径数组 [1, 5]，不是单个 ID -->
<el-cascader v-model="form.directory_id" :options="dirOptions" :props="{ checkStrictly: true }" />

<!-- ✅ 正确：显式设置 emitPath: false，v-model 才绑定叶子节点值 -->
<el-cascader
  v-model="form.directory_id"
  :options="dirOptions"
  :props="{ checkStrictly: true, emitPath: false, value: 'value', label: 'label' }"
  placeholder="选择目录"
  clearable
/>
```

> **后果**：`emitPath` 默认 `true` → v-model 值是 `[1, 5]`（路径数组），后端期望单个整数 `5`。保存时类型不匹配，编辑回显时 cascade 不识别单个 ID。**两边都静默失败，只有功能测试能暴露。**

### 强制流程：使用不熟悉的 Element Plus 组件时

```
决定使用 el-cascader / el-tree-select / el-transfer 等复杂组件
  ↓
1. 查文档确认默认值：emitPath / value-key / node-key 等关键 prop
  ↓
2. 确认 v-model 类型与后端期望类型一致（单个值 vs 路径数组 vs 对象）
  ↓
3. 写完代码后 grep 搜索已知陷阱模式：
     grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
     → 命中说明有 cascader 没设置 emitPath，可能有问题
  ↓
4. Phase 4 用 curl 做 POST+GET 往返验证（参考 §数据链路完整性）
```

### 写完代码后自查命令（补充）

```bash
# 检查 el-cascader 是否设置了 emitPath
grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
# 命中 → 可能 v-model 绑定类型与后端不一致，需确认
```

## 错误处理

- API 返回 `ok: false` → 显示 `ElMessage.error(error)`
- 网络错误 → 统一在 api-client.js 拦截器中处理
- 401 → 自动刷新 token，失败则跳转登录

## 打包构建

- Vite proxy：`/api` `/ws` → `:8765`（Django），`/agentscope` `/agentscope-stream` → `:8000`
- Element Plus 按需引入：`unplugin-vue-components`
- 分包策略：`manualChunks` 按 vendor 拆分

## 代码变更后必检

每次修改 `.vue` / `.js` 文件后，必须**逐级验证**，不通过不得提交：

### 第一级：语法编译

```bash
cd frontend && npx vite build --mode development 2>&1 | tail -10
```

| 错误 | 根因 | 修复方向 |
|------|------|---------|
| `Unexpected token` + 指向 `</script>` | 括号/花括号未闭合（`{}` `()` `[]` 不配对） | 检查报错行之前的函数/对象括号配对 |
| `is not defined` | 缺少 import 或变量未声明 | 检查引用路径和变量名拼写 |
| `Cannot read properties of undefined` | API 返回结构变化 | 检查 `data.ok` 判断和字段路径 |

### 第二级：运行时加载

```bash
# 确认 Vite dev server 正常响应模块请求（无 500）
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/ai-assistant/index.vue
```

| 错误 | 根因 | 修复方向 |
|------|------|---------|
| HTTP 500 | Vue SFC 编译失败 | 运行 `npx vite build` 看完整错误栈 |
| `Failed to fetch dynamically imported module` | 懒加载模块编译错误 | 同上 |
| `[ElOnlyChild] no valid child node found` | Element Plus 组件缺少子元素 | 检查 `el-*` 标签是否有内容或 `v-if` 条件 |

### 第三级：浏览器功能

修改涉及以下模块时必须打开浏览器验证：

| 改动的模块 | 验证动作 |
|-----------|---------|
| `router.js` / `routes.js` | 点击侧边栏每个菜单项 → 确认页面加载（非白屏） |
| `api-client.js` | 登录 → 刷新页面 → 确认不跳回登录页 |
| `ChatView.vue` / SSE 相关 | 发送一条消息 → 确认流式回复正常 |
| `LoginView.vue` | 登录 → 确认跳转 dashboard |
| `AppSidebar.vue` | 确认 7 个模块菜单项完整显示 |

> **核心规则**：代码变更后，编译通过 ≠ 功能正常。语法错误会导致 Vite 返回 500 给浏览器，`动态 import` 失败会导致整个模块白屏。这两项必须在提交前清零。

## 前端数据完整性规则

### 数据来源铁律

```
所有页面展示的数据，必须来自 API 调用数据库。禁止以下行为：
  ❌ ref([{...硬编码数据...}])  // 假数据填充
  ❌ data.value = data.value.concat([...])  // 追加假数据
  ❌ computed 中拼接硬编码对象
  ✅ 数据只从 API 响应赋值：items.value = response.data.items
```

### 数据链路完整性

每次编辑 Vue 文件后，确认数据链路未断裂：

```
浏览器 → Vue 模块加载 (200) → <script setup> 执行 (无语法错)
    → onMounted → api.js → HTTP 请求 → Django view
    → ORM 查询 → DB 返回 → JSON 响应 → .then(data.ok)
    → items.value = data.xxx → 模板渲染
```

**每个环节的常见断裂点**：

| 断裂点 | 现象 | 排查命令 |
|--------|------|---------|
| 模块 500 | 页面白屏，Console: `Failed to fetch dynamically imported module` | `curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/xxx/index.vue` |
| 语法错误 | 同上 | `npx vite build 2>&1 \| grep error` |
| API 返回 401 | 数据为空，跳转登录页 | Network 面板看 `/api/` 请求 |
| API 路径拼写错误 | 404 + `data` 为 undefined | 检查 api.js 中的 URL 路径 |
| `data.ok` 解构错误 | 有响应但页面无数据 | 检查 API 响应格式 `{ok, data, items?}` |
| 字段名不匹配 | 列表为空 | 检查 `response.data.xxx` 与 `store.items` 赋值字段名一致 |
| **组件 v-model 类型 ≠ 后端期望类型** 🔴 | **保存成功但数据错 / 编辑回显不显示** | **对比前端组件 v-model 输出类型 vs 后端字段类型。常见：el-cascader 默认输出路径数组，后端期望单个 ID** |

### 编辑后快速自检

```bash
# 1. 检查模块是否正常加载（期望 200）
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/ai-assistant/index.vue

# 2. 检查对应的 API 是否返回数据（期望 ok:true + 有数据）
TOKEN=$(curl -s -X POST http://localhost:8765/api/ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<user>","password":"<pass>"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8765/api/ai/agents -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -20
```

### 禁止的"假数据"模式

编辑代码时，**绝对禁止**以下写法（它们会让数据显示但来源不是数据库）：

```js
// ❌ 禁止：硬编码假数据作为初始值
const agents = ref([{ id: 1, name: '测试助手', status: 'active' }])

// ❌ 禁止：catch 中填充假数据
try { ... } catch { agents.value = [{ id: 1, name: '默认' }] }  // 错误！应保持空数组

// ❌ 禁止：computed 中拼接假数据
const list = computed(() => [...agents.value, { id: 0, name: '新增项' }])

// ✅ 正确：初始值为空，catch 保持空，数据只来自 API
const agents = ref([])
try { const { data } = await client.get('/ai/agents'); if (data.ok) agents.value = data.agents }
catch { /* 静默失败，agents 保持 [] */ }

// ❌ 禁止：写操作 catch 静默吞错误
try { await client.post(`/api/ai/agents/${id}/delete`) } catch (_) {}
// ✅ 正确：写操作 catch 必须报错 + 立即从本地列表移除（乐观更新）或重新加载
try {
  await client.post(`/api/ai/agents/${id}/delete`)
  items.value = items.value.filter(i => i.id !== id)  // 立即更新 UI
} catch { ElMessage.error('删除失败，请检查网络') }
```

### 写操作静默吞错检查

搜索项目中所有 `catch (_)` `catch{}` `catch () {}`，分两类处理：

| 场景 | 正确处理 |
|------|---------|
| **写操作**（delete/create/update） | catch 必须 `ElMessage.error()` + 乐观更新或重新加载。禁止静默吞错 |
| **读操作**（list/get/query） | catch 可静默，但必须保证数据为空态（不残留旧数据） |

## 🔴 页面区域空白/不可见排查流程

> **触发条件**: 用户反馈"某区域没有内容"、"右侧空白"、"XX 不显示"等视觉缺失问题。
> **来源**: 2026-07-06 case-manager 右侧空白排查耗时过长，根因是 CSS 而非代码逻辑。

### 强制两步排查（不可跳过）

```
用户反馈"XX 区域空白/没有内容"
  ↓
第一步: DevTools Elements → 搜关键 class/文字 → 确认 DOM 中是否存在目标元素？
  ├── 不存在 → 模板/JS 问题 → 检查 v-if 条件、组件是否注册、编译是否报错
  └── 存在 → 第二步
        ↓
第二步: DevTools → 选中目标元素 → Computed 面板 → 逐项检查:
  ├── display: none? → v-if/v-show 或 CSS 隐藏
  ├── width/height: 0? → 内容为空或 CSS 未撑开
  ├── opacity: 0? → 动画或过渡隐藏
  ├── visibility: hidden? → CSS 显式隐藏
  ├── position: absolute + 负坐标? → 被定位到视口外
  ├── overflow: hidden + 子元素被裁剪?
  └── ⚠️ flex-direction 方向是否与预期一致?
       └── 全局 CSS 继承冲突是最隐蔽的坑
           → 必须检查 computed styles 中的 flex-direction 来源
           → 特别注意 scoped 样式没有覆盖全局样式的情况
```

### 关键原则

1. **优先用浏览器 DevTools，不要纯代码分析** — curl/grep/vite build 全部通过 ≠ 渲染没问题。CSS 问题不会被任何 CLI 工具捕获
2. **全局样式冲突是盲区** — scoped 组件内看代码完全正常，但全局 `style.css` 或父级 CSS 可能覆盖关键属性。必须看浏览器 computed styles 面板确认**最终生效值**及其**来源文件**
3. **flex-direction 是最常见的布局杀手** — `.doc-body` 这种全局容器设了 `flex-direction: column`，子组件的 `display: flex` 如果没有显式设 `flex-direction: row`，就会继承 column 方向，导致左右布局变成上下布局
4. **不要反复重写模板** — 如果 vite build 通过了且 API 返回数据，大概率不是模板结构问题。先排除 CSS 再改代码

### 本次教训速查

| 症状 | 排查方向错误（❌） | 正确排查（✅） |
|------|-------------------|--------------|
| 右侧看不到内容 | 数 div 闭合、改 v-if/v-else 链、重写模板 | DevTools computed → `flex-direction: column` 来自全局 `.doc-body` |
| 编译/API/模块全部正常 | 反复 curl + grep 验证已知结论 | 打开浏览器看实际渲染 |
| 怀疑组件 API 用错 | 逐行对照 animal-island-ui.md | 先看 Elements 面板确认组件是否在 DOM 中 |
```
