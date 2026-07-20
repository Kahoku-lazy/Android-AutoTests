# Frontend Rules — Android-AutoTests

> AI 前端开发的行为约束。参考数据（令牌值、CSS class、模块颜色）去源文件查，本文只放红线。

---

## 一、架构

### 三条原则

1. **按业务域拆分，不按技术类型拆分** — 代码放 `modules/{domain}/`，删一个模块 = 删一个目录
2. **模块自治** — 每个模块路由/API/状态/组件内聚。模块间只通过 `router.push`（跳转）、`shared/components/`（共享组件）、`event-bus`（通知）交互，不互相 import
3. **调用链单向不可逆** — `components/ → composables/ → api.js`，上层绝不反向引用下层

### 三层职责与红线

```
components/   → 只做渲染 + emit 事件          ❌ 禁止直接调 axios / apiClient
composables/  → 状态(ref) + 业务逻辑 + API调用  ❌ 禁止操作 DOM
api.js        → 纯 HTTP 请求封装               ❌ 禁止处理业务状态 / import composable
```

### 路由

- 子路由定义在模块 `routes.js`，`router.js` 只做 `routes.push(...)` 汇总
- 守卫只做认证，不写业务逻辑；全部懒加载 `() => import(...)`

---

## 二、代码

### 组件拆分信号（出现任一就该拆）

| 信号 | 阈值 |
|------|------|
| ref/reactive | > 6 个 |
| 模板行数 | > 150 行 |
| 存在独立视觉区域 | 面板 / 列表 / 表单 |
| 文件总行数 | > 300 行（硬上限 500） |

### composable 模式（非渲染逻辑必须进 composable）

```js
// ✅ composables/useAgents.js
export function useAgents() {
  const agents = ref([]); const loading = ref(false); const error = ref(null)
  async function fetch() { loading.value = true; try { /* API */ } catch (e) { error.value = e } finally { loading.value = false } }
  return { agents, loading, error, fetch }
}

// ❌ 组件内直接调 API
onMounted(async () => { const { data } = await apiClient.get('/ai/agents'); agents.value = data.agents })
```

### 命名

文件 `PascalCase.vue`，模板 `kebab-case`，JS 变量 `camelCase`，JSON 字段 `snake_case`，CSS class `kebab-case`

---

## 三、样式

### 核心规则

1. **所有视觉参数从 `tokens.css` 取** — 颜色/圆角/阴影/字体。❌ 组件 scoped 中硬编码色值
2. **覆盖 Element Plus 用 `--el-*` 变量**（已集中在 `tokens.css`），❌ 禁止封装薄 wrapper（如把 `<el-button>` 包一层 `<MyButton>`）
3. **scoped 不够用 `:deep()` 穿透**，❌ 不为一次性需求加全局选择器
4. **只用 Element Plus**，不引入第三方 UI 主题库

> 查具体令牌值/模块颜色 → Read `shared/styles/tokens.css`。查全局 CSS class → grep `style.css`。

---

## 四、数据

### 单一数据流向

```
API 响应 → composable/ref → 组件渲染
用户操作 → composable 函数 → API 调用 → 更新 ref → 重新渲染
```

❌ 组件同时从 props 和 onMounted 请求同一份数据。

### 列表组件必须覆盖三态

```html
<div v-if="loading">加载中</div>
<div v-else-if="error">错误 + 重试</div>
<div v-else-if="!items.length">空态</div>
<div v-else>正常数据</div>
```

### 状态管理选型

能用 `ref` 不用 Pinia，能用 composable 不用 event bus。event bus 只做通知不传数据。

### 数据真实性

```
❌ ref([{ id: 1, name: '测试' }])          // 硬编码假数据
❌ computed 中拼接硬编码对象
✅ items.value = response.data.items        // 只从 API 赋值
```

### 写操作不可静默吞错

```js
// ❌ try { await deleteX(id) } catch (_) {}
// ✅
try { await deleteX(id); items.value = items.value.filter(i => i.id !== id) }
catch { ElMessage.error('删除失败') }
```

### 错误处理三层

| 层 | 位置 | 处理 |
|----|------|------|
| 网络 | `api-client.js` 拦截器 | 401/超时/断网 |
| 业务 | composable | API `ok:false` → ElMessage.error |
| 视图 | 组件模板 | 三态 v-if 切换 |

---

## 五、质量门禁（提交前必过）

### 第一级：编译

```bash
cd frontend && npx vite build --mode development 2>&1 | tail -10
```

### 第二级：模块加载

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/{name}/index.vue
# 期望 200
```

### 第三级：浏览器验证（改以下文件必须）

| 改动 | 验证 |
|------|------|
| router/routes | 点侧边栏每个菜单 → 确认加载 |
| api-client | 登录 → 刷新 → 不跳回登录页 |
| ChatView/SSE | 发一条消息 → 流式回复正常 |
| LoginView | 登录 → 跳转 dashboard |
| AppSidebar | 7 个菜单项完整 |

### 样式自查

```bash
# 模块内硬编码色值（应尽量少）
grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" \
  frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"

# el-cascader emitPath 陷阱
grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
```

---

## 六、Element Plus 默认值陷阱

**el-cascader**：`emitPath` 默认 `true` → v-model 绑定路径数组 `[1,5]`，后端期望单个 ID `5`。必须显式 `emitPath: false`。

使用不熟悉的复杂组件（el-cascader/el-tree-select/el-transfer）时：
1. 查文档确认 emitPath/value-key/node-key 默认值
2. 确认 v-model 类型与后端一致
3. `grep` 搜索已知陷阱模式
4. 用 curl 做 POST+GET 往返验证

---

## 七、页面空白排查

先 DevTools 后代码分析：

1. **Elements 面板** → 目标元素在 DOM 中？不在 → 查 v-if/编译；在 → 下一步
2. **Computed 面板** → 逐项查：`display: none`? `width/height: 0`? `opacity: 0`? `overflow: hidden`? **⚠️ `flex-direction` 被全局 CSS 继承为 column?**

> 全局 CSS 继承是最隐蔽的坑 — scoped 内代码正常，但全局 style.css 覆盖了关键属性。看 computed styles 的**最终值和来源文件**。

---

## 八、构建

- Vite proxy：`/api` `/ws` → `:8765`，`/agentscope` → `:8000`
- Element Plus 按需引入：`unplugin-vue-components`
- AI 对话 SSE：独立 client 指向 `:8000`

---

## 九、自评

每个改动后：

1. 10 分钟能加一个 CRUD 页面？→ 模式一致
2. 改一个颜色全局生效？→ 令牌驱动，无硬编码色值
3. 删一个模块不影响其他？→ 无跨模块网状 import
