## 1. 守护重构（先跑红）

- [x] 1.1 新增 `tests/graybox/unit/test_api_path_callers.py`：按调用形态跨行扫描，覆盖四个面
      （`frontend/src`、`tests/**/*.py`、`tests/api/case/*.yaml` 的 `path:`、`tools/seed_api_endpoints.py`），
      建立 `(文件, 字面量, 理由)` 显式例外清单，并按面登记规模下限。
  **验证**：`python -m pytest tests/graybox/unit/test_api_path_callers.py -v` —— 预期**红**，且失败项**只含**
  `tests/api/conftest.py:34` 那一条（`test_api_path_convention.py` 的负向用例应被例外清单吸收）。
- [x] 1.2 删除 `tests/graybox/unit/test_frontend_api_paths.py`，断言全部迁入 1.1。
  **验证**：`python -m pytest tests/graybox/unit/test_api_path_callers.py tests/graybox/unit/test_auth_endpoint_declaration.py -v`
  收集到的测试名覆盖旧模块的 5 条（扫描量自检、认证链路覆盖、尾斜杠、resolve、认证链路视图）与
  `test_auth_endpoint_declaration.py` 的 7 条，一条不少。

## 2. 修正测试夹具

- [x] 2.1 `tests/api/conftest.py` 的 `auth_session` 登录路径补尾斜杠。
  **验证**：1.1 的守护转绿（`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 无失败）。
- [x] 2.2 `tests/api` 的鉴权夹具恢复可用（需后端在跑）。
  **验证**：`python -m pytest tests/api/test_devices.py tests/api/test_inspector.py -q` 不再出现 `assert 404 == 200`；
  且 `python -m pytest tests/api -q` 无 ERROR（既有失败项若与本夹具无关，须在结论中逐条注明）。

## 3. 文档同步

- [x] 3.1 更新 `tests/AGENTS.md` §契约对拍测试：文件名改为 `test_api_path_callers.py`，覆盖范围从"前端"扩为四个调用面，
      并写明例外清单与规模下限两条机制的用途。
  **验证**：该节内容与 1.1 的实现一致（文件名、四个面、机制描述均能对上）。

## 4. 门禁

- [x] 4.1 单元与架构测试全绿。
  **验证**：`python -m pytest tests/graybox/unit tests/arch -q`（基线 319 passed，±本变更的模块增删）。
- [x] 4.2 架构红线零违规。
  **验证**：`python tools/gen_arch_stats.py --check-boundaries`（基线零违规）。
- [x] 4.3 新增与修改的测试文件静态检查通过。
  **验证**：`python -m ruff check` 与 `python -m ruff format --check` 对 `tests/graybox/unit/test_api_path_callers.py`、
  `tests/api/conftest.py` 均无输出。
- [x] 4.4 前端类型检查不引入新错误。
  **验证**：`cd frontend && npx vue-tsc --noEmit` 的错误数不超过既有基线 30 条（本变更不改前端产品代码）。
