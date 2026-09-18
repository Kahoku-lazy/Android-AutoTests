## 1. 变更与骨架

- [x] 1.1 `openspec/changes/add-login-backend-map/` 四件套（proposal / tasks / design / .openspec.yaml，`skip_specs: true`）
- [x] 1.2 `openspec validate add-login-backend-map` 通过 —— `Change ... is valid`
- [x] 1.3 按用户要求**移除「页面 ↔ 功能 join」**：不解析前端 `REGIONS`、不做端点↔页面归属；受管文件由 17 降为 16

## 2. 采集器（Python 侧）

- [x] 2.1 静态内省：路由表 / DRF 范式 / 视图定义行号 / `MIDDLEWARE` 链 / `PUBLIC_PREFIXES` / `api.__all__` / 表归属
- [x] 2.2 **模型层**：自有表（实测 0 张）、借用表 `auth_user`（归属 `auth`）、表的读点与写点、迁移数、全平台 App×表对照
- [x] 2.3 **模板层**：① Django 模板渲染的**机械判定**（`render(request` / `TemplateResponse` / `render_to_string` / `get_template(` 全域扫描，并按「是否落在注释/文档串内」分类为 `realCall`）② 三个校验器的字段与各自文案（按类源码抽取，不串味）③ 信封渲染器位置
- [x] 2.4 实测组 A（信任）：无令牌 / 有效令牌 / 登出后 access / 登出后 refresh —— 记录实际状态码与响应体
- [x] 2.5 实测组 B（契约）：登录成功形状、错误密码 401、空值 400、重名注册 409、**尾斜杠 404 对照**
- [x] 2.6 实测组 C（开销与兜底）：`verify_token` 调用计数、SQL 计数（DRF vs 裸 view）；`api.create_user` 重复调用是否上抛 `IntegrityError`
- [x] 2.7 输出 stdout 带标记 JSON；pytest 用 `config.test_settings` + `django_db` 事务回滚

## 3. 生成器与模板（Node 侧）

- [x] 3.1 `login-backend-map.cjs`：调采集 → 渲染 → 写自包含 HTML；页头展示指纹与受管文件数
- [x] 3.2 内嵌 `<script type="application/json" id="backend-map-provenance">`（`<` 转义 `\u003c`）
- [x] 3.3 `SOURCE_FILES`（后端 13）+ `OWN_FILES`（3）→ `TRACKED`（16）；`fingerprint()` / `digestOf()`
- [x] 3.4 `--check`：在**任何 Python 子进程之前**返回；已同步 exit 0；内容变更 / HTML 缺失 / 无指纹 三种失败路径各自 exit 1 并点名
- [x] 3.5 模板七节版式：**A** 分层总览（M/T/V + X 横切，含填充度条）· **B** 模型层 · **C** 模板层 · **D** 视图层（路由表 + 错误码映射 + 流水线）· **E** 端点实测 · **F** 横切面（信任时间轴 + 运行面）· **G** 图例索引
- [x] 3.6 顶部加「关于『模版』这一层」澄清块：说明 Django 模板在本工程为空、本图的模板层指 DRF 的 Serializer + Renderer

## 4. 自检器

- [x] 4.1 断言三层骨架齐备：A 节层符号序列 == `MTVX`
- [x] 4.2 断言 HTML 中每个计数/状态码等于实测值（自有表数 / 中间件数 / 公开前缀数 / 端点实测数 / verify 次数 / SQL 条数 / 断点 200 / 401 / 404 / IntegrityError）
- [x] 4.3 断言模板层结论由**机械判定**得出：`real-render-count` == `realCall` 命中数
- [x] 4.4 断言三个校验器的全部 16 条文案原样出现；无 U+FFFD
- [x] 4.5 断言 5 条路由全部出现在 D 节路由表；每条 `file:line` 存在且行号在范围内
- [x] 4.6 输出 `{report, errs}`，`errs` 非空则 exit 1；null 位置**显式登记**在 `report.skippedLocations` 而非静默跳过

## 5. 文档与验证

- [x] 5.1 `README.md`：受管清单（16）、命令、七节内容、实测口径、已知边界
- [x] 5.2 生成 → `--check` exit 0（指纹 `366dba37cfe5`）→ `verify` errs `[]`
- [x] 5.3 反向验证：追加漂移 → exit 1 且点名 `apps/accounts/api.py`；`git checkout` 还原 → exit 0
- [x] 5.4 浏览器实拍：0 console error、0 未替换占位符、页高 10793px，A–G 分节截图齐备

## 6. 实施期发现并修掉的缺陷

- [x] 6.1 `POST /api/auth/login/`（带尾斜杠）实测 **404** —— `accounts` 用无斜杠约定，而 `NormalizeTrailingSlashMiddleware` 只处理反方向；已作为 D 节实测对照展示
- [x] 6.2 `core.autocrlf=true` 下 `git checkout` / `git stash` 会在 LF/CRLF 间重写工作区文件，字节变了但 git 仍 clean —— 逐字节指纹会被这种无意义翻动判成过期。改为**行尾归一后哈希**；前端地图 `login-layer-map.cjs` 有同一缺陷，未在本变更修改，登记为 Open Question
- [x] 6.3 Python stdout 在 Windows 下默认 cp936，Node 按 UTF-8 解码 → E 节中文实测文案全部损坏**而状态码看起来正常**（假绿）。已修采集器并新增「实测文案必须原样进 HTML」+「无 U+FFFD」断言
- [x] 6.4 校验器文案抽取最初按**整文件**扫描，导致三个校验器拿到同一批 16 条文案；改为按类源码抽取（`inspect.getsource`）后为 6 / 10 / 0
- [x] 6.5 `RefreshSerializer` 没有自定义 `validate()`，原实现报出 `null:null` 位置；改为显示「无自定义 validate()」，自检器只对确有 `validate` 的收集位置
- [x] 6.6 采集时撞见 drf-spectacular 告警：`element_locator` 的 `batch-move` 与 `batch-move/` 产生 operationId 冲突（该 App 同时注册了带/不带斜杠两条路由）—— 与本变更无关，仅记录
## 7. 交付后被三处修复带动同步（跨变更记录）

本产物按「受管文件变更即过期」的规则运行（`--check` 每次都会点名变化的源文件），
因此在另外三个变更修完后各重跑一次。每次重跑都让图中的结论跟随实测值变化，而不是留下过期表述：

- `2026-09-17-revoke-session-on-logout` —— F 节由「实测到一处结构断点」变为「**会话级吊销：实测已闭合**」；
  时间轴末步由「⚠ 断点」变为「会话已作废」；图例补 `revoke_session()` / `session_id_of()` / `_is_revoked()`
- `2026-09-17-fix-register-duplicate-race` —— B 节「重名防护位置」由「`serializer.validate`（check-then-act）；
  写口本身无兜底」变为「写口（数据库唯一约束 → `ConflictError` → 视图 409）；校验层不判重」；
  **表的读点由 2 处降为 1 处**（serializer 的判重读消失）
- `2026-09-17-normalize-trailing-slash-both-ways` —— D 节由「调用方必须写无斜杠」变为「网关**双向**容错」；
  错误码表中 login 的 `404 带尾斜杠` 行随实测消失

结论：本产物的叙述已全部**数据驱动**（条件分支取决于实测状态码与异常类型），
同一条代码路径在修复前后都能得到诚实表述；全文陈旧标识符审计残留为 0。

归档时的最终指纹：`38364b89fc87`（16 个受管文件），`--check` exit 0，`verify` errs `[]`。
