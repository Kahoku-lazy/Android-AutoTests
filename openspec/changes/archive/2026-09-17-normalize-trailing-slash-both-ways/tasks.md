## 1. 变更与规格

- [x] 1.1 `openspec/changes/normalize-trailing-slash-both-ways/` 四件套
- [x] 1.2 新能力规格 `specs/api-path-normalization/spec.md`（5 个 Scenario）
- [x] 1.3 `openspec validate normalize-trailing-slash-both-ways` 通过 —— `Change 'normalize-trailing-slash-both-ways' is valid`

## 2. 中间件（gateway/normalize_slash.py）

- [x] 2.1 抽出 `_resolves(resolver, path)` 辅助函数
- [x] 2.2 补反方向：带斜杠 + 无斜杠版可解析 → 去斜杠
- [x] 2.3 保序：**原路径可解析则一律不改写**（保 ``batch-move`` 与 ``batch-move/`` 并存场景的语义）
- [x] 2.4 更新模块 docstring，说明双向与"只在解析失败时改写"

## 3. 测试

- [x] 3.1 新增 `tests/graybox/unit/test_trailing_slash_tolerance.py`（该中间件此前零覆盖） —— 此前 `tests/` 下搜 `NormalizeTrailingSlash` 零命中
- [x] 3.2 集成：带斜杠调用无斜杠路由命中（login/ 与 me/）；无斜杠调用带斜杠路由命中（stats） —— `/api/auth/me/` 与 `POST /api/auth/login/` 由 404 变命中；`/api/dashboard/stats` 仍 200
- [x] 3.3 单元（stub resolver）：原路径可解析时不改写 / 两种形式都不存在时不改写 / 非 /api 前缀不改写 —— 用 stub resolver 精确断言 path_info 未被改写
- [x] 3.4 回归：`/api/no-such-route` 与其带斜杠形式仍为 404 —— `/api/no-such-route` 与其带斜杠形式仍 404

## 4. 证据产物与门禁

- [x] 4.1 重跑 `temps/login-backend-map`：D 节尾斜杠实测由 404 变为命中；`--check` exit 0、verify errs `[]` —— D 节由「带斜杠 → 404，调用方必须写无斜杠」变为「双向容错」；指纹 `8bdad3f2c1d9`，`--check` exit 0，verify errs []
- [x] 4.2 `python manage.py check` / `ruff check` / `ruff format --check` / `gen_arch_stats.py --check-boundaries` —— check / ruff / format / 边界检查全部通过
- [x] 4.3 `pytest -m auth -q` 与 `pytest tests/arch -q` 无回归 —— `tests/arch` 34 passed；**全量灰盒单测 278 passed**（网关级改动跑了完整回归面）
- [x] 4.4 归档并把 delta 同步进 `openspec/specs/api-path-normalization/spec.md`
## 5. 实施期补记

- [x] 5.1 基线探针第一次写错：受保护路径在未鉴权时被 JWT 中间件**先于路由解析**拦成 401，无法区分「命中」与「未解析」。改用真实令牌后才拿到有区分力的矩阵 —— 这条也写进了测试文件的注释，避免后人重踩
- [x] 5.2 实测双向矩阵（修复前 → 修复后）：`POST /api/auth/login/` 404 → 400；`GET /api/auth/me/` 404 → 200；`GET /api/dashboard/stats` 200 → 200（原方向未回归）；`/api/no-such-route(/?)` 404 → 404（保持）
- [x] 5.3 证据产物的 D 节尾斜杠结论改为**数据驱动**（实测 404 时呈现旧警告，否则呈现双向容错结论）
- [x] 5.4 顺带发现（登记为 Open Question，不在本变更处理）：平台路径约定在各 App 之间乃至 App 内混用，`element_locator` 同时注册了 `batch-move` 与 `batch-move/`
