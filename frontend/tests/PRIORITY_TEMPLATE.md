# 前端 Vitest 优先级模板（P0 / P1 / P2）

> 登录模块是首个按此模板落地的样板。后续复杂模块：**只测 P0+P1，默认不测 P2**。

## 怎么定优先级

| 级别 | 含义 | 是否写 Vitest |
|------|------|----------------|
| **P0** | 业务对错的核心：校验、状态机、API 编排、关键数据 | **必测** |
| **P1** | 编排独有行为、次要但可交互的 UI（弹层/提示卡） | **建议测** |
| **P2** | 整页拼装、装饰、真浏览器/真后端链路 | **不测 Vitest**（E2E 或人工） |

## 分层对照

```
P0  composable / 纯逻辑 / 主交互卡片 emit
P1  薄编排器（清表单等）/ Overlay / Prompt
P2  页面 index.vue 整页 mount / 插画动画 / 真登录跳转
E2E 真浏览器 + 真（或接近真）后端
```

## 新模块开测 Checklist

复制下面表格，填模块名后勾选。

### 模块：________

#### P0（必测）

- [ ] 表单/字段校验 composable
- [ ] 核心状态机 / 业务流程 composable
- [ ] 写操作 API 编排（`vi.mock` API，不断真后端）
- [ ] 关键存储（localStorage / token 池等）
- [ ] 主操作卡片：提交 / 禁用 / 关键 emit

#### P1（建议测）

- [ ] 页面 logic 编排层独有逻辑（如切 tab 清表单）
- [ ] 错误浮层 / 确认提示等次要组件（展示 + close/confirm emit）
- [ ] 分支提示卡（如「已有账号」二选一）

#### P2（默认跳过 Vitest）

- [ ] ~~整页 `index.vue` / `XxxView.vue` mount~~ → 留给 E2E
- [ ] ~~装饰性资源（插画、主题动画）~~ → 不测
- [ ] ~~跨 tab storage 同步~~ → E2E（若需要）
- [ ] ~~路由守卫 + 真登录进首页~~ → E2E
- [ ] ~~真实后端错误文案联调~~ → E2E

## 文件与命名约定

```
frontend/tests/
  helpers/                     # 通用挂载、清 storage
  <module>/
    p0/                        # 必测 *.spec.ts
    p1/                        # 建议测 *.spec.ts
    p2/README.md               # 仅登记不测项，不放用例
  PRIORITY_TEMPLATE.md
  README.md
  run.mjs
```

每个 `.spec.ts` 文件头注明：`[P0]` / `[P1]` 与目录路径。

## 用例写法要点

1. **测行为，不测实现细节**（断言状态/文案/emit，少断言内部私有函数）
2. **API 一律 mock**；成功/失败/抛错各至少一条（P0）
3. **Element Plus 用 stub**，测试环境关闭按需 CSS（见 `vite.config.js` 的 `VITEST` 分支）
4. **Teleport 组件** `attachTo: document.body`，`afterEach` 清空 body
5. **需要 `onMounted` 的 composable** 用 `tests/helpers/mountComposable.ts`

## 登录模块落地表（样板）

| 级别 | 项 | 文件 |
|------|----|------|
| P0 | useLoginForm | `login/p0/useLoginForm.spec.ts` |
| P0 | useSavedUsername | `login/p0/useSavedUsername.spec.ts` |
| P0 | useViewStateMachine | `login/p0/useViewStateMachine.spec.ts` |
| P0 | useAuthFlow | `login/p0/useAuthFlow.spec.ts` |
| P0 | useAuthPool | `login/p0/useAuthPool.spec.ts` |
| P0 | LoginCard / RegisterCard | `login/p0/LoginCard.spec.ts` 等 |
| P1 | useLoginView 切模式清表单 | `login/p1/LoginView.logic.spec.ts` |
| P1 | AccountSwitchPrompt | `login/p1/AccountSwitchPrompt.spec.ts` |
| P1 | LoginErrorOverlay | `login/p1/LoginErrorOverlay.spec.ts` |
| P2 | LoginView.vue / useHeroImage / 真后端 | `login/p2/README.md`（不写用例） |
| E2E | 真登录/注册/鉴权跳转 | 另册 |

## E2E 候选（不进 Vitest）

- 登录/注册成功进业务页
- 错误账号密码 / 后端宕机文案
- 记住账号刷新仍预填
- 多账号 switchPrompt 全流程
- 未登录访问受保护路由
- 跨 tab 账号同步（可选）
