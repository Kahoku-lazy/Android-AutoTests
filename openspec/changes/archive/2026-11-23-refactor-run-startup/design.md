# refactor-run-startup — 设计

## Context

动机见 proposal.md - Why。设计需要的现状约束：

- `run.py` 现有 616 行，函数与行号以当前 HEAD 为准；外部契约有三层：① CLI 命令面（`start/stop/restart/status/logs/check/setup` + `--no-db/--check/--force/--from-file`）；② 输出文案（现有测试断言 `"Aborted"`、`"远程"`、`"DB_AUTOSTART=0"`、`ONLINE/OFFLINE` 等字面量）；③ 规格 `openspec/specs/run-db-preflight/spec.md` 的三条 Requirement。
- 测试耦合方式：`tests/arch/unit/test_run_db_preflight.py` 用 `monkeypatch.setattr(run, "_db_reachable", ...)` 等直接替换 `run` 模块属性；`tests/task/unit/test_task_sweep.py` 调 `run._running_ids_from_drain`。**模块属性替换要求被测调用链真的经过该模块的全局名字**，这是拆分方式的关键约束。
- `utils/` 已是平台工具目录（`adb.py` / `platform_tools.py` / `check_gates.py` / `logs.py`），`run.py` 已依赖 `backend.config.env.load_dotenv` 与 `utils.adb` / `utils.platform_tools`（后者为函数内延迟 import）。
- 根 AGENTS 红线：模块依赖方向变更须先提变更申请；本设计不新增任何依赖边。

## Goals / Non-Goals

**Goals:**

- `run.py` 只剩入口职责；六种职责落到 `utils/service_ctl/` 的 5 个单一职责模块。
- 服务注册表、DB 连接参数、环境开关解析各收敛到唯一真相源。
- 消除导入期副作用；外部行为（命令面、输出文案、退出码、启停顺序）逐字节保持。
- 每步可独立验证、独立回退。

**Non-Goals:**

- 不改 `all()` 短路语义（backend 失败则不尝试 frontend）——要改另立变更。
- 不去重 `_write_stop_timeout_mark` 与 `backend/apps/task_list/sweep_mark.py`——涉及新依赖边，须先走变更申请。
- 不动横幅文案（含 admin 提示）、不动 `run_daphne.py`、不引入新第三方库、不做日志框架迁移（`utils/logs.py` 与本变更无关）。

## Decisions

### D1 落点：`utils/service_ctl/` 包（而非平铺或顶层新包）

与 `utils/adb.py`、`utils/check_gates.py` 同域，符合"相同业务功能一个目录"。备选①平铺 `utils/db_preflight.py` 等 5 个模块：utils 根目录已有 10 个文件，再铺 5 个会稀释目录语义；备选②顶层新包：新增顶层目录需要更强的理由，且与 utils 既有工具割裂。

**实施期修正（原案 `utils/platform/` 被否决）**：`utils/` 下的脚本（`python utils/check_openapi_coverage.py`、`gen_arch_stats.py` 等）执行时会把 `utils/` 放进 `sys.path`，此时包名 `platform` 会**遮蔽标准库 `platform`**——`wsgiref → from platform import python_implementation` 直接 ImportError，openapi-coverage 门禁实测失败。故包名改为 `service_ctl`（无标准库同名冲突，也不与既有 `utils/platform_tools.py`（Android platform-tools）混淆）。

包内分层：

```
run.py (入口: load_dotenv + argparse + 分发)
  └─> utils/service_ctl/commands.py   编排 + 横幅 + adb/setup 命令
        └─> services.py            按注册表启停 + drain + 超时名单
              ├─> db.py            DbConfig 唯一连接参数源 + 预检/清理
              └─> proc.py          端口/PID/kill/spawn/wait_http
                    └─> config.py  ServiceSpec 注册表 + env_flag + base_env
依赖单向向下，无环；config 不 import 包内任何模块。
```

### D2 服务注册表：`ServiceSpec` frozen dataclass，惰性构建

`config.py` 定义 `ServiceSpec(name, port, log, cwd, ready_timeout, extra_env, command)`，`build_registry() -> dict[str, ServiceSpec]` 在**命令执行时**调用（不在 import 时），`RETIRED_SERVICES` 与 `SERVICE_ORDER` 同归 config。`SERVICES/_START/_STOP/_LOGS` 五处散点全部由注册表派生。
理由：端口来自 `SERVER_PORT` 环境变量，惰性构建配合 D7 才能保证"先 load_dotenv 后读环境"。备选"import 时建表"会把导入期副作用换个地方复活，弃。

### D3 开关解析：`env_flag(name, default)` 单函数，语义逐值等价

统一词表 `TRUE={"1","true","yes"}`、`FALSE={"0","false","no"}`（strip+lower）：命中 TRUE 返回 True，命中 FALSE 返回 False，其余返回 default。
等价性核对（必须保持）：`DB_CHECK`/`DB_AUTOSTART` 现行为"值在 falsy 集才关"→ `env_flag(name, True)` 逐值等价；`AUTO_SETUP` 现行为"值在 truthy 集才开"→ `env_flag(name, False)` 逐值等价。`STOP_DRAIN_TIMEOUT` 是整数不是开关，保留 `int(os.environ.get(...))` 但收敛为 config 里的具名常量读取函数。

### D4 DB 参数唯一真相源：`DbConfig.from_env()`

frozen dataclass，字段即现 `_db_config()` 的 7 键。`db.py` 内 `reachable(cfg)` / `ensure(cfg, allow_autostart)` / `status_line()` / `start_local_service(cfg)` / `elevation_hint(cfg)` / `cleanup_idle_connections(cfg)` 全部吃同一个 cfg；`cleanup_idle_connections` 不再混读 `BASE_ENV`，与预检同源（两者默认值本就一致，行为等价，且根治漏传密码这类事故）。`MySQLdb` 保持函数内延迟 import。

### D5 进程工具与 drain 的归属

`proc.py`：`find_listening_pid / pid_alive / kill / graceful_kill / kill_port / wait_http / spawn / make_env`，命令构造（netstat/taskkill/lsof/kill、`CREATE_NO_WINDOW`）逐字保留。`spawn` 修复句柄泄漏：`open` 的日志文件在 `Popen` 返回后于父进程关闭（子进程已继承句柄，Windows 下行为不变）。
`services.py`：`start_service(spec)` / `stop_service(spec)` 按注册表分发（backend 停机 = drain → MySQL 清理 → kill_port 的既有顺序）；`_drain_backend` / `_running_ids_from_drain` / `_write_stop_timeout_mark` 原样迁入。超时名单**保留本地写入**（见 Non-Goals）。
魔法 sleep 收敛为具名常量（`STOP_SETTLE_SECONDS=1`、`RESTART_SETTLE_SECONDS=2`），数值不变。

### D6 测试策略：先特征测试、后迁 patch 目标，不做 re-export 门面

门面方案（run.py re-export 新模块函数）被否决：`monkeypatch.setattr(run, "_db_reachable", ...)` 影响不到 `db.py` 内部调用，门面会制造"测试绿但没测到"的假象。
迁移映射（旧 → 新）：

| 旧目标 | 新目标 |
|---|---|
| `run._db_reachable / _db_config / _ensure_db / _start_local_db_service / _is_loopback / _db_status_line` | `utils.service_ctl.db.*` |
| `run.cleanup_mysql_connections` | `utils.service_ctl.db.cleanup_idle_connections` |
| `run._running_ids_from_drain` | `utils.service_ctl.services.*` |
| `run.resolve_services / _STOP / _START / cmd_start` | `utils.service_ctl.commands.*`（注册表替身改 patch `build_registry` 或注入 specs） |
| `run.time.sleep / run.subprocess.run` | 对应新模块的 `time` / `subprocess` |

阶段 0 先对**现状 run.py** 补特征测试（cmd_start 先停后起与顺序、DB 失败中止、`resolve_services` 的 all/退役/非法分支、横幅文案），随后与实现同步迁移。输出文案断言全部保留原字面量。

### D7 入口时序：`load_dotenv()` 移入 `run.py` 入口，先于任何命令执行

`run.py` 顶部只 import 标准库与 `load_dotenv`；`main()` 第一行 `load_dotenv()`，随后才调用 `commands.*`（config 惰性读环境，见 D2）。`utils/service_ctl/*` 各模块 import 时零副作用，测试可自由 monkeypatch 环境后再调用。对 CLI 用户时序完全等价（原来 import 时读 .env，现在分发前读 .env，中间无其他读者）。

### D8 命名与注释

函数迁移尽量保留可识别名（去前导下划线转为模块公开 API，如 `_db_reachable → db.reachable`），降低迁移 diff 噪声；每个新模块按仓库注释规范写模块 docstring（职责清单 + 依赖 + 测试归属）。

## 模块防火墙自检

- 跨 App import：本变更不 import 任何 `backend.apps.*`；对 `backend.config.env.load_dotenv` 的依赖是既有边，保留在 `run.py` 入口，不扩散到 `utils/service_ctl/*`。
- 无新增跨模块依赖边：`utils/service_ctl → utils.adb / utils.platform_tools` 为既有边（原 run.py 内的延迟 import 原样迁入 commands.py）；停机名单不去重正是为了不新增 `→ backend.apps.task_list` 边（红线第 4 条）。
- 写库：本变更无任何 INSERT/UPDATE/DELETE；`cleanup_idle_connections` 的 `KILL` 是运维连接清理，非业务写库，原样保留。
- 前端不直连数据库、仪表盘不做写操作：本变更不触碰前端与仪表盘。
- 依赖方向：`run.py → utils.service_ctl.*` 单向；包内 `commands → services → {db, proc} → config` 单向无环。

## Risks / Trade-offs

- [测试 patch 目标迁移遗漏，出现假绿/假红] → 阶段 0 特征测试先行；迁移后全仓 grep `import run` / `setattr(run` 确认无残留；全量 unit/integration 门禁兜底。
- [输出文案或启停顺序漂移，破坏 run-db-preflight 规格与 e2e 环境] → 文案字面量原样搬运并保留断言；手工冒烟 `start/stop/restart/status/logs` 全命令面。
- [惰性注册表改变环境读取时机] → D7 保证 load_dotenv 先于一切读取；CLI 路径时序等价；测试路径反而更可控。
- [Windows 进程操作细节（taskkill 竞态、CREATE_NO_WINDOW、句柄继承）被"顺手优化"破坏] → proc.py 命令构造逐字保留，唯一改动是父进程关闭日志句柄（子进程已继承，安全）；stop 竞态注释原样保留。
- [包名与标准库撞名（已发生并修正）] → 初版 `utils/platform/` 在 `python utils/*.py` 的 sys.path 语义下遮蔽标准库 `platform`，openapi-coverage 门禁实测 ImportError；已改名 `utils/service_ctl/`（见 D1 实施期修正）。新增包名须先确认不与标准库模块同名。
- [一次大拆难 review] → 6 阶段小步提交，每步独立绿、独立回退（见 tasks.md）。

## Migration Plan

纯本地工具重构，无部署/数据迁移。实施按 tasks.md 的 6 阶段：特征测试 → config → proc → db → services → commands + 薄 run.py + 测试迁移；每阶段跑对应测试子集，收尾跑 `python run.py check` + 全量 unit/integration + 手工冒烟。回退策略：每阶段一个提交，任一步失败单独 revert 该步，不影响已合入的前序阶段。

## Open Questions

（无。`all()` 语义与 sweep_mark 去重已明确列为 Non-Goals，属后续独立变更，不影响本设计的任务拆分。）