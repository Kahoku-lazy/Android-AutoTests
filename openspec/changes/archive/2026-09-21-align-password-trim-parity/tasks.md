## 1. 修正误导注释

- [x] 1.1 改 `frontend/src/views/composables/useAuthFlow.ts` 的密码注释：删除「与 LoginSerializer / authenticate 一致」这一与事实相反的等价声明，改为陈述真实分工 —— 前端不自行去除密码、首尾空白由接口统一负责、与注册侧最终口径一致。验证：`cd frontend && npx eslint src/views/composables/useAuthFlow.ts` 零告警，并通读该行确认不再出现「与后端一致」式表述。

## 2. 补守护（零依赖默认单测）

- [x] 2.1 在 `tests/graybox/unit/test_auth_validation_parity.py` 增**后端侧行为断言**：import `LoginSerializer` / `RegisterSerializer`，断言 ① 登录密码字段的首尾空白去除为开启、账号字段为关闭；② 登录密码字段对 `'  abc123  '` 返回 `'abc123'`，对含内部制表符与换行的输入原样保留；③ 注册校验对带首尾空白的密码产出已去空白值。验证：`python -m pytest tests/graybox/unit/test_auth_validation_parity.py -q` 全绿，且该用例不连数据库、不连 Redis。
- [x] 2.2 同一文件增**前端侧读源码断言**：登录出口不自行去除密码、注册出口会去除；沿用既有「提取量下限」做法（提取不足即判失败，避免两个空集合互比通过）。验证：同上命令全绿；临时删掉注册出口的去除应使该用例失败（验证后还原）。
- [x] 2.3 反向验证守护有效性：临时把登录密码字段改成不去除首尾空白，确认守护**失败**且错误信息同时列出两侧口径；随后还原并复跑。验证：`python -m pytest tests/graybox/unit/test_auth_validation_parity.py -q` 先红后绿，`ruff check tests/graybox/unit/test_auth_validation_parity.py` 零告警。

## 3. 一致性与关单

- [x] 3.1 逐条对齐规格与实现：新要求的 6 个场景各自落到 `tests/graybox/unit/test_auth_validation_parity.py`（前两条、第五条）与既有 `tests/api/case/{login,register}.yaml`（TC-LOGIN-015 对应「账号口径有意不同」、TC-LOGIN-016 对应「首尾空白被去掉」、TC-REG-021/022 对应注册侧去除）；无对应断言的场景需在规格或任务里说明原因。验证：`openspec validate "align-password-trim-parity"` 通过 + 逐条对照记录。
- [x] 3.2 核对「零行为改动」边界：改动清单只应包含 `openspec/changes/align-password-trim-parity/`（本变更产物）、`dev_docs/ARCH_PRD/PRD-00-登录模块.md`（§数据表单 密码行，立单前已改）、`frontend/src/views/composables/useAuthFlow.ts`（仅注释）、`tests/graybox/unit/test_auth_validation_parity.py`；`apps/`、`tests/api/`、`tests/e2e/`、`frontend/src` 其余文件必须零改动。验证：`git status --porcelain` 逐行核对（注意 PRD-00 登录模块与 ARCH 文档目前是未跟踪文件，不出现在 `git diff` 中，需按内容核对）。
- [x] 3.3 关单门禁：`python -m pytest tests/graybox/unit -q` 全绿（`test_logout_session_revocation.py` 中依赖真实 Redis 的用例在 Redis 未启动时失败属既有环境例外，见 PRD 附录说明，不得因此放过本变更引入的新失败）。验证：命令输出与改动前对比，失败集合无新增。

### 规格场景 → 断言 对照（3.1 记录）

| 规格场景 | 断言出处 |
|---|---|
| 密码首尾空白在两侧都被去掉 | 灰盒 `test_backend_login_password_strips_surrounding_whitespace` · `test_backend_register_strips_password_surrounding_whitespace`；活体 TC-LOGIN-016（200） |
| 密码内部的空白保留 | 灰盒 `test_backend_password_inner_whitespace_is_kept` |
| 账号的空白口径有意不同 | 灰盒 `test_backend_trim_stance_is_declared_per_field` · `test_backend_login_username_is_kept_as_typed`；活体 TC-LOGIN-015（401） |
| 口径漂移必须失败 | 反向验证（2.3）：后端给登录密码字段加 `trim_whitespace=False` → 2 条变红，输出「口径漂移：期望 密码=True / 账号=False，实际 密码=False / 账号=False」；前端删掉注册出口的 `.trim()` → `test_frontend_register_export_trims_password` 变红。两处均已还原 |
| 守护测试不依赖运行中的服务 | 落在 `tests/graybox/unit` 默认套件内（3.3 全量跑 289 passed；唯二报错的文件是 `test_env_loader.py` / `test_kb_files.py` 的沙箱权限错误，与本文件无关） |
| 该口径对外只表现为成功与失败 | 活体 TC-LOGIN-016（200 + 令牌对）· TC-LOGIN-015（401「用户名或密码错误」）；灰盒层不涉及响应形状，故不重复断言 |
