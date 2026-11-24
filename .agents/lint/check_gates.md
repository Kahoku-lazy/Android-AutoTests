# check_gates —— 32 条检查的判定口径

本文逐条记录 `python -m run check` 实际在查什么、怎么判、判到哪里。

- **注册表（唯一真相源）**：`utils/check_gates.py` 的 `build_gates()`。
- **执行器**：`utils/check_gates.py`；`python -m run check` 与 `.github/workflows/ci-phase1.yml` 都只调到它。
- **目录与配置位置**：见 [lint.md](lint.md)。本文只写判定口径，不重复“配置文件放哪”。
- **模块依赖规则**：见 [linting.md](linting.md)。本文只登记 `linting` 这条门禁在跑。

## 1. 怎么跑

```text
python -m run check                                     # 全部 32 条
python -m utils.check_gates                             # 等价入口：直接跑注册表
python -m utils.check_gates --only silent-except        # 只跑一条
python -m utils.check_gates --only boundary,linting     # 逗号分隔
```

**写法约定**：本仓库一律用 `python -m <模块>` 调用 Python 入口，不写路径式
（`python utils/check_gates.py`）也不写 `python manage.py`。两者行为完全一致，
`-m` 方式的好处是走导入系统、不依赖 cwd 的脚本路径拼接。

| 入口 | 用途 | 路径式写法（等价，不再使用） |
|---|---|---|
| `python -m run check` | 平台管理入口 | `python run.py check` |
| `python -m utils.check_gates` | 门禁注册表 | `python utils/check_gates.py` |
| `python -m utils.gen_arch_stats` | 边界 / 体积检查 | `python utils/gen_arch_stats.py` |
| `python -m utils.check_openapi_coverage` | 契约覆盖检查 | `python utils/check_openapi_coverage.py` |
| `python -m manage <子命令>` | Django 管理命令 | `python manage.py <子命令>` |

`ci-phase1.yml` 目前仍用路径式调用（与 `-m` 等价，同一份 `main()`）；统一成 `-m` 需同步改工作流，见第 13 节。

| 退出码 | 含义 |
|---|---|
| 0 | 阻塞项全部通过（告警项失败不影响） |
| 1 | 有阻塞项失败 |
| 2 | `--only` 里出现未知门禁名（同时打印可用门禁清单） |

## 2. 分级与总数

**32 条 = 29 条阻塞 + 3 条告警。**

| 告警项 | 行为 |
|---|---|
| `cred-default-pwd` | `always_show`：命中就打印，但恒判通过，汇总不出现 WARN |
| `inline-style` | `always_show`：同上，恒判通过 |
| `engines-agents-style` | 按子命令退出码记 WARN，不影响退出码 |

CI 只点名那 29 条阻塞项（python job 20 条、frontend job 9 条），3 条告警项不进 CI，只在本地跑。

输出规则：明细只在**失败项**与 `always_show` 项下打印，每条取末尾 20 行；汇总行按 `PASS` / `FAIL` / `WARN` 逐条列出并统计阻塞与告警的通过数。

## 3. Python 正确性与契约（7 条，全阻塞）

| 门禁 | 查什么 | 判定 |
|---|---|---|
| `django-check` | Django 系统检查 | `manage.py check`，注入占位 `DJANGO_SECRET_KEY` |
| `makemigrations-check` | 迁移与模型是否一致 | `manage.py makemigrations --check --dry-run` |
| `pytest-collect` | 测试**能否全部导入**（不执行用例） | `pytest -c tests/pytest.ini --collect-only -q`，注入三把模型密钥占位值 |
| `openapi-schema` | 契约可生成、可校验、且与基线一致 | `spectacular --validate --fail-on-warn` 生成到 `temps/openapi.generated.yaml`，再与 `openspec/openapi.yaml` 逐字比对（比较前 CRLF 归一为 LF） |
| `openapi-coverage` | 业务路径是否全部已文档化 | `python -m utils.check_openapi_coverage` |
| `boundary` | 跨 App 写库、五个具名内部模块、`.u2` 句柄 | `python -m utils.gen_arch_stats --check-boundaries` |
| `linting` | 19 个模块的允许依赖 + 16 条禁止合同 | `python -m utils.linting` |

`openapi-schema` 失败时会直接给出重建基线命令：
`python -m manage spectacular --file openspec/openapi.yaml --validate --fail-on-warn`。

## 4. Python 风格（4 条，全阻塞）

| 门禁 | 范围 | 判定 |
|---|---|---|
| `ruff-format` | `backend/{apps,config,gateway,shared,models}/` + `tests/` | `ruff format --check` |
| `ruff-lint` | 同上 | `ruff check` |
| `ruff-engines-format` | `engines/` | `ruff format --check` |
| `ruff-engines-lint` | `engines/` | `ruff check` |

按目录分两组是因为规矩不同（`ruff.toml` 对 `engines/` 有单独配置），不是历史遗留。
`tests/` 于 2026-11-19 经需求方确认纳入 ruff 范围，但它**不在**凭据扫描范围内。

## 5. 前端质量与规范（10 条，全阻塞）

| 门禁 | 查什么 | 判定 |
|---|---|---|
| `vitest` | 前端单元测试（P0/P1） | `npm test` |
| `vite-build` | 能否构建 | `npx vite build` |
| `eslint` | 前端 lint | `npm run lint` |
| `vue-tsc` | 前端类型 | `npm run typecheck` |
| `prettier` | `src/**/*.{vue,js,css}` 格式 | `npx prettier --check` |
| `prettier-ts` | `src/**/*.ts` 格式 | `npx prettier --check` |
| `style-gates` | 字号 / 令牌 / 阴影 / 圆角 / 动效五类约束 | `npm run lint:styles` |
| `dashed-whitelist` | 虚线只允许落在 `KpiCard` / `AgentRouteCard` | `npm run lint:lines` |
| `vue-file-size` | 单个 `.vue` < 500 行（超标须进白名单） | `gen_arch_stats.py --check-frontend` |
| `mock-data` | 前端模块里的硬编码假数据 | 走查 `frontend/src/modules/**/*.vue`，正则 `ref(\s*\[\s*\{[^}]*id:` |

前 8 条以 `frontend/` 为 cwd；后 2 条在 python job 里跑，不需要装前端依赖。

## 6. 硬编码凭据（5 条）

| 门禁 | 查什么 | 范围 | 级别 |
|---|---|---|---|
| `cred-password` | `password = '...'` 字面量 | 平台 5 目录 + `engines/` | 阻塞 |
| `cred-apikey` | `api_key = 'sk-...'` | 平台 4 目录 + `engines/` | 阻塞 |
| `cred-secret` | `secret_key` / `SECRET_KEY` / `private_key` 字面量 | 平台 4 目录 + `engines/` | 阻塞 |
| `cred-frontend` | 前端 `api_key` / `password` / `token` / `secret` 取值 ≥8 位字面量 | `frontend/src` 的 `.js/.vue/.ts` | 阻塞 |
| `cred-default-pwd` | `'admin123'` / `'autotests2026'` / `password:` 等常见默认值 | 平台 4 目录 | 告警 |

排除规则与 CI 的 `grep -v` / `grep -vE` 同口径：

- `cred-password` 排除空串赋值与含 `PASSWORD` 的行；
- `cred-secret` 排除含 `os.environ` / `getenv` 的行；
- `cred-frontend` 排除 `node_modules` / `.test.`，并按行正则排除 `v-model:password`、`:token` 这类属性绑定；
- 平台 4 目录 = `PY_SCOPES` 去掉 `models/`（`models/` 里本来就有字段名，避免误报）。

## 7. 自研架构守门（4 条，全阻塞）

这 4 条在 CI 里没有等价的内联步骤，是 check_gates 独有的一层。

| 门禁 | 查什么 | 判定 |
|---|---|---|
| `silent-except` | 捕获后什么都不做：处理器体只有 `pass/continue/break`，且无 `raise`、无日志调用、无注释 | AST |
| `single-agent-constructor` | `Agent(...)` 只许出现在 `engines/ae_harness/agents/creator.py`，其余位置必须走 `create_agent` | AST，只看调用形态不看字符串 |
| `engines-agents-retirement` | ① 底座包不反向 import Agent 系（`engines/device`、`vision`、`uart_log` 禁 `engines.agents` / `backend_bridge` / `ae_harness`）② `knowledge_assistant` 产品面（前端 + 后端两条路径）不得存在 ③ `engines/agents` 不得存在，且 `engines` / `backend` / `tests` / `utils` 不得再 import 它 | import 行正则 + 目录存在性 |
| `business-asset` | 受管业务资产目录禁厂商标识（大小写不敏感，命中路径名或文件内容）；已禁用的资产路径不得复活 | 目录走查 + 路径存在性 |

`engines-agents-retirement` 的三项各有一个开关（`RETIRE_PHASE`），退役完成后已全部置为 `True`，即现在的口径就是最终口径：三项都在查。

## 8. 体积与风格告警（2 条，不影响退出码）

| 门禁 | 查什么 | 判定 |
|---|---|---|
| `inline-style` | `frontend/src/modules` 下单个 `<style>` 块超过 120 行 | 走查，恒判通过（只提示） |
| `engines-agents-style` | `module-docstring` 四字段 / tool 命名 / 禁 `django`·`apps` import | `python -m scripts.check_engines_agents_style`，按退出码记 WARN |

`engines-agents-style` 的正文规则在 `.agents/rules/engines-code-style.md`，本文不重复。

## 9. 四种判定器

| 判定器 | 用在哪些门禁 | 通过条件 | 失败时的表现 |
|---|---|---|---|
| 子进程退出码 | 所有 `cmd_gate` | 退出码为 0 | 取 stdout+stderr 末尾 20 行 |
| 源码走查 | 5 条凭据 + `mock-data` + `inline-style` | 无命中 | 输出 `相对路径:行号:命中行` |
| AST | `silent-except`、`single-agent-constructor` | 无命中 | 输出文件与行号 |
| 生成 + 比对 | `openapi-schema` | 生成成功且与基线逐字一致 | 附重建基线的命令 |

走查类统一跳过 `node_modules`、`__pycache__`、`.venv`、`venv`、`dist`、`.git`、`.pytest_cache`，只判同一条正则，不看语义。

## 10. 已知边界（2026-11-24 实测）

> 这一节记录的是“检查在跑，但覆盖不到”的位置。门禁全绿不等于覆盖完整。

| 边界 | 现状 | 影响 |
|---|---|---|
| 缺失目录静默跳过 | 走查类门禁遇到不存在的根目录直接跳过，不报错 | 路径搬走后范围静默缩水，结果仍是 PASS |
| `silent-except` 的根目录过期 | 写的是 `apps` / `config` / `gateway` / `shared` / `engines`，前四个在仓库根已不存在（`backend/` 迁包后未同步） | 实际只扫 `engines/`；用同一套 AST 规则扫 `backend/` 可测到 2 处命中：`backend/apps/task_list/api.py:822`、`backend/apps/task_list/sweep_mark.py:38` |
| `business-asset` 的受管目录随退役消失 | `BUSINESS_ASSET_DIRS` 指向 `engines/agents/config/data/app_info`，而该包已被本文件的门禁禁止存在 | 受管目录扫描恒空，只剩 `FORBIDDEN_ASSET_PATHS` 两条在生效 |
| 命令门禁对缺失路径的可见性不统一 | 实测 `ruff check <不存在的目录>` 输出 `All checks passed!` 并退出 0；`ruff format --check` 则报 `os error 2`、退出 2 | 同类漂移在不同门禁上表现相反，不能假定“路径错了会红” |
| 负向检查恒真 | `FORBIDDEN_ASSET_PATHS`、`knowledge_assistant`、`engines/agents` 都是“不得存在” | 换个包名或改个路径复活，门禁不报 |
| `single-agent-constructor` 只认裸名 | 只匹配 `Agent(...)` 这种直接名字调用 | `agent.Agent(...)`、别名导入后的调用抓不到 |
| 走查类只看单行 | 行级正则 + 子串/正则两套排除 | 跨行拼接、变量中转、Base64 等构造的凭据抓不到 |
| 契约测试只锁常量形状 | 如 `test_business_asset_gate.py` 断言受管目录基名是 `app_info`，不校验目录存在 | 路径死了测试照样绿，给了“有测试保护”的错觉 |
| `pytest-collect` 的作用域随调用目录 | `tests/pytest.ini` 写 `testpaths = .`，pytest 按调用 cwd 解析，实际扫的是仓库根 | 仓库根有不可读目录时收集必失败（如受限环境下的 `tools/platform-tools`）；`cd tests` 后收集 1209 项通过 |

## 11. 它不检查什么

| 不检查 | 说明 |
|---|---|
| 用例是否真跑通 | `pytest-collect` 只做收集；全量用例要另跑 `python -m pytest -c tests/pytest.ini` |
| 前端依赖边界 | `depcruise` 未接入本门禁，仍是手动 `npm run depcruise` |
| Python docstring 规范 | `engines/` 有 `engines-agents-style` 的 module-docstring 一条；其余靠 `.agents/skills/engines-docstring-check` |
| 无障碍、性能、包体积 | 无对应门禁 |

## 12. 改一条检查时

改哪里、改完要不要动 CI，见 [lint.md](lint.md) 的「改一条检查时改哪里」。本文只描述现状，不参与执行——**漏改本文不会让门禁失败，但会让本文失真**；以 `build_gates()` 的代码为准。

## 13. `-m` 统一范围

`-m` 写法已在本地验证通过（2026-11-24 实跑，均退出码 0）：

| 命令 | 结果 |
|---|---|
| `python -m utils.check_gates --only silent-except` | PASS，退出码 0 |
| `python -m utils.gen_arch_stats --check-boundaries` | 模块边界检查通过 — 零违规，退出码 0 |
| `python -m manage check` | `System check identified no issues`，退出码 0 |
| `python -m run --help` | 正常打印用法，退出码 0 |

已统一为 `-m` 的位置：

| 位置 | 现状 |
|---|---|
| `.github/workflows/ci-phase1.yml` | 两个 job 均为 `python -m utils.check_gates --only "$gates"` |
| `utils/service_ctl/commands.py` | 子进程改为 `sys.executable -m utils.check_gates`（`cwd` 保持仓库根）；`run setup` 提示文案同步 |
| `utils/check_gates.py` 执行器内部 | 六处子进程改模块调用：`manage check`、`manage makemigrations`、`manage spectacular`、`utils.check_openapi_coverage`、`utils.gen_arch_stats`（boundary / 体积各一处） |
| `run.py` | 模块 docstring 的用法示例改为 `python -m run ...` |
| `AGENTS.md` | 「项目工具」两条改为 `python -m run start / stop / status` 与 `python -m run check` |
| `README.md`、`README.en.md`、`CONTRIBUTING.md` | 示例命令改为 `python -m run ...` / `python -m manage ...` |
| `.agents/lint/lint.md`、`linting.md` | 示例命令改为 `-m` |
| `utils/adb.py`、`utils/__init__.py`、`utils/platform_tools.py` | 面向用户的安装提示改为 `python -m run setup` |
| `utils/check_openapi_coverage.py`、`utils/gen_arch_stats.py` | 模块 docstring 与失败提示改为 `-m` |
| `openspec/schemas/android-autotests/templates/tasks.md` | 任务模板里的验证命令改为 `-m` |
| `tests/device/unit/test_device_adb_missing.py` | 断言随 `utils/adb.py` 的提示文案同步 |
| `CHANGELOG.md` | `[Unreleased] → Changed` 登记本次统一 |

改完实测：受影响门禁 10/10 通过（`django-check`、`makemigrations-check`、`openapi-schema`、`openapi-coverage`、`boundary`、`vue-file-size`、`ruff-format`、`ruff-lint`、`ruff-engines-format`、`ruff-engines-lint`），`ci-phase1.yml` 两个 job 的 YAML 仍可解析。

保持原样、不参与统一的两类：

| 类别 | 例子 | 原因 |
|---|---|---|
| 历史记录 | `openspec/changes/archive/**`、`openspec/changes/cancelled/**`、`dev_docs/DEV_TEST/**`、`CHANGELOG.md` | 记录当时实际执行的命令，改写等于伪造历史 |
| 需求规格正文 | `openspec/specs/**` | 规格文字改动需走 OpenSpec 变更，不在文档统一范围内 |
| 活文档（未改） | `dev_docs/ARCH_PRD/**` | 架构 / 需求文档的命令示例仍在，随下一次文档同步变更一起改 |

待确认：`backend/AGENTS.md` 的自查清单仍写 `python manage.py check` 与 `python utils/gen_arch_stats.py --check-boundaries`；该段属准入清单，按根 `AGENTS.md` 第 4 条需先提变更申请。
