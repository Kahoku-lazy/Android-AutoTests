# SPEC: case-manager 前端代码检查方案

> **范围**：`frontend/src/modules/case-manager/`
> **目标**：按「先分模块、后全链路」执行可勾选的代码检查，产出缺陷清单与修复优先级，而不是顺手重构。
> **创建日期**：2026-08-11
> **状态**：待执行
> **关联**：`frontend/CLAUDE.md`（模版层必查布局裁剪 + 字段完整性）、`.claude/rules/api-conventions.md`、`apps/case_manager/schema_config.py`

---

## 0. 检查原则

| # | 原则 | 说明 |
|---|------|------|
| 1 | 分层只查本层 | 每层有明确「该查 / 不该查」；跨层问题记到全链路阶段 |
| 2 | 证据优先 | 每条缺陷标注：文件路径、现象、根因假设、验证方式 |
| 3 | 不扩 scope | 发现异味可记 🟡，不「顺手」大改相邻代码 |
| 4 | 契约同源 | JSON 字段 `snake_case`；TS/Vue 变量 `camelCase`；请求体发出去必须是 snake_case |
| 5 | 用户可读错误 | 禁止把堆栈、HTTP 术语、内部字段名直接甩给用户 |

### 严重度

| 标记 | 含义 | 处理 |
|------|------|------|
| 🔴 | 功能错误 / 数据丢失 / 契约断裂 | 必须修 |
| 🟠 | 竞态、泄漏、易踩坑、缺状态反馈 | 优先修 |
| 🟡 | 味道、死代码、命名漂移、一致性 | 可记债 |

### 分层总览

```
routes / index / CaseEditor     ← 编排入口
        ↓
components/                     ← 看得见的对不对（布局、字段、交互）
        ↓
composables/                    ← 状态与流程对不对（副作用、锁、WS）
        ↓
api/ + api.ts                   ← 请求对不对（URL、方法、字段映射）
        ↓
types/                          ← 契约对不对（与 schema_config.py 同源）
```

**执行顺序（强制）**：M1 types → M2 api → M3 composables → M4 components → M5 根模块 → M6 全链路。

---

## M1. `types/` — 契约层

**对象**：`types/api-config.ts`（当前几乎仅此文件）  
**对照真相源**：`apps/case_manager/schema_config.py`

### 该查

- [ ] multi 顶层：`case_info` / `steps` / `test_data` / `validation` 与 Schema `required` 一致
- [ ] single 顶层：`meta` / `request` / `cases` 与 `SINGLE_API_SCHEMA` 一致
- [ ] 字段名全部 snake_case；枚举（`method`、`auth.type`）与后端一致
- [ ] 可空语义：`null` vs 缺省 vs `[]` / `{}` 与 Schema 一致
- [ ] `isSingleFormat` 探测逻辑与后端格式探测一致（`meta`+`cases` vs `case_info`）
- [ ] 默认工厂：`defaultApiConfigJson` / `defaultApiStep` / `defaultSingleApiConfig` 产出物能否通过后端校验
- [ ] 仅前端类型（如 `ResolvedVariable`）是否标注「不入库」
- [ ] 消费者（composable/组件）是否引用本文件类型，有无本地私自加字段绕过契约

### 不该查

布局、HTTP 路径、ElMessage、Vue 生命周期。

### 完整度备注

- [ ] 记录：UI / Web / Storage 用例结构是否仍无 types（标为「无契约 / 易漂移」，不强制本轮补齐）

### 通过标准

与 `schema_config.py` 字段级可对照；默认值可被后端 validate 接受；无「UI 有、类型无」的影子字段。

---

## M2. `api/` + `api.ts` — HTTP 封装层

**对象**：

| 文件 | 职责 |
|------|------|
| `api/directories.ts` | 目录 CRUD / 批量移动 / 权限 |
| `api/uiAutomation.ts` | UI 用例 + 锁/可见性 + devices/elements/runner helpers |
| `api/apiTesting.ts` | API 用例 CRUD / batch |
| `api/storage.ts` | Storage 用例 CRUD / batch |
| `api/webAutomation.ts` | Web 用例 CRUD / batch |
| `api.ts` | 兼容 re-export + `fetchStepTypes` |

**对照真相源**：`apps/case_manager` 的 `urls.py` / views

### 该查

#### 2.1 职责边界

- [ ] 仅路径、方法、请求体映射；无业务分支、无轮询、无 UI 文案
- [ ] 组件/composables 不直接 `import client` 发业务请求（允许 `formatApiError`）
- [ ] `api.ts` 只做 facade；新增端点落在 `api/*.ts` 后再导出

#### 2.2 契约对齐

- [ ] 路径、HTTP 方法与后端一致
- [ ] 请求 JSON / query 为 snake_case（`directory_id`、`parent_id`、`target_directory_id`…）
- [ ] 函数参数 camelCase → 发出去已转换
- [ ] query 拼装：`null`/`undefined` 不产生脏参数

#### 2.3 完整性与对称性

- [ ] 四类用例 list/get/save/delete/batch 对称
- [ ] 锁、可见性、step-types、跨模块 helpers 集中且可发现
- [ ] `api.ts` re-export 无遗漏、无错误路径（注意 `.js` 后缀与实际文件一致）
- [ ] `api.ts` 中残留的直接 `client` 调用（如 `fetchStepTypes`）是否应下沉到 `api/` 子文件（记 🟡 即可）

### 不该查

页面布局、ORM、权限装饰器实现细节。

### 通过标准

后端已暴露的 case-manager 端点均可经本层调用；字段映射正确；无组件直连 client。

---

## M3. `composables/` — 状态与流程层

**对象**（按类检查）：

| 类 | 文件 |
|----|------|
| 数据/协议 | `useApiConfigJson`、`useJsonSchemaEditor` |
| 协作/生命周期 | `useEditLock`、`useCaseEditingSocket`、`useDirtyGuard` |
| UI 交互 | `useContextMenu`、`useTreeDragDrop`、`useBatchSelect`、`useDirectoryDialog`、`useDirectoryCascader` |
| 编辑辅助 | `useStepFields`、`useStepDragDrop`、`useStepRunner`、`useDebugDevice`、`useElementLibrary` |
| 杂项 | `useCaseManager`（常量/工具是否该迁出） |

### 该查

#### 3.1 职责边界

- [ ] HTTP 只走 `../api`；无手写 URL
- [ ] 无大段模板职责；单个 composable 不膨胀成整页上帝对象
- [ ] 命名 `useXxx`，文件名与主导出一致

#### 3.2 副作用清理（必查）

- [ ] `addEventListener` ↔ `removeEventListener`（`useDirtyGuard`、`useContextMenu`）
- [ ] WebSocket / reconnect timer ↔ `disconnect` + `onUnmounted`（`useCaseEditingSocket`）
- [ ] 持锁离开是否 `releaseEditLock`
- [ ] `watch` 内定时器/连接在重跑与卸载时清理

#### 3.3 响应信封与错误

- [ ] 正确读 `data.status` / `data.message` / `data.definition`（禁止把 Axios 信封当 definition）
- [ ] 用户错误走 `formatApiError` 或业务话术

#### 3.4 业务场景（按文件）

- [ ] **锁**：创建者锁 / 他人编辑 / 423 / 强制抢锁
- [ ] **脏检查**：保存成功跳过守卫；`beforeunload` + 路由离开都覆盖
- [ ] **WS**：`new` 跳过；`caseId` 变化重连；token 缺失安全退出；刷新不覆盖未保存编辑（或有确认）
- [ ] **config_json**：single/multi 切换清脏数据；`meta`/目录等表字段不误写入 `config_json`
- [ ] **拖拽/批量移动**：禁移根、空选、部分失败 `errors[]`

### 不该查

布局裁剪、`urls.py` 路径字面量（只确认调用了正确 api 函数）。

### 通过标准

关键副作用可清理；主流程分支有覆盖；无信封解构错误；无直连 client。

---

## M4. `components/` — 模板/展示层

**对象**：

| 区域 | 代表 |
|------|------|
| 共用 | `DirectoryTree`、`CaseList`、`CaseCard`、`StepEditor`、`StepViewer`、`WatcherPanel` |
| 类型入口 | `ui/*`、`api/*`、`storage/*`、`web/*` 的 List/Editor |
| API 子面板 | `CaseInfoPanel`、`StepListPanel`、`TestDataPanel`、`ValidationPanel`、`ApiStepCard` |

> `frontend/CLAUDE.md`：**模版层每次修改必须做布局裁剪检测 + 字段显示完整性校验。**

### 该查

#### 4.1 布局裁剪（必查）

- [ ] 表格列长文本：`show-overflow-tooltip` 或等价反馈
- [ ] 目录名、标题、URL、路径截断可见
- [ ] 窄屏/侧栏展开不横向撑爆；Dialog 可滚动、主按钮不被挡
- [ ] 卡片/表格视图切换后仍可用

#### 4.2 字段显示完整性（必查）

- [ ] 列表列、详情、编辑表单覆盖关键字段（优先级、目录、更新时间、锁定/只读等）
- [ ] 空值有占位，不「像丢了」
- [ ] API multi：四面板与 `config_json` 对齐；single：`meta`/`request`/`cases` 有明确展示策略（只读也要说清）
- [ ] `StepEditor`：按步骤类型字段齐全、必填标记正确

#### 4.3 职责与交互

- [ ] 薄组件：重逻辑在 composable；不 `import client` 发业务请求
- [ ] 四类 `*CaseList` 尽量复用 `CaseList`，差异用 props/slots，避免复制漂移
- [ ] loading / saving / error / 空态齐全
- [ ] 危险操作有确认；只读态控件禁用
- [ ] props/emits 约定一致：`treeData`、`activeDirectoryId`、`activeCaseId`、`refresh-tree`、`clear-case`、`update:modelValue`

### 不该查

Schema 字面量对齐（属 M1）、锁/WS 实现细节（属 M3，只确认「接上且时机对」）。

### 通过标准

关键列表/编辑页：无静默空白字段；长文本可感知截断；主交互有状态反馈。

---

## M5. 根模块 — 编排与入口

**对象**：`index.vue`、`CaseEditor.vue`、`routes.ts`、`step-utils.ts`、（可选）模块级样式/逻辑文件

### 5.1 `routes.ts`

- [ ] 四类用例 new/edit 路由完整，`meta.title` 正确
- [ ] 组件指向正确（⚠️ 当前 `storage` new/edit 指向 `ApiCaseEditor.vue` — 确认是有意复用还是路由错误）
- [ ] 懒加载路径可解析；无死路由

### 5.2 `index.vue`（工作台）

- [ ] Tab ↔ `case_type` 映射正确：`ui_automation` / `web_automation` / `storage` / `api_testing`
- [ ] 每 Tab 独立 `treeCache`；切 Tab 清选择态
- [ ] 树选目录 / 选用例 ↔ 列表 `activeDirectoryId` / `activeCaseId` 同步
- [ ] 「返回列表」是否同时清本地选中与父级 `activeCaseId`（防树高亮残存、watch 不触发）
- [ ] `loadTree` 错误有 `ErrorState`/可读提示；定时刷新若存在则无竞态覆盖

### 5.3 `CaseEditor.vue`（UI 编辑器）

- [ ] 加载：使用 `data.definition`，失败有提示（禁静默空表单）
- [ ] 保存：409/423 等冲突有处理；成功后脏标记清除
- [ ] 组合调用：`useEditLock` / `useDirtyGuard` / 步骤相关 composable 时机正确
- [ ] 卸载释放锁、拆除 beforeunload

### 5.4 `step-utils.ts`

- [ ] 仅显示摘要/图标/别名归一；步骤类型定义仍以后端 `step-types` 为准
- [ ] `_TYPE_ALIAS` 过渡别名是否仍需要；死别名记 🟡
- [ ] `FIELD_LABELS` 与 `StepEditor`/`useStepFields` 使用一致

### 通过标准

入口路由可达；树-列表-编辑器选择态闭环；UI 编辑器加载/保存/锁无静默失败。

---

## M6. 完整链路检查（最后执行）

> 前置：M1–M5 缺陷已登记。全链路只验证「串起来是否正确」，不回头改检查标准。

### 6.1 数据流闭环（四类用例各走一遍）

对 **ui / web / api / storage** 分别验证：

```
目录树加载 → 选目录 → 列表过滤 → 新建
  → 编辑必填字段 → 保存
  → 列表可见 → 再打开加载完整
  → 编辑修改 → 保存 → 刷新仍在
  → 删除 → 树与列表同步
```

检查点：

- [ ] 保存请求体字段与后端期望一致（尤其 `config_json`、`directory_id`）
- [ ] 加载不丢字段（description/precondition/steps/锁信息）
- [ ] 列表与树节点计数/名称一致
- [ ] 错误路径：校验失败 400、无权限、网络错误 — 用户能看懂

### 6.2 API config_json 专项链路

- [ ] 新建 multi → 填 case_info + 至少 1 step（含 url）→ 保存通过 Schema
- [ ] 再打开：format=`multi`，四面板数据回填
- [ ] 若存在 single 用例：探测为 single；展示策略符合设计（只读/可编）
- [ ] 前端校验规则 ≥ 后端硬约束的关键项（title、steps 非空、url、extract name/path）— 避免「前端过、后端 400」
- [ ] 表级字段（priority、directory_id、visibility…）与 `config_json` 分离，save 不串写

### 6.3 协作与并发链路

- [ ] A 打开编辑持锁 → B 打开只读 → A 释放 → B 可抢锁/刷新
- [ ] 强制抢锁后原编辑方状态可理解
- [ ] WS `case_updated`：有未保存修改时不静默覆盖（确认或忽略策略明确）
- [ ] 离开页：脏检查弹窗；持锁释放

### 6.4 目录与批量操作链路

- [ ] 创建/重命名/删除目录（权限不足时有提示）
- [ ] 拖拽移动、批量移动：成功数 + `errors[]` 部分失败
- [ ] 不能移到非法目标（根级等）

### 6.5 跨模块调用链路（UI 调试）

- [ ] 选设备 → 连接 observe → 单步 `runStep` → 断开
- [ ] 元素库拉页/元素；失败有提示
- [ ] 调用均经 `api/uiAutomation` helpers，组件无直连

### 6.6 路由与深链

- [ ] `/cases` Tab 记忆、刷新后状态合理
- [ ] `/cases/:id/edit`、`/cases/api/:id/edit`、`/cases/web/:id/edit`、storage 对应路由可直达
- [ ] 浏览器返回键 + 脏检查协同

### 6.7 回归对照（已知风险清单）

以下来自既有排查笔记，全链路阶段必须复验是否仍存在：

| # | 风险 | 复验方式 |
|---|------|----------|
| 1 | 编辑页把 Axios 信封当 `definition` | 打开已有用例，确认表单非空 |
| 2 | WS 覆盖未保存编辑 | 编辑中触发 remote update |
| 3 | 返回列表不清 `activeCaseId` | 返回后再点同一用例 |
| 4 | 树选用例不更新 `activeDirectoryId` | 返回列表后目录上下文 |
| 5 | 前端校验弱于 Schema | 缺 url / 空 extract 点保存 |
| 6 | 表格列缺 overflow tooltip | 长标题列表 |
| 7 | WebCaseEditor 缺 409 处理 | 冲突保存 |
| 8 | storage 路由指向 ApiCaseEditor | 新建/编辑 storage 是否为预期产品行为 |

---

## 7. 输出物

每次检查执行结束，输出一份缺陷表（可写入 `dev_docs/项目笔记/` 或 PR 描述）：

| # | 严重度 | 模块(M1–M6) | 文件 | 现象 | 根因 | 建议修复 | 状态 |
|---|--------|-------------|------|------|------|----------|------|
| 1 | 🔴/🟠/🟡 | | | | | | open/fixed |

并附：

1. **模块结论**：M1–M5 各一段（通过 / 有条件通过 / 不通过）
2. **链路结论**：6.1–6.7 通过项与阻塞项
3. **不修清单**：明确选择不修的 🟡 及理由（避免下次重复争论）

---

## 8. 检查执行清单（总控）

```
阶段 A — 分模块（只读审查 + 点对点验证）
  [ ] M1 types
  [ ] M2 api + api.ts
  [ ] M3 composables
  [ ] M4 components
  [ ] M5 routes / index / CaseEditor / step-utils

阶段 B — 全链路（跑通 + 复验已知风险）
  [ ] 6.1 四类用例 CRUD 闭环
  [ ] 6.2 API config_json
  [ ] 6.3 锁 / WS / 脏检查
  [ ] 6.4 目录与批量
  [ ] 6.5 UI 调试跨模块
  [ ] 6.6 路由深链
  [ ] 6.7 已知风险复验

阶段 C — 收口
  [ ] 缺陷表定稿
  [ ] 🔴/🟠 建修复任务（或本轮直接修）
  [ ] 🟡 记技术债或不修说明
```

---

## 9. 一句话分层口令（审查时复述）

| 层 | 口令 |
|----|------|
| types | 契约是否同源 |
| api | 请求是否接对 |
| composables | 状态与副作用是否正确 |
| components | 看得见是否完整、是否裁切 |
| 根模块 | 入口与选择态是否闭环 |
| 全链路 | 串起来是否还能用 |
