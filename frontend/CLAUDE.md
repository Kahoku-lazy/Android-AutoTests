# Frontend CLAUDE.md — AI 约束

> 工作于 `frontend/` 时必须遵守。细则与反例见 `dev_docs/项目笔记/前端claude笔记.md`；关单自检用 skill `vue-frontend-check`。

**口诀**：展示不碰网，流程不做校验，类型跟着实现走，图标进工厂，共享等第二人，重构先问值不值。  
**完成定义**：构建通过 ≠ 完成；必须在真实页面验证。

---

## 0. 动手前

1. 需求模糊 → 列 3～5 种理解让用户选，禁止默默挑一种执行。
2. 先读目标 `.vue` 的 **template + script + style 三块**；改 CSS 前提取全部 class，禁止凭印象重写漏 inner class。
3. 查：`DESIGN_SYSTEM.md`（色/组件/布局）、`.claude/rules/frontend.md`、模块专属约束（见笔记 §0️⃣）。
4. 判边界：纯 UI→①；API/字段→②；AI SSE→③；跨界按序做。

---

## 1. 职责与红线

| 层 | 只做 | 严禁 |
|----|------|------|
| `.vue` 展示 | 渲染 / v-model / emit / testid | fetch、axios、复杂业务、校验编排 |
| `*.logic.ts` 编排 | 组合 composable、提交前校验、清表单 | 直连 HTTP |
| 流程 composable | API → 副作用 → 跳转 | 表单校验、弹校验 toast |
| 校验 composable | `errors` / `canSubmit` | 发请求 |

- 组件**必须**走模块 `api.js` / `api/*.ts`，禁止组件内 axios/fetch。
- 业务 HTTP 经 **djangoClient → `/api/...` DRF**；逻辑层接口与后端协议（urls/Serializer/契约）一致。
- API/认证函数不做表单校验；`ElMessage.warning` 在 `handleXxx` 调用方。
- 公开 TS 签名与实现参数**同改**；单测随职责迁移。
- `.vue` > 500 行：先拆样式，再拆逻辑。
- JSON：前端 camelCase，HTTP snake_case；响应 `{status, data|message}`。
- 写操作禁止空 `catch` 静默吞错。
- `dashboard` 只读，禁止写操作。
- 新图标：`shared/icons/index.ts` 的 `makeIcon`；禁止无必要的 `IconXxx.vue`。
- 抽 `@/shared`：等第二个真实消费方；单处不提前抽象。
- 状态：`ref` → composable → Pinia（不可跳级）；新模块默认不用 Pinia（workflow 除外）。
- 必用共享件：`ErrorState` / `EmptyState` / `AppCard` / `AppTable` 等（见笔记共享组件表）；禁止同场景自建。

**默认拒绝的重构**：动态 `component :is` 硬合并不同 props 卡片；整表 `reactive` 连锁大改；首屏图 `lazy`；1～2 处路径就抽常量；无行为变化的间接层。  
登录暂缓项与触发条件 → `dev_docs/项目笔记/前端claude笔记.md` §编码行为规范.8。

---

## 2. 模板 / 样式 / 布局（每次改 UI 必做）

1. **布局裁剪（P0）**：真实页面缩小窗口可滚；侧栏展开不挤爆；表格区 `flex: 1 1 0; min-height: 0; overflow-y: auto`；外层禁止乱加 `overflow:hidden`。
2. **Dialog/Drawer**：长内容可滚，底部按钮可达。
3. **字段显示完整性**：有数据来源与空值占位；列表列 / Card / detail 关键字段不漏。
4. **表格长文本列**：`show-overflow-tooltip` 或等价。
5. **视图模式切换**（卡片↔表格等）后布局仍可用。
6. 字号/颜色走 token；静态样式进 class。
7. 三态 + **saving**；错误文案对用户友好，不暴露技术术语。
8. **多视图互斥**；**composable 入参**约定一致。
9. **保存**：信封解包；strip UI-only；校验≥Schema。
10. **展示组件**：薄组件；危险操作确认；编辑锁只读禁用；子面板只改自己 v-model 块。
11. 纯展示子组件：不为「配套重构」而改；只改契约/图标/bug/a11y。

---

## 3. 协议要点

**HTTP / DRF**：组件 emit → composable → 模块 `api` → `djangoClient`（统一客户端）→ `/api/...` **DRF**。  
- 逻辑层接口须与后端协议一致（路径、方法、字段、信封）；对照 `urls.py`、Serializer、`VUE_API_CONTRACT.md`。  
- 禁止组件/composable 旁路直连后端端口或另起非约定 HTTP 客户端。  
**WS**：`wsUrl('/ws/...')` 经 Vite 代理，禁止直连后端端口。test-runner 六种事件 type 不可漏。  
**报告下载**：FileResponse 用 `fetch().text()`，不用 JSON `api()`。  
**SSE（AI）**：按事件类型渲染；停止生成须保留已生成内容；ThinkingBlock / ToolCallCard 折叠规则见笔记 §③。

---

## 4. 关单前最短清单

```
[ ] 真实页面验证；布局可滚；Dialog 按钮可达；关键字段可见
[ ] 三态/saving；错误文案无技术术语
[ ] 多视图互斥、父子选中/清空同步（若涉及）
[ ] 展示层：危险确认、锁态禁用、分块面板/步骤字段对齐（若改 components）
[ ] 保存：信封解包、DTO 清洗、校验≥Schema（若涉及编辑器）
[ ] 逻辑层 API 与后端 DRF 协议一致；经 djangoClient/`api` 通道（若涉及接口）
[ ] 类型与实现一致；testid 未无故改名
[ ] diff 每行可追溯到用户需求
```

详细门禁 → skill `vue-frontend-check`。完整决策树与模块踩坑 → `dev_docs/项目笔记/前端claude笔记.md`。
