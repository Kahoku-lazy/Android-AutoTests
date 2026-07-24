# Frontend Rules — Android-AutoTests

> AI 前端开发的行为约束。结构/模式/配置等可从代码中读出的信息不再记录，本文只放 AI 无法通过读代码获取的约束和陷阱。

---

## 架构红线

1. **按业务域拆分** — 新代码放 `modules/{domain}/`，删一个模块 = 删一个目录
2. **模块自治** — 模块间只通过 `router.push`、`shared/components/`、`event-bus` 交互，不互相 import 业务逻辑
3. **调用链单向** — `components/ → composables/ → api.js`，上层不反向引用下层
4. **三层职责**：
   - `components/` — 只渲染 + emit，❌ 禁止直接调 axios/apiClient
   - `composables/` — 状态 + 逻辑 + API，❌ 禁止操作 DOM
   - `api.js` — 纯 HTTP，❌ 禁止处理业务状态

## 代码约束

### 组件拆分信号（出现任一就该拆）
| 信号 | 阈值 |
|------|------|
| ref/reactive | > 6 个 |
| 模板行数 | > 150 行 |
| 文件总行数 | > 300 行（硬上限 500） |

### 命名
文件 `PascalCase.vue`，模板 `kebab-case`，JS `camelCase`，JSON `snake_case`

### 数据
- ❌ 组件同时从 props 和 onMounted 请求同一份数据
- ❌ 硬编码假数据 `ref([{ id: 1, name: '测试' }])`
- ❌ 写操作静默吞错 `try { await deleteX(id) } catch (_) {}`
- 状态管理：能用 `ref` 不用 Pinia，能用 composable 不用 event bus

## 样式约束

1. **颜色/圆角/阴影/字体从 `tokens.css` 取** — ❌ 组件 scoped 中硬编码色值
2. **覆盖 Element Plus 用 `:deep()` + `--el-*` 变量** — ❌ 禁止封装薄 wrapper
3. 当前平台主题 → `frontend/THEME.md`

## Element Plus 陷阱

**el-cascader**: `emitPath` 默认 `true` → v-model 绑定路径数组 `[1,5]`，后端期望单个 ID。必须显式 `emitPath: false`。

使用不熟悉的复杂组件（el-cascader/el-tree-select/el-transfer）时：查文档确认默认值 → 确认 v-model 类型与后端一致 → `grep` 已知陷阱 → curl 往返验证。

## 页面空白排查

全局 CSS 继承是最隐蔽的坑 — scoped 内代码正常，但 `style.css` 覆盖了关键属性。看 DevTools Computed 面板的**最终值和来源文件**。尤其 `flex-direction` 被全局继承为 column 时。

## 质量门禁

```bash
# 编译
cd frontend && npx vite build --mode development 2>&1 | tail -10

# 样式自查
grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" \
  frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"

# el-cascader emitPath 陷阱
grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
```

### 浏览器验证（改以下文件必须）
| 改动 | 验证 |
|------|------|
| router/routes | 点侧边栏每个菜单 → 确认加载 |
| api-client | 登录 → 刷新 → 不跳回登录页 |
| ChatView/SSE | 发一条消息 → 流式回复正常 |
| LoginView | 登录 → 跳转 dashboard |
| AppSidebar | 7 个菜单项完整 |

## 自评

1. 10 分钟能加一个 CRUD 页面？→ 模式一致
2. 改一个颜色全局生效？→ 令牌驱动，无硬编码色值
3. 删一个模块不影响其他？→ 无跨模块网状 import
