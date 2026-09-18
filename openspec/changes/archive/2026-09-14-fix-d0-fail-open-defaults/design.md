## Context

- 变更性质：**有行为变化的配置变更**（默认值收窄），无 API/DB/前端改动。
- 现状证据（均实测，非推测）：
  - `config/settings.py:58`、`:133-137`、`:138`（原文见 proposal 表）；
  - `CORS_ALLOWED_ORIGINS` 全仓 0 命中 → 未接线；
  - `.env`（未跟踪）只设 `DJANGO_DEBUG=True`，未设 `DJANGO_ALLOWED_HOSTS` / `CORS_*` → 本地走默认值；
  - `DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true","1","yes")`（`:40`）→ **默认档位是生产**，所以「默认 fail-open」不只是理论问题；
  - `tests/` 内 0 处引用 `ALLOWED_HOSTS` / `CORS_ALLOW_ALL_ORIGINS`；
  - Django `django.test.utils.setup_test_environment()` 会把 `"testserver"` 追加进 `ALLOWED_HOSTS`（源码实测）→ 测试客户端不受本变更影响。
- 同类前例：`.openspec.yaml` 的 `skip_specs` 用于无 spec 级变化的变更；本变更同样不以 spec 承载。

## Goals / Non-Goals

**Goals:**

- 让「不配置」等于「安全默认」：生产档位（`DEBUG=False`）下默认拒绝未知 Host、默认不放行跨域；本地开发（`DEBUG=True`）保持现有的免配置体验。

**Non-Goals:**

- 不改 `CORS_ALLOW_CREDENTIALS`（生产 allow-all 已关闭，凭据只对白名单来源有效）。
- 不引入 `CSRF_TRUSTED_ORIGINS`、`SECURE_*` 等其它加固项（D0-7~13，另案）。
- 不引入 `_env_bool()` 之类的配置读取抽象（见 D1）。
- 不动本地 `.env`（未跟踪，属本机环境）。

## Decisions

**D1 默认值按 `DEBUG` 分档，不新建 helper、不拆配置文件。**
既有风格是三处内联 `os.environ.get(...).lower() in ("true","1","yes")`；只把「默认值」从常量改为随 `DEBUG` 变的表达式，diff 最小、读起来仍是「一行一件事」。
备选：抽 `_env_bool(name, default)` —— 会顺带重写 `DEBUG` 等既有行，超出本次需求（AGENTS.md：只碰必须碰的）。

**D2 显式环境变量始终优先于新默认值。**
`os.environ.get(...)` 的既有语义保留：生产若要刻意放开，仍可 `CORS_ALLOW_ALL_ORIGINS=True` 或 `DJANGO_ALLOWED_HOSTS=*`。本次只改「不配置时」的结果，不改「配置后」的语义。

**D3 必须同时接线 `CORS_ALLOWED_ORIGINS`。**
只把默认值改成 `False` 而不提供白名单入口，等于把生产从「全放开」推向「全封死」，前端将无法跨域访问——那是把 fail-open 换成 fail-broken。接线后：默认关 + 白名单可配。

**D4 不新增 capability spec。**
`openspec/specs/` 现有 23 份 spec 全部是功能/协议/前端主题，没有「配置与安全默认值」类能力；为此新造一份 spec 属过度设计。不变量（生产默认 fail-closed、显式配置优先）写在本文件与 ARCH-00 §七，二者是本仓库 D0 层的既有落点。

**D5 `.env.example` 的死键清理并入本变更。**
`SCREENSHOT_INTERVAL` / `AGENTSCOPE_PORT` 是上一变更（`remove-dead-d0-config`）删除的符号，其模板文件当时漏改；同一文件的同一主题，一次改完，避免留一个「模板里有、代码里没有」的坑。

**D6 生产默认 `ALLOWED_HOSTS=127.0.0.1,localhost`。**
它让「单机部署（同机 nginx 反代到 Daphne，Host 为 127.0.0.1）」「本机 `manage.py check`/`runserver` 冒烟」仍能直接工作，同时拒绝外部 Host 头；对外域名/IP 都必须显式声明——这正是 `ALLOWED_HOSTS` 的设计意图。

## Risks / Trade-offs

- [部署侧 BREAKING：未配置 `DJANGO_ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS` 的生产环境升级后 400/跨域失败] → 已在 proposal「What Changes #6」与「Impact」显式登记，并给出迁移动作；本仓库本地 `.env` 为 `DEBUG=True` 不受影响。
- [显式设了 `CORS_ALLOW_ALL_ORIGINS=True` 的生产环境行为不变（仍是全放开）] → 这是 D2 的有意保留（显式即授权）；如需彻底禁止，属另案策略问题。
- [`DJANGO_ALLOWED_HOSTS` 传空串（`DJANGO_ALLOWED_HOSTS=`）会得到 `[""]`] → 沿用变更前语义（`split(",")` 不过滤空项），不在本次顺手改动。
- [测试客户端依赖 `testserver`] → 已核实 Django 在测试环境追加 `"testserver"`；并以 `pytest -m "unit or integration"` 回归。
