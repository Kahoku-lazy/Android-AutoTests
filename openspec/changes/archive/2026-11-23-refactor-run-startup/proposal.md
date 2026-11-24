# refactor-run-startup

## Why

`run.py` 已膨胀到 616 行，把配置、数据库预检、进程/端口工具、服务启停与排空、adb/setup、命令编排六种职责混在一个文件里：服务注册表散落 6 处（`SERVICES` / `SERVICE_ORDER` / `RETIRED_SERVICES` / `_START` / `_STOP` / `_LOGS`），数据库连接参数在 `_db_reachable` 与 `cleanup_mysql_connections` 各造一遍（历史上已因此漏传 `DB_PASSWORD` 出过事故，见 `tests/arch/unit/test_run_db_preflight.py::test_cleanup_mysql_passes_password`），环境开关 truthy 解析散写 4 处且口径不一。模块顶层还有导入期副作用（`load_dotenv()` + 读端口），测试只能先 import 再 monkeypatch，顺序脆弱。现在拆，是为了让"加一个服务 / 改一个开关"不再牵连一大片。

## What Changes

- `run.py` 瘦身为薄 CLI（约 60 行）：只做 docstring、`load_dotenv()`、argparse 与命令分发；命令面（`start / stop / restart / status / logs / check / setup` 及全部旗标）**完全不变**。
- 新增 `utils/service_ctl/` 包，按单一职责拆出 5 个模块：
  - `config.py`：`ServiceSpec` 服务注册表（端口/日志/启动命令/就绪超时一处定义）+ `env_flag()` 唯一开关解析 + `BASE_ENV`；
  - `proc.py`：端口/PID 探测、优雅与强制杀进程、`spawn`、`wait_http`；
  - `db.py`：`DbConfig.from_env()` 作为连接参数唯一真相源，预检、状态行、本机服务拉起、空闲连接清理全部复用；
  - `services.py`：按注册表启停服务、drain 排空、停机超时名单写入；
  - `commands.py`：`cmd_*` 编排与横幅输出。
- `load_dotenv()` 从模块顶层移入 `run.py` 的入口（消除 `import run` 的导入期副作用）。
- 现有测试的 monkeypatch 目标从 `run` 模块迁到新模块（re-export 门面无法保持 patch 语义，必须迁）；并先补特征测试锁住 `cmd_start` 顺序、先停后起、`resolve_services` 等现状行为。
- **行为零变更**：`all()` 短路（backend 失败则不尝试 frontend）原样保留；`run-db-preflight` 三条 Requirement 全部满足；不新增 `run.py → backend.apps` 依赖边（停机超时名单保留本地写入实现，与 `sweep_mark` 的去重另立变更）。
- 顺手修复两处实现层小缺陷（不改外部行为）：`spawn()` 父进程日志句柄泄漏；`cleanup_mysql_connections` 与预检的连接参数口径统一。

## 关联文档

无关联 PRD 编号：纯重构（内部结构调整，外部行为与命令面不变），无新增需求。

## Capabilities

### New Capabilities

（无——纯重构不引入新能力。）

### Modified Capabilities

（无——`run-db-preflight` 的需求级行为全部保持，仅实现位置变化。本变更已在 `.openspec.yaml` 声明 `skip_specs: true`。）

## Impact

- **代码**：`run.py`（重写为薄 CLI）；新增 `utils/service_ctl/{__init__,config,proc,db,services,commands}.py`。
- **测试**：`tests/arch/unit/test_run_db_preflight.py`（patch 目标迁移）、`tests/task/unit/test_task_sweep.py`（`_running_ids_from_drain` 的 import 迁移）；新增 `tests/arch/unit/` 下启动编排特征测试。
- **依赖方向**：`run.py → utils.service_ctl.*`；`utils/service_ctl` 内部单向 `commands → services → {db, proc} → config`，无环；对 `backend.config.env.load_dotenv` 的既有依赖保留在 `run.py` 入口；不新增对 `backend.apps` 的依赖。
- **不受影响**：`run_daphne.py`、`utils/check_gates.py`、前端、后端各 App、CI 命令面（`python run.py check` 等照常）。
- **风险与回退**：按模块分 6 步提交，每步旧测试保持绿；任一步出问题可单独回退该步。最大风险是测试 patch 目标迁移遗漏，用全量 unit/integration 门禁兜底。