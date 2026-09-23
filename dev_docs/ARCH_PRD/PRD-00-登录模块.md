# 登录模块 业务功能需求

> 版本：v1.0 · 日期：2026-09-20 · 状态：新建（对照 HEAD 实测）
> 范围：`apps/accounts`（后端）· `frontend/src/views/`（登录页）· `frontend/src/shared/`（会话基础设施）· `frontend/src/router.ts`（路由守卫）
> 关联：[平台总体架构](ARCH-平台总体架构.md) · [需求总纲](PRD-需求总纲.md) · [API-登录](../DEV_TEST/接口文档/API-登录.md)
> 规格真相源：`openspec/specs/` 下的 auth-session · auth-registration · auth-form-validation · auth-response-shape · api-path-convention

---

## 产品功能

### 登录

#### UI交互

1. **模版** —— 一张登录卡片，从上到下：
   1. 账号输入框 —— 占位「账号」
   2. 密码输入框 —— 占位「密码」，右侧小眼睛可切明文
   3. 「记住账号」开关
   4. 登录按钮
   5. 卡片底部「没有账号？去注册 →」
   `views/components/LoginCard.vue`
2. **业务逻辑**
   1. 边填边校验：不合格的输入框变红、下方说明原因；两项都合格按钮才亮。
   2. 点登录：按钮转圈，期间不能重复点。
   3. 登录成功：提示「登录成功，正在跳转...」，会话写入本地（单账号），跳转工作台 `/dashboard`。
   4. 登录失败：覆盖层显示后端给的原因；卡片上已填内容保留，改完可以直接再点。
   5. 「记住账号」勾选且这次登录成功：下次打开登录页，账号自动填好。
   6. 点「去注册」：清空注册表单的四个字段。
   `views/LoginView.logic.ts` · `views/composables/useAuthFlow.ts`
3. **样式** —— 以实际代码为准
   `views/styles/login-card.css` · `views/styles/auth-form-card.css` · `views/LoginView.style.css` · `shared/styles/tokens.css`
4. **校验** —— 即时显示在对应输入框下方，共 4 条：
   1. 账号 3 条 —— 「请输入用户名」「用户名不能为空白」「用户名过长，最多150个字符」
   2. 密码 1 条 —— 「请输入密码」
   `shared/composables/useLoginForm.ts`
5. **出口** —— 只把「账号 + 密码」两个字段交给 `POST /api/auth/login/`：
   1. 请求体只有 `username` 与 `password` 两个字段。
   2. 密码不做任何修剪。
   3. 成功还是失败，由后端回来的信封决定。
   `shared/api/auth.ts`

#### API契约

登录接口：POST api/auth/login/

1. **入口**
   1. 方法与路径：`POST api/auth/login/`。
   2. 尾斜杠必须带，不带是 404（`APPEND_SLASH=False`，容错中间件已删除）。
   3. 公开端点：不需要登录，也不做 DRF 鉴权。
   4. 请求字段：`username` / `password`，2 个字符串，都允许留空，留空会被校验拦下。
   `apps/accounts/urls.py` · `apps/accounts/serializers.py`
2. **业务规则**
   1. 先把账号和密码填齐 —— 缺一个就直接拒绝，不去查库。
   2. 账号格式：不能是纯空白，最长 150 个字符。
   3. 拿账号密码核对身份。核对不通过时，「密码错」和「用户不存在」给同一句话 —— 防止有人靠反复试来猜哪些账号存在。
   4. 核对通过 → 签一对令牌，access 与 refresh 共享同一个会话标识（`sid`），方便以后按会话一起作废。登录**不写库、不写 Redis**。
   5. 签令牌的前提：**生产环境的签名密钥不得是默认值** —— 非调试模式下密钥为空、或仍是占位值 `change-me`，服务启动即抛错，不签发任何令牌。
   6. 令牌里必须带 `sub`（用户 id）。**缺 `sub` 的令牌一律 401，不得冒成 500** —— 下游四个调用点都直接取 `sub` 用。
   `apps/accounts/serializers.py` · `apps/accounts/views.py` · `shared/auth/jwt_auth.py`
3. **返回**
   1. `200` 登录成功，签发令牌对
   2. `400` 账号或密码没填、格式不合格
   3. `401` 账号或密码错误
   4. 统一信封 `{status, data}` / `{status, message}`
   5. 成功体：`access_token` · `refresh_token` · `token_type: bearer` · `user: {id, username}`
   6. 失败时的 `message` 按固定顺序取：响应里的 `message` → `detail` → 第一个字段的第一条错误 → 列表首项 → 兜底「请求无效」。
   7. 其中 `detail` 以 `JSON parse error` 开头时，换成产品文案「请求格式错误」再返回。
   `shared/renderers.py`
4. **校验** —— 这个端点会给出的提示，共 6 条（按源码顺序）：
   1.「请输入用户名和密码」
   2.「请输入用户名」
   3.「请输入密码」
   4.「用户名不能为空白」
   5.「用户名过长，最多150个字符」
   6.「用户名或密码错误」

   另有 1 条不在 serializer 里：请求体不是合法 JSON 时，框架先报 `JSON parse error`，由渲染器换成产品文案「请求格式错误」再返回 `400`。
   `shared/renderers.py`

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 长度 / 格式约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 登录 | `username`（账号） | CharField（字符串） | 必填 | 不能是纯空白 · 最长 150 个字符 | `auth_user.username` |
| 登录 | `password`（密码） | CharField（字符串） | 必填 | 只要求非空 · 首尾空白由接口去掉（与注册同口径） | `auth_user.password` |

> 接口层这两个字段都声明成 `required=False` / `allow_blank=True` —— 留空会走到「请输入用户名」这类产品文案，而不是 DRF 默认的字段必填错误。

`auth_user` 的列（全部功能共用这张表；★ 是登录模块真正读写的 7 列）：

| 列 | 类型 | 长度 | 约束 |
|---|---|---|---|
| ★ `id` | AutoField | — | 主键 · 唯一 · 非空 |
| ★ `password` | CharField | 128 | 非空（存哈希，不是明文） |
| `last_login` | DateTimeField | — | 可空 |
| ★ `is_superuser` | BooleanField | — | 非空 |
| ★ `username` | CharField | 150 | **唯一** · 非空 |
| `first_name` | CharField | 150 | 非空 |
| `last_name` | CharField | 150 | 非空 |
| ★ `email` | EmailField | 254 | 非空 |
| `is_staff` | BooleanField | — | 非空 |
| ★ `is_active` | BooleanField | — | 非空；Django 认证后端核对身份时检查，停用账号登不进来 |
| ★ `date_joined` | DateTimeField | — | 非空；建账号时写入 |

> 这张表由 Django 内置 `User` 决定 —— `apps/accounts` 没有 `models.py`。后端登录只读它（`authenticate()`），只有注册会写。

### 注册

#### UI交互

1. **模版** —— 一张注册卡片，从上到下：
   1. 账号 —— 占位「设置账号（3-20 字符）」
   2. 邮箱 —— 占位「邮箱地址」
   3. 密码 —— 占位「设置密码（至少 6 位）」
   4. 确认密码 —— 占位「确认密码」
   5. 完成注册按钮
   6. 卡片底部「已有账号？去登录 →」
   `views/components/RegisterCard.vue`
2. **业务逻辑**
   1. 四个字段边填边校验，提示各自显示在对应输入框下方；四项全过之前按钮是灰的。
   2. 提交后按钮转圈。
   3. **注册成功即完成登录** —— 直接进入工作台，不需要再登一次，会话写入本地（单账号）。
   4. 账号被占用：提示「用户名已存在」，其余字段保留，换个账号可以立刻重试。
   5. 点「去登录」：清掉刚填的登录密码，不留上一次的输入。
   `views/LoginView.logic.ts` · `views/composables/useAuthFlow.ts`
3. **样式** ——以实际代码为准
   `views/styles/login-card.css` · `views/styles/auth-form-card.css`
4. **校验** —— 即时显示在对应输入框下方，共 9 条：
   1. 账号 3 条 —— 「请输入用户名」「用户名至少 3 个字符」「用户名最多 20 个字符」
   2. 邮箱 2 条 —— 「请输入邮箱」「邮箱格式不正确」
   3. 密码 2 条 —— 「请输入密码」「密码至少 6 位」
   4. 确认密码 2 条 —— 「请再次输入密码」「两次密码不一致」
   `shared/composables/useLoginForm.ts`
5. **出口** —— 把四个字段交给 `POST /api/auth/register/`：
   1. 请求体是账号、邮箱、密码、确认密码。
   2. 提交前四个字段的首尾空白都会先去掉（与后端 `strip` 对齐）。
   3. 成功还是失败，由后端回来的信封决定。
   `shared/api/auth.ts`

#### API契约

注册接口：POST api/auth/register/

1. **入口**
   1. 方法与路径：`POST api/auth/register/`。
   2. 尾斜杠必须带，不带是 404。
   3. 公开端点：不需要登录，也不做 DRF 鉴权。
   4. 请求字段：`username` / `password` / `password2` / `email`，4 个字符串，都允许留空。
   `apps/accounts/urls.py` · `apps/accounts/serializers.py`
2. **业务规则**
   1. 先查四个字段的格式：账号长度与空白、邮箱格式、密码长度、两次密码是否一致。
   2. 格式过了才建账号；用户名重不重复**不在这里判**，交给数据库的唯一约束。
   3. 撞上重名 → `409`「用户名已存在」，而不是 `500`。两个请求同时抢同一个名字，也只有一个成功、另一个拿 409。
   4. 建账号成功 → 直接签一对令牌，用户不用再登一次。写库经 `apps/accounts/api.py`（唯一写口，`IntegrityError` 翻译成领域错误）。
   `apps/accounts/serializers.py` · `apps/accounts/views.py` · `apps/accounts/api.py`
3. **返回**
   1. `200` 注册成功，同时完成登录
   2. `400` 字段格式不合格
   3. `409` 用户名已存在
   4. 统一信封 `{status, data}` / `{status, message}`
   5. 成功体：`access_token` · `refresh_token` · `token_type: bearer` · `user: {id, username, email}`（比登录多了 `email`）
   `shared/renderers.py`
4. **校验** —— 这个端点会给出的提示，共 9 条（按源码顺序）：
   1.「请输入用户名和密码」
   2.「请输入用户名」
   3.「请输入密码」
   4.「用户名至少 3 个字符」
   5.「用户名最多 20 个字符」
   6.「密码至少 6 位」
   7.「两次密码不一致」
   8.「请输入邮箱」
   9.「邮箱格式不正确」

   `409` 不是校验文案，是写口翻出来的领域结论。
   `apps/accounts/serializers.py`

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 长度 / 格式约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 注册 | `username`（账号） | CharField（字符串） | 必填 | 3 – 20 个字符 | `auth_user.username`（唯一） |
| 注册 | `email`（邮箱） | CharField（字符串） | 必填 | 必须含 `@` | `auth_user.email` |
| 注册 | `password`（密码） | CharField（字符串） | 必填 | 至少 6 位 | `auth_user.password`（存哈希） |
| 注册 | `password2`（确认密码） | CharField（字符串） | 必填 | 必须与密码一致 | **不落库** —— 只用于确认 |

> 注册是登录模块里**唯一写库**的动作：经 `apps/accounts/api.py` 的 `create_user()` → `User.objects.create_user()`，写入时 `is_active=True`、`date_joined=now`。

### 刷新令牌

#### UI交互

1. **模版** —— **无界面**。用户看不到「刷新」这件事，它是请求层的自动行为。
2. **业务逻辑**
   1. 访问令牌过期时，受保护请求被 `401` 挡下 → 自动用刷新令牌换一次新访问令牌，然后**重发原请求**，用户无感。
   2. 多个请求同时遇到 401 时**只刷新一次**，其余等这一次的结果（`refreshPromise` 锁）。
   3. 公开认证端点（登录 / 注册 / 刷新）的 401 表示凭证本身无效，**不触发刷新**。
   4. 刷新失败 → 清掉本地令牌；还有别的账号就切过去，一个都不剩才跳登录页。
   `shared/api-auth-interceptors.ts` · `shared/api-client.ts`
3. **样式** —— 无。
4. **校验** —— 无字段级校验；两句驳回文案由视图直接返回（见 API 契约）。
5. **出口** —— `POST /api/auth/refresh/`，只带 `refresh_token`。
   `shared/api/auth.ts`（`logout` / `me` / `login` / `register`）· `shared/api-client.ts`（`refresh`）

#### API契约

刷新令牌接口：POST api/auth/refresh/

1. **入口**
   1. 方法与路径：`POST api/auth/refresh/`。
   2. 尾斜杠必须带，不带是 404。
   3. 公开端点：不需要登录，也不做 DRF 鉴权。
   4. 请求字段：`refresh_token`，1 个字符串。
   `apps/accounts/urls.py`
2. **业务规则**
   1. 只认刷新令牌；拿访问令牌或别的类型来换，一律拒绝。
   2. 令牌本身坏了、过期了，或者它所属的会话已经被登出作废 → 也拒绝。
   3. 换发新访问令牌时会把会话标识 `sid` 一起带过去 —— 这样登出仍然撤得掉续期后的令牌。
   `apps/accounts/views.py` · `shared/auth/jwt_auth.py`
3. **返回**
   1. `200` 换发新的访问令牌 —— **不返回新 refresh**
   2. `401` 刷新令牌无效、过期、类型不对，或会话已作废
   3. 统一信封 `{status, data}` / `{status, message}`
   4. 成功体：`access_token` · `token_type: bearer`
4. **校验** —— 无字段级校验（`RefreshSerializer` 没有 `ValidationError`）。这个端点的两句驳回文案在视图里：
   1.「令牌类型错误，需要刷新令牌」—— 传进来的是访问令牌或类型不符
   2.「刷新令牌无效或已过期」—— 令牌无效、过期或已被吊销

#### 数据表单

无表单，令牌走请求体。令牌本身的结构（HS256）：

| claim | 含义 |
|---|---|
| `sub` | 用户 id。缺 `sub` 必须 401，不是 500 |
| `jti` | 单个令牌的唯一 id，登出兜底按它吊销 |
| `iat` / `exp` | 签发时间 / 过期时间。访问令牌 1 小时，刷新令牌 7 天 |
| `type` | `access` 或 `refresh`；换令牌时必须匹配 |
| `sid` | 会话标识。一次登录的访问与刷新令牌共享同一个 `sid`，登出按它整组作废 |

> `sid` 只存在于令牌内部，**不出现在任何 API 响应里** —— 接口形状与前端都不受影响。

### 登出

#### UI交互

1. **模版** —— **不在登录页**：
   1. 登出入口在侧栏底部的账号区（`data-testid=sidebar-logout`）。
   2. 折叠态下同一入口渲染为图标按钮（⎋），行为相同。
   `shared/components/AppSidebar.vue`
2. **业务逻辑**
   1. 点登出 → 调 `POST /api/auth/logout/`。
   2. 成功：清空本地会话（`access_token` / `refresh_token` / `username`）并跳回登录页。单账号下没有「还有别的账号就切过去」这回事。
   3. 后端返回 **503 + `retry`** 时：提示「服务暂时异常，请稍后重试」并**保留本地登录态** —— 用户不用重新登。
   4. 其它失败（网络异常 / 令牌已失效）：仍清本地，避免用户卡在已失效的会话里。
   `shared/components/AppSidebar.vue` · `shared/auth/token-storage.ts`
3. **样式** —— 登出入口在侧栏，不在登录页；侧栏皮肤与登录页共用同一套令牌。
4. **校验** —— 无。
5. **出口** —— `POST /api/auth/logout/`，令牌走 `Authorization` 头，无请求体。
   `shared/api/auth.ts`

#### API契约

登出接口：POST api/auth/logout/

1. **入口**
   1. 方法与路径：`POST api/auth/logout/`。
   2. 尾斜杠必须带，不带是 404。
   3. **需要登录**：`IsAuthenticated`，必须带 `Authorization` 令牌。
   4. 无请求字段，令牌走请求头。
   `apps/accounts/urls.py` · `apps/accounts/views.py`
2. **业务规则**
   1. 从请求头取令牌，不接收请求体。
   2. 按**会话**作废：一次登录签发的访问与刷新令牌一起失效，而不只是当前这一个 —— 按 `sid` 写 `jwt:session_revoked:<sid>`。
   3. 签发时没有会话标识的老令牌，按单个令牌兜底作废 —— 按 `jti` 写 `jwt:blacklist:<jti>`。
   4. 写不进吊销记录就**拒绝登出** —— 返回 `503` 让调用方重试，绝不假装成功。
   5. **网关先拦**：`logout` 不在网关的公开路径白名单里，所以没带令牌的请求**到不了视图** —— 由 `gateway/middleware.py` 直接返回 `401`「请先登录」；令牌无效则返回 `401`「登录已过期或令牌无效」。视图里那段「没带头就返回空对象」的兜底在真实链路上不可达。
   `apps/accounts/views.py` · `shared/auth/jwt_auth.py`
3. **返回**
   1. `200` 整个会话已作废（`data: {}`）
   2. `503` 写不进吊销记录
   3. `503` 的响应体带 `retry: true`，调用方据此重试
4. **校验** —— 无字段级校验。`503` 的文案是「Redis 不可用，无法撤销令牌」。

#### 数据表单

无表单。登出会写两个 Redis 键，**TTL 不一样**：

| 键 | 谁写 | TTL | 为什么是这个值 |
|---|---|---|---|
| `jwt:session_revoked:<sid>` | `revoke_session()` | `JWT_REFRESH_TTL` = 604800s（7 天）| 登出只带访问令牌（1 小时），但同会话的刷新令牌还有至多 7 天寿命 —— TTL 取短了，刷新令牌会复活 |
| `jwt:blacklist:<jti>` | `blacklist_token()` | `max(exp - now, 60)`，即令牌**剩余寿命**，最少 60 秒 | 给没有 `sid` 的老令牌兜底；令牌自己过期就够了，不必留 7 天 |

> 这里有一处**刻意的不对称**：登出是 **fail-closed**（写不进就 503 拒绝），而校验是 **fail-open** —— `_is_revoked()` 在 Redis 不可用时返回「未吊销」并放行令牌，理由是「拒绝所有令牌会把所有人锁在门外」。
> `shared/auth/jwt_auth.py`

### 查看当前身份

#### UI交互

1. **模版** —— 无独立界面。消费方是 AI 助手：`modules/ai-assistant/index.vue` 与 `ToolDebugPage.vue` 用 `isSuperuser` 决定管理入口是否可见。
2. **业务逻辑** —— 全局**只拉取一次**并共享；取失败时把 `isSuperuser` 记为 `false`（看不到管理入口，而不是报错）。
   `shared/composables/useAuthUser.ts`
3. **样式** —— 无。
4. **校验** —— 无。
5. **出口** —— `GET /api/auth/me/`。
   `shared/api/auth.ts`

#### API契约

当前用户接口：GET api/auth/me/

1. **入口**
   1. 方法与路径：`GET api/auth/me/`。
   2. 尾斜杠必须带，不带是 404。
   3. **需要登录**：必须带 `Authorization` 令牌。
   4. 无请求字段。
   `apps/accounts/urls.py`
2. **业务规则**
   1. 只读，不改任何东西。
   2. 必须带令牌；没带、或者令牌已被登出作废 → `401`。
   3. 令牌有效但账号已经被删 → `404`。
   4. 返回里带 `is_superuser`，前端据此决定要不要显示管理入口。
   `apps/accounts/views.py`
3. **返回**
   1. `200` 返回当前身份
   2. `401` 没带令牌，或令牌已被登出作废
   3. `404` 账号已被删除
   4. 成功体：`user: {id, username, is_superuser}`
4. **校验** —— 无字段级校验。

#### 数据表单

无表单，只读 `auth_user` 的三列：`id` · `username` · `is_superuser`。

### 会话与账号管理

> 这一节不是端点，是「登录成功之后，会话怎么被持有与使用」。代码住在 `shared/` 与 `router.ts`，不属于登录页，但业务上是登录这件事的完整闭环。

#### UI交互

1. **模版**
   1. 侧栏底部账号区：只显示当前账号名（`data-testid=sidebar-active-account`），**不可点开** —— 单账号下没有账号列表。
   2. 账号区下方是「● 在线」状态与「退出」按钮。
   3. 折叠态下账号名隐藏，靠 `title` 提示当前账号。
   `shared/components/AppSidebar.vue`
2. **业务逻辑**
   1. **未登录守卫**：没有令牌时访问任何页面 → 一律跳回 `/login`。
   2. **已登录免登**：已有令牌时访问 `/login` → 一律跳 `/dashboard`，**没有 `?add` 例外**。
   3. **单账号会话**：登录成功后整份会话（`access_token` / `refresh_token` / `username`）写在 `localStorage`，一次只保留一个账号；再登一个会**覆盖**前一个。
   4. **无切换**：不提供账号列表、账号切换与「添加账号」入口。
   5. **登出**：清空整份会话并回登录页。
   6. **无跨标签页同步**：两个标签页共享同一份 `localStorage` 会话，后登录者覆盖先登录者（见下方数据表单的取舍说明）。
   `router.ts` · `shared/auth/token-storage.ts`
3. **样式** —— 侧栏账号菜单的皮肤，与登录页共用同一套令牌。
4. **校验** —— 无。
5. **出口**
   1. 会话的唯一读写点是 `shared/auth/token-storage.ts` —— api-client 与页面都从它读写，消除双源竞态。
   2. 请求头的注入在 `shared/api-auth-interceptors.ts`；续期失败会清空会话并跳转登录页。

#### API契约

本节不新增端点，复用上面的「登出」与「刷新令牌」；身份由「查看当前身份」提供。

#### 数据表单

浏览器本地存储（不在数据库里）：

| 键 | 内容 | 说明 |
|---|---|---|
| `localStorage.access_token` | 访问令牌 | `token-storage.ts` 是唯一读写点 |
| `localStorage.refresh_token` | 刷新令牌 | 续期失败时与 access 一起清空 |
| `localStorage.username` | 当前账号名 | 侧栏显示与设备页「当前用户」都读它 |
| `localStorage.saved_username` | 上次「记住账号」的用户名 | 与令牌无关，登出不清 |

**一次只保留一个账号**：`saveSession()` 覆盖写入上面三项，并顺带删除多账号时代遗留的 `auth_accounts` 键。

**不做反向迁移**：升级后老用户的 `auth_accounts` 不再被读取，表现为「未登录」，被守卫送回 `/login` 重新登录一次 —— 账号池的 active 记在 `sessionStorage`，迁移代码无法判断该选哪个账号，静默挑一个比重登更差。

**已知取舍（跨标签页）**：单账号共用一份 `localStorage`，后登录者覆盖先登录者；先开的标签页可能短时显示旧账号名（令牌已是新的），刷新后一致。本次不为它补替代实现。

---

## 测试

> 本模块各功能的测试资产按功能分节登记，每节含「业务场景 · 接口自动化测试用例 · 前端单元层测试用例 · 业务功能测试用例」四类；逐条用例文档见 `dev_docs/DEV_TEST/`。

### 登录

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧**
   - 记住账号回填【模版 · 业务逻辑 5】—— WHEN 上次勾了「记住账号」且那次登录成功，再次打开登录页 → THEN 账号框已自动填好，密码框为空
   - 即时校验【业务逻辑 1 · 校验】—— WHEN 账号或密码为空 → THEN 该输入框变红、下方给出对应文案
   - 提交门槛【业务逻辑 1】—— WHEN 两项都合格 → THEN 登录按钮才亮；任一不合格则一直灰着
   - 提交中【业务逻辑 2】—— WHEN 点了登录 → THEN 按钮转圈，期间不能重复点
   - 登录成功【业务逻辑 3 · 出口】—— WHEN 账号密码核对通过 → THEN 提示「你登录成功，正在跳转...」，进入工作台
   - 登录失败【业务逻辑 4 · 校验】—— WHEN 密码错或用户不存在 → THEN 覆盖层给出原因，卡片上已填内容保留，可以改完重试
   - 切到注册【业务逻辑 6】—— WHEN 点「去注册」 → THEN 注册表单的四个字段被清空

   **业务功能侧**
   - 凭证换令牌【入口 · 业务规则 4】—— WHEN 提交正确的账号密码 → THEN 返回 200 与一对令牌，且两者共享同一个会话标识 `sid`
   - 填不齐就拒绝【业务规则 1 · 校验】—— WHEN 账号或密码为空、账号纯空白、账号超 150 字符 → THEN 返回 400 与对应文案，且**不去查库**
   - 凭证错误统一口径【业务规则 3】—— WHEN 密码错或账号不存在 → THEN 都返回 401「用户名或密码错误」，不透露账号是否存在
   - 公开端点【入口 3】—— WHEN 不带 `Authorization` 头 → THEN 依然受理
   - 路径写法【入口 2】—— WHEN 请求 `POST /api/auth/login`（少尾斜杠）→ THEN 返回 404，不重定向、不改写
   - 只读不写【业务规则 4】—— WHEN 登录成功 → THEN 只读 `auth_user`，不写库、不写 Redis

   > 契约型约束（前后端文案一字不差、响应 DTO 不多不少、拦截器公开端点清单与网关一致、公开端点的 401 不触发刷新）不是业务场景，而是实现约束 —— 由单元层对拍守护，见下面第 3 项。
   >
   > **对应规格**：`openspec/specs/api-path-convention`（路径写法）· `auth-form-validation`（文案与阈值）· `auth-response-shape`（响应 DTO）· `auth-session`（公开端点的 401 不刷新）

2. **接口自动化测试用例** —— 活体接口用例（`tests/api/case/login.yaml`，由 `tests/api/test_login_page.py` 驱动）：

> 已实现用例的逐条「测试目的 / 测试方法与步骤 / 断言逻辑」见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`（编号沿用 `TC-LOGIN-###` / `TC-REG-###` / `TC-REFRESH-###` / `TC-LOGOUT-###` / `TC-ME-###`，已实现 39 条：登录 13 · 注册 14 · 刷新 5 · 登出 4 · me 3）。用例实现细节以上述文档为准。

3. **前端单元层测试用例** 
   1. 代码路径： `frontend/tests/login/`
   2. 简介：—— 11 个 spec / 59 个用例（`cd frontend && npx vitest run tests/login`）；
   3. 逐条用例的测试目的与断言逻辑见 `dev_docs/DEV_TEST/单元测试文档/单元测试-登录.md`（编号 `TC-FE-LOGIN-001` ~ `TC-FE-LOGIN-059`）

4. **业务功能测试用例**
   1. 用例文档： `dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md`
   2. 简介：—— 8 条业务流（登录成功 / 失败重试 / 输入拦截 / 记住账号 / 模式切换 / 注册即登录 / 会话退出 / 令牌失效）+ 20 条输入组合用例（等价类 + 边界值：登录 12 · 注册 8）+ 22 条交互与异常场景（按钮态 / 单击 / 快速连点 / 长按 / 回车 / loading / 覆盖层 / 窄屏）
   3. 编号：`BF-##`（业务流）· `TC-BF-LOGIN-###` · `TC-BF-REG-###` · `TC-BF-UI-###`

5. **端到端测试用例** —— Playwright 真实浏览器（`tests/e2e/test_login_e2e.py`，15 条，编号 `E2E-001` ~ `E2E-015`）：
   1. 代码路径： `tests/e2e/`（运行 `python -m pytest tests/e2e -q`）
   2. 简介：登录成功 / 失败重试 / 按钮态 / 快速连点 / 长按 / loading / 回车 / 记住账号 / 模式切换 / 注册即登录 / 登出 / 路由守卫 / 窄屏；**零密钥** —— 夹具用公开注册端点自建 `e2e_probe` 账号后复用，因此不会静默跳过
   3. 编号与业务用例（`BF-##` / `TC-BF-UI-###` / `TC-SESSION-###`）的映射见 `dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md` 第四节

### 注册

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧**
   - 即时校验【业务逻辑 1 · 校验】—— WHEN 四个字段里任一不合格 → THEN 对应输入框下方给出文案
   - 提交门槛【业务逻辑 1】—— WHEN 四项全过 → THEN 完成注册按钮才亮；否则一直灰着
   - 提交中【业务逻辑 2】—— WHEN 点了完成注册 → THEN 按钮转圈，期间不能重复点
   - 注册成功即登录【业务逻辑 3 · 出口】—— WHEN 账号唯一且格式合法 → THEN 不用再登一次，直接进入工作台
   - 账号被占用【业务逻辑 4 · 校验】—— WHEN 提交的账号已存在 → THEN 提示「用户名已存在」，其余字段保留，换个账号可以立刻重试
   - 切回登录【业务逻辑 5】—— WHEN 点「去登录」 → THEN 清掉刚填的登录密码

   **业务功能侧**
   - 建账号并签发令牌【业务规则 2 · 4】—— WHEN 四个字段格式全过且账号未被占用 → THEN 建账号并直接返回 200 与一对令牌
   - 格式不合格【业务规则 1 · 校验】—— WHEN 账号长度越界、两次密码不一致、邮箱不含 @ → THEN 返回 400 与对应文案
   - 顺序重名【业务规则 3】—— WHEN 用已存在的用户名注册 → THEN 返回 409「用户名已存在」，而不是 500
   - 并发重名【业务规则 3】—— WHEN 两个请求同时抢同一个用户名 → THEN 只有一个成功、另一个拿 409，且先写入者的账号完好
   - 唯一性由库裁定【数据表单】—— WHEN 前置校验通过但写入时撞上唯一约束 → THEN 由写口翻成领域错误再映射成 409（校验层不负责判重）
   - 一次失败不污染其他操作【业务规则 4】—— WHEN 写口因重名失败、而调用方还在一个更大的事务里 → THEN 失败被隔离，调用方后续的写操作照样能跑

   > **对应规格**：`openspec/specs/auth-registration`（用户名唯一性由写口保证）· `auth-response-shape` · `auth-form-validation`

2. **测试用例** —— 活体接口用例（`tests/api/case/register.yaml`，由 `tests/api/test_login_page.py` 驱动）：

> 已实现用例的逐条「测试目的 / 测试方法与步骤 / 断言逻辑」见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`（注册 14 条）。下表是**需求侧的期望口径**，用例实现细节以上述文档为准。

| 编号 | 标题 | 请求 | 期望 |
|---|---|---|---|
| TC-REG-001 | 正常注册 | `POST /api/auth/register/` | `HTTP 200` + schema `register_success` |
| TC-REG-004 | 用户名和密码均为空 | 同上 | `HTTP 400` +「请输入用户名和密码」|
| TC-REG-005 | 用户名为空 | 同上 | `HTTP 400` +「请输入用户名」|
| TC-REG-006 | 密码为空 | 同上 | `HTTP 400` +「请输入密码」|
| TC-REG-007 | 用户名少于 3 字符 | 同上 | `HTTP 400` +「用户名至少 3 个字符」|
| TC-REG-009 | 用户名超过 20 字符 | 同上 | `HTTP 400` +「用户名最多 20 个字符」|
| TC-REG-011 | 两次密码不一致 | 同上 | `HTTP 400` +「两次密码不一致」|
| TC-REG-012 | 邮箱为空 | 同上 | `HTTP 400` +「请输入邮箱」|
| TC-REG-013 | 邮箱格式不正确 | 同上 | `HTTP 400` +「邮箱格式不正确」|
| TC-REG-019 | 密码少于 6 位 | 同上 | `HTTP 400` +「密码至少 6 位」|
| TC-REG-020 | 用户名已存在 | 同上 | `HTTP 409` +「用户名已存在」|

**已实现**（2026-09-20 落地，期望口径如下；逐条测试方法与断言逻辑见上面指向的接口自动化测试文档）：

| 编号 | 标题 | 场景类型 | 期望 | 设计意图 |
|---|---|---|---|---|
| TC-REG-021 | 用户名前后带空格 | 正常 | `HTTP 200` | 后端 strip 后再判重与入库 |
| TC-REG-022 | 邮箱前后带空格 | 正常 | `HTTP 200` | 邮箱同样 strip |
| TC-REG-023 | 并发同名注册 | 异常 | 一个 `200` 一个 `409` | 把「并发也只一个成功」从单测搬到活体层 |

3. **自动化覆盖的测试用例**
   - `tests/api/test_login_page.py` —— 驱动上面 11 条 YAML 用例
   - `tests/graybox/unit/test_register_uniqueness.py` —— `test_sequential_duplicate_returns_409` · `test_duplicate_appearing_at_write_time_returns_409` · `test_write_port_translates_integrity_error` · `test_conflict_does_not_break_caller_transaction` · `test_serializer_does_not_guarantee_uniqueness`
   - `tests/graybox/unit/test_auth_frontend_contract.py` —— `test_token_dto_fields_are_returned_by_both_endpoints`
   - `frontend/tests/login/p0/RegisterCard.spec.ts` · `useAuthFlow.spec.ts`

### 刷新令牌

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。这个功能没有界面，UI交互侧讲的是它在界面背后的行为。

   **UI交互侧（界面上看不到，但决定用户体验）**
   - 无感续期【业务逻辑 1】—— WHEN 访问令牌过期、用户正在用页面 → THEN 自动换新令牌并重发原请求，用户察觉不到中断
   - 并发只刷一次【业务逻辑 2】—— WHEN 多个请求同时遇到 401 → THEN 只触发一次刷新，其余等这一次的结果
   - 公开端点的 401 不刷新【业务逻辑 3】—— WHEN 登录 / 注册 / 刷新自身返回 401 → THEN 不发起刷新（凭证本身就无效，刷了也没用）
   - 刷不动就退出【业务逻辑 4】—— WHEN 刷新也失败 → THEN 清掉本地令牌；还有别的账号就切过去，一个都不剩才跳登录页

   **业务功能侧**
   - 换新访问令牌【业务规则 3】—— WHEN 拿有效的刷新令牌请求 → THEN 返回 200 与新的访问令牌，**不返回新 refresh**
   - 类型必须匹配【业务规则 1】—— WHEN 拿访问令牌冒充刷新令牌 → THEN 返回 401「令牌类型错误，需要刷新令牌」
   - 无效 / 过期 / 已吊销【业务规则 2】—— WHEN 刷新令牌是乱码、已过期，或所属会话已登出 → THEN 返回 401「刷新令牌无效或已过期」
   - 续期不脱离会话【业务规则 3】—— WHEN 续期成功 → THEN 新访问令牌仍带同一个 `sid`，原会话登出后它同样失效
   - 递归保护【业务逻辑 3】—— WHEN 刷新请求自身返回 401 → THEN 不再次刷新（不递归）

   > **对应规格**：`openspec/specs/auth-session`（会话与令牌生命周期）· `auth-response-shape`

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/refresh.yaml`；单请求由 `tests/api/test_auth_tokens.py` 驱动，「登出后再刷新」由 `tests/api/test_auth_session_flow.py` 驱动）：

> 已实现用例的逐条「测试目的 / 测试方法与步骤 / 断言逻辑」见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`。下表是**需求侧的期望口径**，用例实现细节以上述文档为准。

| 编号 | 标题 | 场景类型 | 期望 | 设计意图 |
|---|---|---|---|---|
| TC-REFRESH-001 | 正常续期 | 正常 | `HTTP 200` + `data.access_token` 非空 | 基线 |
| TC-REFRESH-002 | 用访问令牌冒充刷新令牌 | 异常 | `HTTP 401` +「令牌类型错误，需要刷新令牌」| 类型必须匹配 |
| TC-REFRESH-003 | 刷新令牌是乱码 | 异常 | `HTTP 401` +「刷新令牌无效或已过期」| 签名/格式校验 |
| TC-REFRESH-004 | 登出后再刷新 | 异常 | `HTTP 401` +「刷新令牌无效或已过期」| 会话级吊销（登出吊销整个 `sid`）|
| TC-REFRESH-005 | 缺 `refresh_token` 字段 | 异常 | `HTTP 401` | 空令牌走同一拒绝路径 |

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_logout_session_revocation.py` —— `test_session_ids_are_shared_by_the_pair` · `test_refresh_keeps_session_ownership` · `test_verify_token_rejects_revoked_session` · `test_revocation_ttl_covers_refresh_lifetime`
   - `tests/graybox/unit/test_auth_endpoint_declaration.py` —— `test_public_endpoint_pairs_allow_any_with_empty_authentication`（刷新属公开端点）
   - `tests/graybox/unit/test_auth_frontend_contract.py` —— `test_refresh_dto_fields_are_returned_by_refresh`
   - `frontend/tests/login/p0/apiAuthInterceptors.spec.ts` —— 401 续期、公开端点不刷新、并发刷新锁、刷新失败清令牌

### 登出

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧（登出口在侧栏，不在登录页）**
   - 从侧栏登出【模版 · 业务逻辑 1】—— WHEN 点侧栏账号区的登出 → THEN 调一次登出接口
   - 还有别的账号【业务逻辑 2】—— WHEN 登出后本地还存着其他账号 → THEN 自动切到剩下的账号并重载页面，不回登录页
   - 只剩一个账号【业务逻辑 2】—— WHEN 登出的是最后一个账号 → THEN 回到登录页
   - 登出被拒【业务逻辑 3】—— WHEN 后端返回 503 + `retry`（Redis 不可用）→ THEN 提示「服务暂时异常，请稍后重试」并**保留登录态**，用户不用重新登
   - 其它失败【业务逻辑 4】—— WHEN 网络异常或令牌已失效 → THEN 仍清掉本地登录态，不让用户卡在失效会话里

   **业务功能侧**
   - 整个会话作废【业务规则 2】—— WHEN 用一次登录签发的访问令牌登出 → THEN 该会话的访问与刷新令牌**一起**失效，不只是当前这一个
   - 登出后旧令牌不可用【业务规则 2】—— WHEN 登出后再用原访问令牌请求受保护端点，或用原刷新令牌续期 → THEN 都返回 401
   - 其它会话不受影响【业务规则 2】—— WHEN 同一账号在两处登录（两个不同的 `sid`），其中一处登出 → THEN 另一处仍然有效
   - 老令牌兜底【业务规则 3】—— WHEN 令牌没有 `sid`（历史令牌）→ THEN 按 `jti` 单独吊销，且校验端不因缺 `sid` 报错
   - 写不进就拒绝【业务规则 4】—— WHEN Redis 不可用、吊销记录写不进去 → THEN 返回 503 + `retry`，绝不假装成功
   - 没带令牌【业务规则 5】—— WHEN 请求没带 `Authorization` 头 → THEN 网关中间件直接返回 401「请先登录」，请求到不了视图

   > **对应规格**：`openspec/specs/auth-session`（登出作废整个会话）

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/logout.yaml`；单请求由 `tests/api/test_auth_tokens.py` 驱动，登出后的两条由 `tests/api/test_auth_session_flow.py` 驱动）：

> 已实现用例的逐条「测试目的 / 测试方法与步骤 / 断言逻辑」见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`。下表是**需求侧的期望口径**，用例实现细节以上述文档为准。

| 编号 | 标题 | 场景类型 | 期望 |
|---|---|---|---|
| TC-LOGOUT-001 | 正常登出 | 正常 | `HTTP 200` + `data = {}` |
| TC-LOGOUT-002 | 登出后再用原 access 请求 `/me/` | 异常 | `HTTP 401` |
| TC-LOGOUT-003 | 登出后再用原 refresh 刷新 | 异常 | `HTTP 401` |
| TC-LOGOUT-004 | 未带 Authorization 头登出 | 异常 | `HTTP 401` +「请先登录」（网关中间件拦下，不经视图） |
| TC-LOGOUT-005 | 停掉 Redis 后登出 | 异常 | `HTTP 503` + `retry = true`，且本地登录态保留 —— **接口层未落地**（需停全局 Redis）；fail-closed 行为由灰盒单元用例 `tests/graybox/unit/test_logout_session_revocation.py` 覆盖 |

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_logout_session_revocation.py`（9 个，缺 Redis 的用例会真实连 Redis）—— `test_session_ids_are_shared_by_the_pair` · `test_logout_kills_refresh_token` · `test_logout_kills_access_token` · `test_refresh_keeps_session_ownership` · `test_other_session_is_unaffected` · `test_logout_fails_closed_when_redis_unavailable` · `test_legacy_token_without_sid_still_logs_out` · `test_verify_token_rejects_revoked_session` · `test_revocation_ttl_covers_refresh_lifetime`
   - `tests/graybox/unit/test_auth_endpoint_declaration.py` —— `test_protected_endpoint_pairs_non_public_with_authentication`
   - `frontend/tests/login/p0/token-storage.spec.ts` —— 单账号会话的读写、覆盖与清空

### 查看当前身份

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧（没有自己的界面，行为落在别的页面上）**
   - 管理入口可见性【模版 · 业务逻辑 1】—— WHEN 当前账号是管理员 → THEN 工具调试这类管理入口可见；不是管理员则不可见
   - 拉取失败不报错【业务逻辑 2】—— WHEN 身份请求失败 → THEN 按「不是管理员」处理，页面不弹错
   - 全局只拉一次【业务逻辑 2】—— WHEN 多个页面都需要身份 → THEN 只请求一次并共享结果

   **业务功能侧**
   - 读身份【业务规则 1 · 4】—— WHEN 带有效令牌请求 → THEN 返回 200 与 `user: {id, username, is_superuser}`，且**只读**、不改任何数据
   - 没带令牌【业务规则 2】—— WHEN 不带令牌 → THEN 返回 401
   - 登出之后【业务规则 2】—— WHEN 令牌已被登出作废 → THEN 返回 401
   - 账号已删【业务规则 3】—— WHEN 令牌有效但账号已被删除 → THEN 返回 404，而不是 500

   > **对应规格**：`openspec/specs/auth-response-shape`（身份接口 DTO 与响应一致）· `auth-session`

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/me.yaml`；单请求由 `tests/api/test_auth_tokens.py` 驱动，「登出后再读」由 `tests/api/test_auth_session_flow.py` 驱动）：

> 已实现用例的逐条「测试目的 / 测试方法与步骤 / 断言逻辑」见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`。下表是**需求侧的期望口径**，用例实现细节以上述文档为准。

| 编号 | 标题 | 场景类型 | 期望 |
|---|---|---|---|
| TC-ME-001 | 正常读取身份 | 正常 | `HTTP 200` + `data.user` 含 `id` / `username` / `is_superuser` |
| TC-ME-002 | 不带令牌 | 异常 | `HTTP 401` |
| TC-ME-003 | 登出后再读 | 异常 | `HTTP 401` |
| TC-ME-004 | 令牌有效但账号已删 | 异常 | `HTTP 404` —— **接口层未落地**（需删库，属集成层 `django_db`）|

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_auth_frontend_contract.py` —— `test_me_dto_fields_match_me_response_user`
   - `tests/graybox/unit/test_auth_endpoint_declaration.py` —— `test_protected_endpoint_pairs_non_public_with_authentication`
   - `tests/graybox/unit/test_logout_session_revocation.py` —— `test_logout_kills_access_token`（用 `me` 作受保护端点验证）

### 会话与账号管理

1. **业务场景** —— 从功能出发，覆盖 UI交互 与 业务功能两侧；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧**
   - 未登录守卫【业务逻辑 1】—— WHEN 没有令牌时访问任何页面 → THEN 一律跳回 `/login`
   - 已登录免登【业务逻辑 2】—— WHEN 已有令牌时访问 `/login` → THEN 直接跳 `/dashboard`
   - 无添加账号例外【业务逻辑 2】—— WHEN 已有令牌时访问 `/login?add=1` → THEN 同样跳 `/dashboard`，不呈现任何「添加账号」界面
   - 账号名只读【模版 1】—— WHEN 点击侧栏底部的当前账号名 → THEN 不展开账号列表
   - 单账号覆盖【业务逻辑 3】—— WHEN 先登 A 再登 B → THEN 本地只保留 B 的会话
   - 登出即回登录页【业务逻辑 5】—— WHEN 点侧栏「退出」 → THEN 清空会话并回 `/login`

   **业务功能侧（这一节不新增端点，约束落在鉴权姿态与本地存储上）**
   - 公开端点两者成对【API契约 · 鉴权姿态】—— WHEN 检查 login / register / refresh → THEN 权限是「允许任何人」**且**鉴权类为空列表
   - 受保护端点两者成对【API契约 · 鉴权姿态】—— WHEN 检查 logout / me → THEN 权限不含「允许任何人」**且**鉴权类非空
   - 没有中间态【API契约 · 鉴权姿态】—— WHEN 遍历 `apps/accounts` 的全部 APIView → THEN 每个都满足上述不变量
   - 公开端点清单一致【API契约】—— WHEN 比较前端拦截器声明的公开端点与网关公开路径清单中的 `/api/auth/*` → THEN 两者相同
   - 会话只有一个读写点【数据表单】—— WHEN api-client 与页面都要读写会话 → THEN 都走 `shared/auth/token-storage.ts`，不各写各的
   - 一次只保留一个账号【数据表单】—— WHEN 连续登录两个账号 → THEN 本地只留下后一个，且不存在账号列表结构
   - 续期失败一律跳登录【出口】—— WHEN 续期请求失败 → THEN 清空会话并跳 `/login`，不因「还有备用账号」而停留

   > **对应规格**：`openspec/specs/auth-session`（认证端点显式声明鉴权姿态）· `api-path-convention`

2. **测试用例** —— 端到端用例**部分落地**（2026-09-20）：守卫与登出三条已由 `tests/e2e/test_login_e2e.py` 覆盖 —— TC-SESSION-001 → `E2E-013` · TC-SESSION-002 → `E2E-014` · TC-SESSION-007 → `E2E-012`；多账号相关条目（TC-SESSION-003~006）已随本次变更**作废**，其余仍按下表设计（令牌生命周期需要环境编排）：

| 编号 | 标题 | 场景类型 | 期望 |
|---|---|---|---|
| TC-SESSION-001 | 未登录访问 `/dashboard` | 正常（守卫） | 跳转 `/login` |
| TC-SESSION-002 | 已登录访问 `/login` | 正常 | 跳转 `/dashboard` |
| ~~TC-SESSION-003~~ | ~~已登录访问 `/login?add`~~ | — | **已作废**（移除多账号后没有「添加账号」入口） |
| ~~TC-SESSION-004~~ | ~~添加第二个账号~~ | — | **已作废**（单账号会话为覆盖写入） |
| ~~TC-SESSION-005~~ | ~~切换到第二个账号~~ | — | **已作废**（不再提供账号切换） |
| ~~TC-SESSION-006~~ | ~~登出其中一个账号~~ | — | **已作废**（登出即清空会话并回登录页） |
| TC-SESSION-007 | 登出最后一个账号 | 正常 | 回到登录页 |
| TC-SESSION-008 | 后端 503 时登出 | 异常 | 提示重试且**保留**登录态 |
| TC-SESSION-009 | 访问令牌过期后访问受保护端点 | 异常 | 自动续期并重发，用户无感 |
| TC-SESSION-010 | 刷新令牌也失效 | 异常 | 清本地令牌并回登录页 |

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_auth_endpoint_declaration.py` —— 4 个（鉴权姿态不变量）
   - `frontend/tests/login/p0/token-storage.spec.ts` —— 单账号会话的读写、覆盖与清空
   - `frontend/tests/login/p0/apiAuthInterceptors.spec.ts` —— 401 续期 / 公开端点不刷新 / 并发锁 / 刷新失败清令牌
   - `frontend/tests/login/p0/useSavedUsername.spec.ts` —— 记住账号
   - **缺口：路由守卫（`router.ts`）目前没有任何测试。**

### 怎么跑这些测试

```
python -m pytest tests/graybox/unit -q              # 单元层（零依赖，读源码对拍契约）
python -m pytest tests/api -q                       # 接口层全量（需后端 :8766 已启动；64 条）
python -m pytest tests/api/test_login_page.py tests/api/test_auth_tokens.py -q   # 登录模块接口用例（单请求 38 条）
cd frontend && node tests/run.mjs module login      # 前端登录模块（11 个文件 / 57 个用例，仅终端输出）
cd frontend && node tests/run.mjs html tests/login   # 前端登录模块 + HTML 报告（tests/reports/html/index.html）
python -m pytest tests/e2e -q                        # 端到端层（需前后端都已启动；15 条，无需任何密钥）
python -m pytest tests/e2e --html=tests/reports/e2e.html --self-contained-html   # 端到端层 + pytest-html 报告
```

> 端到端层跑完会**自动**生成步骤报告 `tests/reports/e2e/index.html`（含带标注的过程截图，图片已压缩并在报告里缩放显示）；不需额外参数，成败都会落盘。

> 前端报告产物（HTML / JUnit / JSON）与逐条用例清单：`dev_docs/DEV_TEST/单元测试文档/单元测试-登录.md`；报告目录 `frontend/tests/reports/` 已在 `.gitignore:66`，属可随时重新生成的产物。端到端报告 `tests/reports/e2e.html` 同理（`tests/reports/` 已 gitignore）。

> `tests/graybox/unit/test_logout_session_revocation.py` 需要**真实的 Redis**：Redis 未启动时其中 6 个用例会失败（`Error 10061 connecting to localhost:6379`），失败的正好是需要写吊销键的那些；`test_logout_fails_closed_when_redis_unavailable` 反而会通过 —— 它断言的正是 Redis 不可用时返回 503。

---

## 附录：已知缺口

1. **刷新 / 登出 / me 的活体接口用例已于 2026-09-20 落地** —— `tests/api/case/` 新增 `refresh.yaml` / `logout.yaml` / `me.yaml`，登录模块接口用例共 **39 条**（逐条见 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`）。仍未落地的只剩两条：TC-LOGOUT-005（需停 Redis，行为已由灰盒单测覆盖）与 TC-ME-004（需删库，属集成层）。
2. **端到端层已由 0 条变为 15 条**（2026-09-20，Playwright）—— 覆盖登录页交互、路由守卫与登出，不再依赖 `TEST_ADMIN_PASSWORD`（夹具自建 `e2e_probe` 账号复用），原「静默跳过」的假守护随之解掉。**路由守卫不再是缺口**：`router.ts:30-39` 的两条重定向规则由 `E2E-013` / `E2E-014` 覆盖。移除多账号后 `E2E-009` 不再依赖 `/login?add=1` 例外（改为「登出后重开登录页」验证预填），`E2E-012` 断言改为单账号会话键被清空。仍未落地：TC-SESSION-008~010（503 登出、令牌续期与失效）与 TC-BF-UI-016/019/021（停后端、多标签页、限速）—— 都需要环境编排。
3. **接口文档有一处口径与代码相反** —— `dev_docs/DEV_TEST/接口文档/API-登录.md:18` 写「路径无尾斜杠」，与 `apps/accounts/urls.py`、`apps/accounts/AGENTS.md`、`test_api_path_convention.py` 及四份兄弟接口文档都相反。本 PRD 以**代码**为准。
4. **登录端点没有任何防爆破限流（代码审查 P1 · 2026-09-21 登记，暂不修改）** —— `POST /api/auth/login/` 可被无限次试密码：`LoginView` 未配 `throttle_classes`（`apps/accounts/views.py:26-55`），全局 `REST_FRAMEWORK` 无 `DEFAULT_THROTTLE_CLASSES`（`config/settings.py:284-298`），全仓也不存在 `django-axes` 或入口 `limit_req` 一类设施（grep `throttl|ratelimit|limit_req` 零命中）。**这与防枚举是两件事**：登录侧的「凭证错误统一口径【业务规则 3】」只保证「不透露账号是否存在」，并不限制尝试次数。**本次决定**：暂不修改，只登记为已知缺口；**若要收口**，加 DRF `AnonRateThrottle`（按 IP + 用户名双键）或入口限流即可，属纯配置改动，不动接口契约与响应形状。注意勿与 `TC-BF-UI-021` 混淆 —— 那条（`dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md:121`）测的是慢网络下的前端 loading 行为，不是登录频率限制。
