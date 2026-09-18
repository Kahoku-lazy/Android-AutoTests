## 1. 壳层结构

- [x] 1.1 重写 `LoginView.vue` Hero：左栏标题/描述/「登录」「注册」CTA，右栏 Meeting doodle 容器挂载 `LoginCard`/`RegisterCard`/`AccountSwitchPrompt`/`LoginErrorOverlay`；删除 `.hero__brand` 与 `AnimalFace` 引用。验证：模板中无动物贴纸文案；`data-testid="login-page"` 仍在
- [x] 1.2 重写 `LoginView.style.css`：`.login-page` 横线笔记本底 + 稀疏 doodle 层；双栏 grid；Meeting doodle 虚线边/胶带/马克笔短线/硬阴影；CTA primary/ghost 对齐 showcase；≤768px 单栏堆叠；移除贴纸相关规则。验证：`cd frontend && npm run lint:styles` 通过；新样式无无关硬编码色扩散

## 2. 交互接线

- [x] 2.1 左侧「登录」「注册」绑定既有 `switchMode`；Meeting 标题随 `viewState` 显示「登录」/「注册」。验证：点击切换后对应卡片可见且标题正确
- [x] 2.2 确认 `switchPrompt` 态仍优先展示 `AccountSwitchPrompt`，不与表单双栏冲突。验证：有已存账号且无 `?add=1` 时进入切换提示

## 3. 测试与门禁

- [x] 3.1 更新/补充 `frontend/tests/login/**`：覆盖 CTA 切换、Meeting 标题、贴纸板不存在；既有登录/注册 testid 仍可用。验证：相关 vitest 通过
- [x] 3.2 跑前端构建与样式门禁：`cd frontend && npm run typecheck`（或项目惯用检查）与 `npm run lint:styles`。验证：本变更无新增失败

## 4. 扁平表单（去 AppCard 嵌套）

- [x] 4.1 `LoginCard` / `RegisterCard` / `AccountSwitchPrompt` 去掉 `AppCard`，改为 `.auth-panel`；`login-card.css` 去掉便签壳样式。验证：Meeting doodle 内无 `.ac-card` / `el-card`
- [x] 4.2 更新 login 单测与 Hero 断言（无嵌套卡）；跑 `lint:styles` + 相关 vitest。验证：通过
