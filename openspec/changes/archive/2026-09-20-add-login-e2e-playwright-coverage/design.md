## Context

见 proposal.md — Why。现状约束（均为实测）：

1. 端到端层是 **Python + pytest-playwright 0.9.0**（Playwright 1.61.0，本机已装 chromium 1228 与 chrome-headless-shell 1228），`page` 夹具默认无头即可用；`tests/e2e/conftest.py` 已有前后端可达性检查与失败截图钩子。
2. 前端 5173 / 后端 8766 由 `python run.py start` 拉起；Vite 把 `/api` 代理到 8766，因此浏览器侧看到的登录请求是 `http://localhost:5173/api/auth/login/`。
3. 登录页现有 `data-testid` 已覆盖：`login-page` / `login-username` / `login-password` / `login-remember` / `login-submit` / `login-to-register` / `login-mode-login` / `login-mode-register` / `login-error-message` / `login-error-dismiss`；注册卡 `register-*`；侧栏 `sidebar-logout`。
4. 路由守卫（`router.ts:30-39`）：无令牌且非 `/login` → `/login`；有令牌访问 `/login` 且无 `?add` → `/dashboard`。
5. 记住账号存 `localStorage.saved_username`；令牌池存 `localStorage.auth_accounts` + `sessionStorage.auth_active`。

## Goals / Non-Goals

**Goals**

- 端到端层在**不提供任何密钥**的前提下可执行、可守护，且覆盖「按钮态 / 点击次数 / 长按 / loading / 覆盖层 / 守卫 / 窄屏」这些只有真实浏览器能看到的回归面。

**Non-Goals**

- 不改前端源码、不新增 testid、不改后端行为；不追求 UI 像素级断言（那属于设计层地图产物）。
- 不覆盖需要环境编排的用例（停后端 / 多标签页 / 限速）与会话账号切片。

## Decisions

### D1 账号来源：自建夹具账号，而不是密钥或超级管理员

**选择**：夹具首次运行时用公开端点 `POST /api/auth/register/` 创建固定账号 `e2e_probe / e2e-probe-password`；若返回 409（已存在）则改用 `POST /api/auth/login/` 登录复用。任一失败即 **fail**（明确报错），不 skip。

**理由**：实测该账号（非超级用户、无任何角色）能完整登录并渲染 `/dashboard`（见探针输出：`URL after login: .../dashboard`，仪表盘正文正常）。相比两个替代方案：

| 方案 | 问题 |
|---|---|
| 环境变量 `TEST_ADMIN_PASSWORD` | 默认门禁静默跳过 —— 正是 `tests/AGENTS.md` 点名的「起不到守护作用」 |
| 复用 admin 超级管理员 | 会把超级管理员权限带进 E2E，测出来的路径不代表普通用户；且仍需密钥 |

**代价**：开发库多 1 行 `auth_user`（固定用户名，不随运行次数增长）。这与接口层注册用例已经在写库的既有做法一致。

### D2 选择器只来自 `selectors.py`，且只用现有 testid

**选择**：新增常量集中在 `tests/e2e/selectors.py`（它自己的文档字符串就是这么要求的），用例里不出现字面选择器。缺 hook 的观测点改用「已存在的 testid + 属性/类」表达（例如按钮禁用态读 `[data-testid=login-submit] button` 的 `disabled`，loading 读 `is-loading` 类）。

**理由**：为测试改前端源码会引入一次不必要的生产变更；能用现有 hook 表达就不碰源码。

### D3 「只发 1 次请求」用网络层计数，不看界面

**选择**：用例内 `page.on("request")` 收集 URL 以 `/api/auth/login/` 结尾的请求，断言计数。

**理由**：功能文档已明确「连点类用例必须同时看网络面板的请求条数，只看界面会漏掉重复提交」。界面断言（覆盖层层数）作为第二条独立断言同时保留。

### D4 loading 窗口用 `page.route` 制造，而不是靠响应够慢

**选择**：E2E-007 先 `page.route` 拦截登录请求、延迟 1.5 秒再 `continue_`，在这段确定窗口内断言按钮处于 loading 且不可点，然后再放行、断言落到工作台。

**理由**：本地后端响应只有几十毫秒，直接断言 loading 是 flaky 的。延迟放行把「观测 loading」变成确定性事件。

### D5 回车不提交：断言当前行为，并显式标注它是待决项

**选择**：E2E-008 断言「焦点在密码框按 Enter 不发请求」，并在用例与文档里写明依据（表单没有原生 submit 按钮）。

**理由**：这是功能文档第五节待决项 1 的实测结论。把它固化成用例，等于给产品决策装了一个「改变即报警」的探针；同时用注释标明「若决定支持回车提交，本用例应改为断言 1 次请求」，避免它被误读成「回车不提交是期望行为」。

### D6 storage 隔离靠 pytest-playwright 的 per-test context

**选择**：不手工清 storage —— 每个用例默认拿到全新的 browser context。

**理由**：`remember` 与守卫用例需要「同一次上下文内跨页面」的 storage 连续性，用同一 context 里的 `context.new_page()` 或同页导航即可，不必自己造清理逻辑。

### D7 删除占位示例用例

**选择**：删除 `tests/e2e/test_example_e2e.py`。

**理由**：它是自称的占位模板，且是唯一依赖密钥的用例；其链路被 E2E-001 正式覆盖。留着会让「端到端层需要密钥」的错误印象继续存在。

## Risks / Trade-offs

- [`e2e_probe` 被别人改了密码或被删] → 夹具 register 409 后 login 失败即 fail 并打印明确信息（要求删除/改名该账号或改夹具常量），不静默跳过。
- [前后端没起] → 沿用既有 `e2e_services` 夹具 skip 整组；这是环境不可达，不是用例缺陷。
- [连点 / 长按对时序敏感] → 固定点击间隔（0.12s × 5）与固定按压 1.2s，断言目标是请求计数（离散量）而非动画状态。
- [E2E 让开发库累积账号] → 固定用户名复用，总量恒为 1。
- [窄屏断言过严导致误报] → 只断言「无横向滚动」与「登录卡与按钮命中可点」，不断言具体像素。
