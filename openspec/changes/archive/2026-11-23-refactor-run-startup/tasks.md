# refactor-run-startup — 任务清单

> 依据：proposal.md（范围）、design.md（D1–D8 决策与迁移映射）。
> 纪律：每阶段一个提交、独立绿、独立回退；输出文案与启停顺序逐字保留；不新增依赖边。

## 1. 特征测试锁住现状（对现有 run.py）

- [x] 1.1 新增 `tests/arch/unit/test_run_startup_orchestration.py`：覆盖 `cmd_start` 先停后起与启动顺序、DB 失败中止且零服务拉起、`--no-db` 跳过检查、`all()` 短路现状（backend 失败则 frontend 不尝试）、成功横幅文案、`resolve_services` 的 all/退役 redis 提示/非法服务退出码 1。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_run_startup_orchestration.py` 全绿（此时被测对象仍是旧 run.py）。
- [x] 1.2 跑基线确认无回归：`python -m pytest -c tests/pytest.ini tests/arch/unit tests/task/unit/test_task_sweep.py` 全绿，记录结果作为后续各阶段的对照基线。

## 2. config.py：注册表 + 开关解析（D2/D3）

- [x] 2.1 新建 `utils/service_ctl/__init__.py` 与 `utils/service_ctl/config.py`：`ServiceSpec` frozen dataclass、惰性 `build_registry()`、`RETIRED_SERVICES`、`SERVICE_ORDER`、`env_flag(name, default)`、`base_env()`、`stop_drain_timeout()`、具名 settle 常量；模块 docstring 按仓库规范写职责/依赖/测试归属。验证：`ruff check utils/service_ctl` 通过。
- [x] 2.2 新增 `tests/arch/unit/test_platform_config.py`：`env_flag` 对 `DB_CHECK/DB_AUTOSTART/AUTO_SETUP` 的逐值等价表（含 "0/1/true/false/yes/no/空/乱值"）、注册表端口取自 `SERVER_PORT`、日志名与 cwd 字段正确。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_platform_config.py` 全绿。

## 3. proc.py：进程/端口工具（D5）

- [x] 3.1 新建 `utils/service_ctl/proc.py`：迁入 `find_listening_pid / pid_alive / kill / graceful_kill / kill_port / wait_http / spawn / make_env`，命令构造与竞态注释逐字保留；唯一改动是 `spawn` 在 `Popen` 后关闭父进程日志句柄。验证：`ruff check utils/service_ctl/proc.py` 通过。
- [x] 3.2 新增 `tests/arch/unit/test_platform_proc.py`：`kill_port` 优雅/强制两分支、无监听 PID 返回 False、`wait_http` 成功/超时、`spawn` 句柄关闭（用替身 Popen/open）。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_platform_proc.py` 全绿。

## 4. db.py：连接参数唯一真相源（D4）

- [x] 4.1 新建 `utils/service_ctl/db.py`：`DbConfig.from_env()` + `reachable / ensure / status_line / start_local_service / elevation_hint / cleanup_idle_connections`，全部吃同一 cfg；`cleanup_idle_connections` 改从 `DbConfig` 取参（含密码）；`MySQLdb` 保持延迟 import；输出文案逐字保留。验证：`ruff check utils/service_ctl/db.py` 通过。
- [x] 4.2 按 design.md D6 映射表迁移 `tests/arch/unit/test_run_db_preflight.py` 的全部 patch 目标到 `utils.service_ctl.db`（含 `run.time.sleep`/`run.subprocess.run` 替身），断言文案不变。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_run_db_preflight.py` 全绿。

## 5. services.py：启停 + drain（D5）

- [x] 5.1 新建 `utils/service_ctl/services.py`：按注册表的 `start_service / stop_service`（backend 停机保持 drain → MySQL 清理 → kill_port 顺序）、`_drain_backend / _running_ids_from_drain / _write_stop_timeout_mark` 原样迁入（名单保留本地写入，不 import backend.apps）。验证：`ruff check utils/service_ctl/services.py` 通过。
- [x] 5.2 迁移 `tests/task/unit/test_task_sweep.py::test_running_ids_extracted_from_drain_payload` 的 import 与调用目标到 `utils.service_ctl.services`。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_task_sweep.py` 全绿。

## 6. commands.py + 薄 run.py（D1/D7/D8）

- [x] 6.1 新建 `utils/service_ctl/commands.py`：迁入 `cmd_start/stop/restart/status/logs/check/setup`、`resolve_services`、`_adb_status_line / _ensure_adb` 与横幅输出；开关改走 `env_flag`，服务启停改走注册表；`all()` 短路语义原样保留。验证：`ruff check utils/service_ctl/commands.py` 通过。
- [x] 6.2 重写 `run.py` 为薄 CLI（docstring + argparse + 分发表）：`main()` 首行 `load_dotenv()`，随后分发到 `commands.*`；删除全部已迁出的函数与顶层副作用。验证：`python run.py status` 与 `python run.py logs backend` 输出与重构前一致（四行状态/日志尾 20 行）。
- [x] 6.3 迁移阶段 1 特征测试与其余残留 patch 目标到 `utils.service_ctl.commands`（注册表替身按 D6 注入）。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit` 全绿。
- [x] 6.4 全仓确认无残留引用：grep `import run`、`setattr(run`、`run\._`，仅剩文案字符串类引用（如 tests/device 的提示语断言）。验证：grep 结果逐条核对并记录在提交说明。

## 7. 收尾门禁与冒烟

- [x] 7.1 架构红线：`python utils/gen_arch_stats.py --check-boundaries` 通过（确认无新增依赖边、无环）。
- [ ] 7.2 本地质量门禁：`python run.py check` 通过（含 ruff）。
- [ ] 7.3 全量测试：`python -m pytest -c tests/pytest.ini -m "unit or integration"` 全绿，与 1.2 基线对照无新增失败。
- [ ] 7.4 手工冒烟全命令面：`python run.py start` → `status`（四行 ONLINE）→ `logs` → `restart` → `stop` → `setup --check`；另验 `start --no-db` 与 DB 停机时的中止文案符合 run-db-preflight 规格。验证：逐命令输出与重构前一致，记录验收结果。

## 8. 验收记录（等待环境修复后补勾）

- 7.2 现状：可运行的门禁子集 8/8 通过（django-check / makemigrations / pytest-collect / boundary / silent-except / business-asset / engines-agents-retirement / single-agent-constructor）；ruff format/lint 用 `--no-cache` 对 `run.py + utils/service_ctl + tests` 全通过。整条 `run.py check` 仍失败于沙箱写入权限（见 7.4）与工作区既有未完成改动（prettier / vue-tsc / knowledge-search 端点未文档化），非本变更引入。
- 7.3 现状：本变更相关测试 188 通过 / 4 失败（与 1.2 基线同一批 4 个既有失败）；全量 `-m "unit or integration"` 为 866 通过 / 23 失败，失败项均在其他模块（ai_assistant / device / serial_log / task）且根因是工作区既有改动（`create_role` 改 `prepare_role`、`Workflow.release_state` 缺失、厂商标识变更）或 `logs/` 写入被拒，无一涉及 `run.py` / `utils/service_ctl`。
- 7.4 现状：`status`（与 HEAD 版逐行一致）、`logs`、`stop`、`setup --check`、DB 不可达中止文案均已验证；`start` / `restart` 在 `logs/backend.log` 写入处被拒（`PermissionError`）。HEAD 版 `run.py` 在同一行同样失败，证明是环境限制而非重构回归：沙箱子进程以低完整性运行，而 `logs/`、`tests/`、`utils/`、`frontend/` 等目录缺少 Low 完整性标签，只有工作区根与 `backend/` 可写。