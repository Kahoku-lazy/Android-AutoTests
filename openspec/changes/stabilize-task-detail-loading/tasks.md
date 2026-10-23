## 1. 报告接口瘦身

- [x] 1.1 `backend/apps/task_list/task_reports.py`：新增轻量行对象与两段取数——主查询用 `.values_list()` 只取分组 5 列，`_spans` 切段后只对每段第一行回查展示/阶段/明细；`_grouped` 改为复用 `_spans`，输出不变。验证：`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py tests/api/test_task_api_paths.py -q` 全绿。**验证结果**：21 passed。
- [x] 1.2 增量事件不读 `payload`：回查用 `Case(When(is_delta=False, then=payload))` 置空增量载荷；`_detail` / `_conclusion` / `_verdict_maps` 所需字段全部来自非增量代表行。验证：`tests/api/test_task_event_flow.py::test_delta_events_load_without_payload` 通过，且变更前后同一任务的 `rounds` / `cases` / `conclusion` 逐字段一致（任务 139、141 对比）。**验证结果**：新增用例通过；对比脚本输出 `task 139: identical=True`、`task 141: identical=True`（输出字节数也一致）。
- [x] 1.3 复测基线：对任务 141 运行 `python temps/probe_task_report.py`，记录三次耗时与响应体积，确认服务端聚合 < 4 秒且未压缩体积明显下降。验证：脚本输出。**验证结果**：2.36s / 2.57s / 2.50s（变更前 10.18s / 10.37s / 10.50s）；未压缩 8.69 MB（gzip 后约 1.05 MB，与变更前一致）。

## 2. 开发代理容错

- [x] 2.1 `frontend/vite.config.js`：为 `/api`、`/media` 的 proxy 配置加 `configure(proxy)`，在 `error` 事件里对未开始写出的 `ServerResponse` 返回 `503` + `{status: false, message: "后端服务未就绪（可能正在重启），请稍后重试"}`；`res` 非 `ServerResponse`（WS）或已写出时跳过。验证：`npx vitest run tests/shared/p0/proxyFallback.spec.js` 断言 503/JSON 与重复写保护。**验证结果**：`npx vitest run tests/shared/p0/proxyFallback.spec.js` 3 passed（503/JSON、已写出不重写、WS socket 跳过）。
- [x] 2.2 端到端验证：后端不可用时浏览器请求 `/api/tasks/141/report/` 得到 503 与可读 message；后端恢复后原 200 不变。验证：抓包或页面 `ErrorState` 文案。**验证结果**：用临时 Vite（端口 5199、上游 `127.0.0.1:9`）实测 `HTTP/1.1 503` + `{"status":false,"message":"后端服务未就绪（可能正在重启），请稍后重试"}`；真实 5173 服务配置重载后 `/api/devices/` 401、`/` 200，行为未变。

## 3. 门禁与规格

- [x] 3.1 静态检查：`ruff check` 与 `ruff format --check` 覆盖改动文件；前端 `npm run build:check`（或等价 lint）通过。验证：命令退出码 0。**验证结果**：`ruff check` 与 `ruff format --check` 全过；`python run.py check` 中 vue-tsc / vite-build / eslint / vitest 均 PASS。唯一失败项 `prettier-ts` 命中 `frontend/src/modules/ai-assistant/helpers/assistant-cards.ts`——该文件是本次改动之外既有未提交修改，未触碰。
- [x] 3.2 规格校验：`openspec validate stabilize-task-detail-loading --strict` 通过。验证：命令输出通过。**验证结果**：`Change 'stabilize-task-detail-loading' is valid`。
