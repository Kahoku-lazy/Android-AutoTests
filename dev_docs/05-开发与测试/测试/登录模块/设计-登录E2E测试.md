# 设计：登录模块 E2E 测试（方案 3）

> 日期：2026-08-12  
> 状态：已落地（E2E 12/12 通过）  
> 范围：C 档全量（含多账号 / 跨 tab）  
> 前提：API（`tests/auth/`）与 Vitest P0/P1 已覆盖契约与组件逻辑；本设计只补真浏览器整链路。

---

## 1. 目标与边界

### 目标

用 **pytest-playwright** 补齐登录相关 E2E，与现有 API 用例同仓库、同 Allure 报告，通过标签区分层级。

### 分层边界

| 层 | 位置 | 测什么 | 不测什么 |
|----|------|--------|----------|
| API | `tests/auth/test_*.py` | 400/401/Schema/黑名单 | UI、路由、localStorage |
| Vitest P0/P1 | `frontend/tests/login/` | 校验、composables、卡片 emit | 真后端跳转 |
| E2E | `tests/auth/e2e/` | 真浏览器：UI → API → 路由/存储 | 字段级 400 穷举 |

### 明确不做（本阶段）

- 不写 Vitest 整页 `LoginView` mount（见 `frontend/tests/login/p2/README.md`）
- 不新建前端 Playwright 独立栈
- 不强制接入 CI 门禁（先本地可跑）

---

## 2. 目录结构

```
tests/
├── conftest.py                      # 已有：base_url、Allure 元数据
├── e2e/                             # 新增：跨模块 E2E 共享
│   ├── __init__.py
│   ├── conftest.py                  # FRONTEND_URL、login_as、clear_auth
│   └── selectors.py                 # data-testid 常量（唯一选择器源）
└── auth/
    ├── test_login.py                # 已有 API（不动逻辑）
    ├── ...
    ├── README.md                    # 增补「E2E」小节
    └── e2e/
        ├── __init__.py
        ├── conftest.py              # auth E2E 专用：second_user 等
        ├── test_login_flow.py
        ├── test_register_flow.py
        ├── test_account_switch.py
        └── test_cross_tab.py
```

`tests/case_manager/test_e2e_api_editor.py` 中的 `_login` 改为调用共享 `login_as()`（同批或紧随跟进）。

---

## 3. Allure：API 与 E2E 同一报告 + 标签区分

### 结论

**可以。** 项目已默认 `--alluredir=tests/allure-results`（`pytest.ini`）。一次跑完 `tests/auth/`（含 API + e2e 子目录），结果写入同一目录，`allure serve` 即同一份报告。

### 约定（必须遵守）

| 维度 | API（已有） | E2E（新增） |
|------|-------------|-------------|
| `pytest.mark` | `@pytest.mark.api` + `@pytest.mark.auth` | `@pytest.mark.e2e` + `@pytest.mark.ui` + `@pytest.mark.auth` |
| `allure.tag` | `("auth", "api", priority, …)` | `("auth", "e2e", priority, …)` |
| `allure.feature` | `"认证模块"` | `"认证模块"`（同一 Feature，便于并排看） |
| `allure.story` | `"登录接口"` / `"注册接口"` / … | `"登录E2E"` / `"注册E2E"` / `"多账号E2E"` / `"跨TabE2E"` |
| 用例 ID 前缀 | `TC-LOGIN-*` / `TC-REG-*` | `TC-E2E-LOGIN-*` / `TC-E2E-REG-*` / `TC-E2E-SW-*` / `TC-E2E-TAB-*` |

筛选示例：

```bash
# 同一 Allure 目录，全量认证（API + E2E）
python -m pytest tests/auth/ -v

# 只跑接口
python -m pytest tests/auth/ -v -m "api and auth"

# 只跑 E2E
python -m pytest tests/auth/e2e/ -v -m e2e --browser chromium

# 报告
allure serve tests/allure-results
```

报告内：按 **Tags** 点 `api` / `e2e`，或按 **Story** 区分「登录接口」与「登录E2E」。

E2E 复用 `tests/auth/conftest.py` 的 `set_allure_metadata(...)`，`tags` 传入 `("auth", "e2e", "P0")` 即可，禁止漏标导致报告里分不清层级。

---

## 4. 环境与依赖

| 项 | 约定 |
|----|------|
| 前端 | `TEST_FRONTEND_URL`，默认 `http://localhost:5173` |
| 后端 | `TEST_BASE_URL`，默认 `http://localhost:8766` |
| 浏览器 | Chromium（pytest-playwright） |
| 依赖 | `requirements.txt` 增加 `pytest-playwright`；执行前 `playwright install chromium` |
| 凭据 | `admin / admin123`（与 API 测试一致） |
| 服务探测 | session 级探测前后端；不可达则 **skip 整组 E2E**，不硬 fail |

---

## 5. 共享 Helper 与 Fixture

### Helper（`tests/e2e/`）

| 函数 | 行为 |
|------|------|
| `login_as(page, username, password)` | 打开 `/login` → 填 testid → 提交 → `wait_for_url("**/dashboard**")` |
| `clear_auth(page)` | 清除 `localStorage`（含 `auth_accounts`）与 `sessionStorage`（含 `auth_active`） |
| `logout_via_ui(page)` | 点击侧边栏退出（`sidebar-logout`） |

### Fixture

| Fixture | 作用 |
|---------|------|
| `frontend_url` | session，读环境变量 |
| `clean_page` | function：新 page + `clear_auth` |
| `admin_creds` | 固定 admin |
| `second_user` | API 预注册 `E2E-{ts}`；teardown 尽量删除 |

### 清理

1. 每用例开始 `clear_auth`（必须）
2. 注册用户优先 API 创建 + teardown 删除；删失败不阻断套件
3. 不删除非 `E2E-` / `admin` 账号

---

## 6. data-testid 约定

前端登录相关组件补齐稳定 testid；Python 只认 `tests/e2e/selectors.py`，禁止散写 `text=登录` 类脆弱定位。

| testid | 位置 |
|--------|------|
| `login-page` | `LoginView` 根 |
| `login-username` / `login-password` | 登录输入 |
| `login-remember` | 记住账号 |
| `login-submit` | 登录按钮 |
| `login-to-register` | 去注册 |
| `register-username` / `register-email` / `register-password` / `register-password2` | 注册输入 |
| `register-submit` / `register-to-login` | 注册提交 / 去登录 |
| `login-error-overlay` / `login-error-message` / `login-error-dismiss` | 错误遮罩 |
| `account-switch-prompt` / `switch-to-existing` / `add-new-account` | 多账号 Prompt |
| `app-sidebar` / `sidebar-logout` / `sidebar-add-account` | 侧边栏 |

---

## 7. 用例清单（C 档）

### 登录流 `test_login_flow.py`

| ID | 场景 | 关键断言 |
|----|------|----------|
| TC-E2E-LOGIN-001 | 正确账号密码登录 | URL → `/dashboard`，侧边栏可见 |
| TC-E2E-LOGIN-002 | 密码错误 | 错误遮罩出现，文案含「用户名或密码错误」，仍在 `/login` |
| TC-E2E-LOGIN-003 | 记住账号 → 清 token 再开 `/login` | 用户名预填 |
| TC-E2E-LOGIN-004 | 未登录访问 `/dashboard` | 踢回 `/login` |
| TC-E2E-LOGIN-005 | 已登录访问 `/login`（无 `?add`） | 重定向 `/dashboard` |
| TC-E2E-LOGIN-006 | 登录 → UI 登出 | 回 `/login`；再访受保护页仍被踢 |

### 注册流 `test_register_flow.py`

| ID | 场景 | 关键断言 |
|----|------|----------|
| TC-E2E-REG-001 | 注册新用户 | 成功后进 `/dashboard` |
| TC-E2E-REG-002 | 「去注册」↔「去登录」 | LoginCard / RegisterCard 切换 |

### 多账号 `test_account_switch.py`（按真实路由校准）

代码事实：有 token 且访问 `/login`（无 `?add`）会进 dashboard；侧边栏「添加账号」进 `/login?add=1` 显示 LoginCard。`switchPrompt` 与路由守卫可能冲突。

| ID | 场景 | 关键断言 |
|----|------|----------|
| TC-E2E-SW-001 | 登录后点「添加账号」 | URL 含 `add=1`，出现 LoginCard |
| TC-E2E-SW-002 | 在该页登录第二账号 | dashboard；`auth_accounts` 含 2 个 key |
| TC-E2E-SW-003 | 侧边栏账号菜单切换（若可点） | active 变化 / 页面仍可用 |
| Prompt 相关 | 手工确认可达性 | 不可达则 `skip` + 记产品债，或先修再测 |

### 跨 Tab `test_cross_tab.py`

| ID | 场景 | 关键断言 |
|----|------|----------|
| TC-E2E-TAB-001 | 同 context 第二 page | 共享 localStorage 池一致（或刷新后一致） |

---

## 8. 实现顺序（建议）

1. 前端补 `data-testid`（登录组件 + 侧边栏关键按钮）
2. `tests/e2e/` 共享层（selectors / login_as / clear_auth）
3. `test_login_flow.py`（001–006）
4. `test_register_flow.py`
5. `test_account_switch.py` + 手工验证 Prompt
6. `test_cross_tab.py`
7. case_manager `_login` 迁到 `login_as`
8. 更新 `tests/auth/README.md` + 本目录说明

---

## 9. 成功标准

- [ ] `pytest tests/auth/ -m api` 与改前一致（回归）
- [ ] `pytest tests/auth/e2e/ -m e2e --browser chromium` 上表用例通过或按约定 skip
- [ ] 同一次 `allure serve tests/allure-results` 可见 API + E2E；Tags 可筛 `api` / `e2e`
- [ ] E2E 选择器全部来自 `selectors.py`，无脆弱文本定位（除断言文案内容本身）
)
