# lint 目录

这里只登记仓库里**已经在执行**的检查。

位置是 `.agents/lint/`，和 `.agents/rules/`、`.agents/docs/` 放在一起。工具配置文件仍留在各自默认路径，不搬进本目录。ruff、pytest、ESLint、Prettier、vue-tsc、OpenSpec 只认自己的默认位置；搬过来，对应检查就不再生效。

本文件是目录，不是第二份规则。条文仍以根 `AGENTS.md`、各级索引和 `.agents/rules/` 为准。改红线、禁止事项、准入清单、依赖方向，先走变更申请，不在这里改。

## 怎么跑

```text
python run.py check
```

本地跑 `utils/check_gates.py` 里登记的全部 32 条。退出码只看阻塞项。

CI 是 `.github/workflows/ci-phase1.yml`。它只点名那 29 条阻塞项，不再把命令抄进 YAML。3 条告警项不进 CI。

## 32 条门禁

注册表：`utils/check_gates.py` 的 `build_gates()`。

`blocking=False` 的只有 3 条。其中 `cred-default-pwd` 与 `inline-style` 命中了也打印为通过，汇总里不会出现 WARN。只有 `engines-agents-style` 会按命令退出码记成 WARN，且不影响退出码。

| 门禁 | 检查什么 | 配置 / 实现 | 级别 |
|---|---|---|---|
| django-check | Django 系统检查 | `manage.py check` | 阻塞 |
| ruff-format | Python 格式（平台 + tests） | `ruff.toml` | 阻塞 |
| ruff-lint | Python lint（平台 + tests） | `ruff.toml` | 阻塞 |
| makemigrations-check | 迁移与模型一致 | `manage.py makemigrations --check` | 阻塞 |
| pytest-collect | 测试可收集，不执行用例 | `tests/pytest.ini` | 阻塞 |
| openapi-schema | OpenAPI 可生成且与基线一致 | `openspec/openapi.yaml` | 阻塞 |
| openapi-coverage | 业务路径都已写进契约 | `utils/check_openapi_coverage.py` | 阻塞 |
| vitest | 前端单元测试 | `frontend/package.json` 的 `test` | 阻塞 |
| vite-build | 前端构建 | `frontend/vite.config.js` | 阻塞 |
| prettier | 前端格式（vue / js / css） | `frontend/.prettierrc`、`frontend/.prettierignore` | 阻塞 |
| ruff-engines-format | Python 格式（engines） | `ruff.toml` | 阻塞 |
| ruff-engines-lint | Python lint（engines） | `ruff.toml` | 阻塞 |
| eslint | 前端 lint | `frontend/eslint.config.js` | 阻塞 |
| dashed-whitelist | 虚线只允许白名单落点 | `frontend/tests/check-dashed-whitelist.mjs` | 阻塞 |
| vue-tsc | 前端类型 | `frontend/tsconfig.json` | 阻塞 |
| prettier-ts | 前端格式（.ts） | `frontend/.prettierrc` | 阻塞 |
| style-gates | 字号 / 令牌 / 阴影 / 圆角 / 动效 | `frontend/tests/check-style-gates.mjs` | 阻塞 |
| cred-password | 硬编码密码 | `check_gates.py` 内正则 | 阻塞 |
| cred-apikey | 明文 API Key | 同上 | 阻塞 |
| cred-default-pwd | 常见默认密码 | 同上 | 只打印，恒通过 |
| cred-secret | 硬编码 Token / Secret | 同上 | 阻塞 |
| cred-frontend | 前端硬编码凭据 | 同上 | 阻塞 |
| boundary | 跨 App 写库、五个内部模块名、`.u2` 句柄 | `utils/gen_arch_stats.py --check-boundaries` | 阻塞 |
| linting | 每个包的允许依赖 + 禁止合同（可查间接链） | `.linting` / `utils/linting/` | 阻塞 |
| vue-file-size | Vue 单文件不超过 500 行；超标文件须在白名单 | `utils/frontend-whitelist.json` | 阻塞 |
| mock-data | 前端模块里的硬编码假数据 | `check_gates.py` 内正则 | 阻塞 |
| inline-style | 单文件内联样式过长 | `check_gates.py` | 只打印，恒通过 |
| silent-except | 捕获后什么都不做且无注释 | `check_gates.py` AST | 阻塞 |
| business-asset | 受管目录禁厂商标识，禁用路径不得复活 | `check_gates.py` | 阻塞 |
| engines-agents-retirement | 旧 Agent 包不复活、底座不反向依赖 | `check_gates.py` | 阻塞 |
| single-agent-constructor | `Agent(...)` 只允许出现在 `creator.py` | `check_gates.py` AST | 阻塞 |
| engines-agents-style | module-docstring 存在性 / tool 命名 / 禁 django·apps import | `.agents/rules/engines-code-style.md` | 告警 |

`boundary` 现在只留 import 图表达不了的三件事：

1. 跨 App 写库必须走对方 `api.py`。
2. 跨 App 不得 import 五个具名内部模块：`service`、`runner`、`consumer`、`callbacks`、`state_machine`。
3. `backend/apps` 与 `backend/gateway` 的代码行不得出现 `.u2`。

import 方向由 `linting` 门禁承担：`utils/linting` 读仓库根的 `.linting`，一次建立模块级 import 图，同时做允许清单与红线两套判定。规则、红线清单与验收方法见 [linting.md](linting.md)，这里只登记“它在跑”。

`tach.toml` 与 `.importlinter` 已删除，`tach` / `import-linter` 两个包也已从 `requirements.txt` 移除。需要第三方工具复跑时，用 `python -m utils.linting export --out-dir <目录>` 按 `.linting` 重新生成这两份配置。

## 工具配置留在原地

| 文件 | 谁读 | 不要搬的原因 |
|---|---|---|
| `ruff.toml` | ruff-format / ruff-lint / ruff-engines-* | ruff 从仓库根读 |
| `tests/pytest.ini` | pytest-collect | 门禁命令写死 `-c tests/pytest.ini` |
| `frontend/eslint.config.js` | eslint | ESLint 从 `frontend/` 读 |
| `frontend/.prettierrc` | prettier / prettier-ts | Prettier 从 `frontend/` 读 |
| `frontend/.prettierignore` | 同上 | 同上 |
| `frontend/tsconfig.json` | vue-tsc | `vue-tsc` 从 `frontend/` 读 |
| `frontend/tests/check-style-gates.mjs` | style-gates | `npm run lint:styles` 的脚本路径 |
| `frontend/tests/check-dashed-whitelist.mjs` | dashed-whitelist | `npm run lint:lines` 的脚本路径 |
| `utils/check_gates.py` | 全部 32 条的注册表 | `run.py check` 与 CI 都调用它 |
| `utils/linting/` | linting | 读取仓库根的 `.linting`；判定逻辑不在这里改 |
| `.linting` | linting | 仓库根的依赖真相源；linting 只认这个路径 |
| `utils/frontend-whitelist.json` | vue-file-size | `gen_arch_stats.py` 按这个路径读 |
| `utils/boundary-whitelist.json` | boundary | 同上；当前不存在，按空列表处理 |
| `.github/workflows/ci-phase1.yml` | CI 编排 | GitHub Actions 只认这个路径 |
| `openspec/config.yaml` | OpenSpec CLI | 只约束产物语言：zh-CN，SHALL/MUST 保持英文 |
| `openspec/schemas/android-autotests/schema.yaml` | OpenSpec CLI | 四件套顺序是 proposal → specs → design → tasks |

OpenSpec 这两份不在 `check_gates.py` 里，也不在 CI 里。只有跑 OpenSpec 流程时才用到。

不算门禁、本目录不收的仓库配置：`.gitattributes`、`.gitignore`、`.github/dependabot.yml`、`frontend/.npmrc`。

## linting 与 boundary 的分工

两份配置都在默认位置：`.linting` 在仓库根（linting 只认这个路径），`boundary` 的内部规则写在 `utils/gen_arch_stats.py`。

| 规则 | 交给谁 | 不交给另一个的原因 |
|---|---|---|
| 每个 App、每个引擎包的允许依赖与禁止合同 | `.linting` 的 `[[modules]]` / `[[forbid]]` | 一次建图两套语义，避免两份配置各自漂移 |
| 跨 App 只能碰对方公开模块 | `.linting` 的 `ignore_imports` 白名单 | 白名单命中不到真实 import 会报错，白名单不会越积越多 |
| 跨 App 写库、`.u2` 句柄、五个具名内部模块 | `boundary` | 前两件不是 import 关系；五个模块名是行首文本规则 |

两边本地都已跑过：`python -m utils.linting` 通过（19 个模块、16 条红线），`python utils/check_gates.py --only boundary,linting` 2/2 通过。

## 改一条检查时改哪里

1. 依赖方向、模块清单、白名单：改仓库根的 `.linting`，**不要**改 `utils/linting/` 的判定逻辑；改完跑 `python -m utils.linting`，并按 [linting.md](linting.md) 第 5 节验收一遍。
2. 新增或改其它判定：只改 `utils/check_gates.py` 的 `build_gates()`。
3. 若新增阻塞项，再把名字加进 `ci-phase1.yml` 对应 job 的 `--only` 列表。告警项不加。
4. 改完回到本文件，改表格里的那一行。本文件不参与执行，漏改不会让门禁失败，但会让目录再次失真。
