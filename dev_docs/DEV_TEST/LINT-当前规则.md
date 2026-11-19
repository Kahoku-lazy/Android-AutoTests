# 当前 Lint 规则

> 记录仓库**现在实际生效**的检查，不是建议稿。
> 核对来源：`ruff.toml`、`frontend/eslint.config.js`、`frontend/tests/check-style-gates.mjs`、`utils/check_gates.py`、`.github/workflows/ci-phase1.yml`。
> 日期：2026-11-19。

规则分两套，同一条禁令只写在一处。

| 套 | 管什么 | 配置 |
| --- | --- | --- |
| 通用写法 | 任何 Python / 前端项目都该查的写法 | `ruff.toml`、`frontend/eslint.config.js` |
| 本仓库结构 | 只有这个仓库才成立的红线 | `utils/check_gates.py` |

Skill 目录不进这两套。`skill-creator` 与 `stylekit-skill` 已在 `ruff.toml` 排除。

提交前跑 `python run.py check`。它与 CI 用的是同一批门禁。

## 1. Python：Ruff

配置：[ruff.toml](../../ruff.toml)。行宽 100，目标 Python 3.13。

```powershell
python -m ruff check .
python -m ruff format --check .
```

CI 不是扫整个仓库。`ruff-lint` / `ruff-format` 只扫后端五个目录：

```text
backend/apps/  backend/config/  backend/gateway/  backend/shared/  backend/models/
```

`ruff-engines-lint` / `ruff-engines-format` 另扫 `engines/`。两段都失败即挡 CI。

### 1.1 启用的规则

| 编号 | 规则 |
| --- | --- |
| `I` | import 顺序：标准库 → 第三方 → `backend` / `engines` / `utils`，组之间空一行 |
| `F403` `F405` | 禁止 `from 模块 import *` |
| `F401` | 禁止没用到的 import |
| `F841` | 禁止赋值了却没用的变量 |
| `F821` | 禁止用了却没导入的名字 |
| `E722` | 禁止裸 `except:` |
| `B904` | `except` 里再 `raise` 必须 `from err` 或 `from None` |
| `T201` | 库代码禁止 `print()` |
| `Q` | 字符串用双引号 |
| `S608` | 禁止用字符串拼接拼 SQL |

格式另由 `ruff format` 管：空格缩进、双引号、保留尾随逗号。

### 1.2 豁免

| 范围 | 放开的规则 | 原因 |
| --- | --- | --- |
| `**/__init__.py` | `F401` | 再导出 |
| `backend/config/settings.py`、`tests/test_settings.py` | `F403` `F405` | 配置允许星号导入 |
| `tests/**/*.py` | `T201` | 测试可以打印 |
| `run.py`、`**/management/commands/*.py` | `T201` | 命令行入口 |
| `utils/{check_gates,gen_arch_stats,check_openapi_coverage,live_screen,module_docstring}.py` | `T201` | 这五个是命令行脚本；`utils/logs.py` 是库，不放开 |
| `engines/ae_harness/assistant/_bootstrap.py`、`engines/ae_harness/knowledge/probe.py` | `T201` | 控制台骨架与知识库探针 |
| 四个文档技能的 `scripts/` | `T201` | 技能自带的命令行：engines-agents-style、engines-docstring、django-61-docs、agentscope-docs |
| `engines/agents/realtime_vocie_agent.py`、`engines/agents/realtime_vocie/demo.py` | `T201` | 本地演示入口。对应包已退役，这两条豁免目前没有文件可匹配 |

整目录排除：迁移、`__pycache__`、`.venv`、`node_modules`、`skill-creator`、`stylekit-skill`。

`**/apps.py`、`**/admin.py`、`**/conftest.py` 还写着忽略 `D100`。当前没有启用 docstring 规则，这三条不生效。

## 2. 前端：ESLint

配置：[frontend/eslint.config.js](../../frontend/eslint.config.js)。CI 门禁名是 `eslint`，命令是 `npm run lint`，扫 `frontend/src`。

不扫：`dist/`、`node_modules/`、`src/auto-imports.d.ts`、`src/components.d.ts`。

### 2.1 失败即挡

| 规则 | 内容 |
| --- | --- |
| ESLint recommended | JS 推荐规则。`no-undef`、`no-unused-vars` 关掉，交给 `vue-tsc` |
| `eslint-plugin-vue` 的 `flat/essential` | Vue 推荐规则 |
| `no-debugger` | 禁止留下 `debugger` |
| `no-var` | 禁止 `var` |
| `no-restricted-imports` | 禁止直接 import `axios`、`ky`、`got`、`superagent` |
| `no-restricted-globals` | 禁止直接使用 `fetch`、`XMLHttpRequest` |
| `no-restricted-syntax` | 禁止 `navigator.sendBeacon` |
| `no-console`（仅 `src/modules/**`、`src/views/**`） | 禁止 `console.log` 与 `console.debug`。`console.warn`、`console.error` 允许 |

HTTP 只能走 `@/shared/api-client`。只有这两个文件例外：

```text
src/shared/api-client.ts
src/shared/api-auth-interceptors.ts
```

### 2.2 只警告，不挡提交

| 规则 | 内容 |
| --- | --- |
| `no-console` | 业务目录以外的 `console.log` 只警告 |
| `prefer-const` | 能用 `const` 就别用 `let` |
| `@typescript-eslint/no-explicit-any` | 少写 `any` |
| `@typescript-eslint/no-unused-vars` | 未使用变量；以 `_` 开头的参数和变量忽略 |
| `@typescript-eslint/no-empty-function` | 空函数 |
| `vue/no-mutating-props` | 不直接改 props |
| `vue/no-unused-vars` | 模板未使用变量 |
| `vue/no-use-v-if-with-v-for` | `v-if` 不和 `v-for` 放一起 |
| `no-unreachable` `preserve-caught-error` `no-empty` `no-useless-assignment` `no-irregular-whitespace` | 历史遗留，先降为警告 |

明确关闭：`vue/multi-word-component-names`、`vue/no-v-html`。

类型对错不在 ESLint 里判，由门禁 `vue-tsc` 挡。

## 3. 前端样式

门禁名 `style-gates`，命令 `npm run lint:styles`，实现是 [frontend/tests/check-style-gates.mjs](../../frontend/tests/check-style-gates.mjs)。失败即挡。

| 批 | 规则 |
| --- | --- |
| 1 | 排版字号不低于 12px，禁止硬编码 `font-size` 字面量 |
| 1b | 画布字号（ECharts 等）单独计数，只降不增 |
| 2 | 颜色与规格只登记在 `tokens.css` 的主 token，调色板只降不增 |
| 3 | `.vue` / `.css` / `.ts` / `.js` 里的外观值要能追到主 token |
| 4 | 阴影模糊半径为 0；圆角用纸张刻度；动效用时长令牌 |

虚线另有门禁 `dashed-whitelist`（`npm run lint:lines`）：虚线只允许出现在规定的卡片上。

`vue-file-size` 要求单个 Vue 文件不超过 500 行。`mock-data` 禁止在 `frontend/src/modules/**/*.vue` 里用 `ref([{ id: ... }])` 写假列表。

## 4. 本仓库结构门禁

全部定义在 [utils/check_gates.py](../../utils/check_gates.py)。下表只列规则，不列测试收集、构建和格式化。

### 4.1 失败即挡，并且进 CI

| 门禁 | 规则 |
| --- | --- |
| `boundary` | 三道墙：跨 App 不许 import 对方内部实现；跨 App 不许直接写对方的表；`engines/` 不许 import `django` 或 `backend.apps`；`device` / `vision` / `uart_log` 不许反向依赖 `backend_bridge` 或 `ae_harness` |
| `cred-password` | 后端五个目录与 `engines/` 不许写 `password = '...'` |
| `cred-apikey` | 同上范围，不许写 `sk-` 开头的明文 Key |
| `cred-secret` | 不许把 `secret_key` / `private_key` 写成字符串字面量。从环境变量读的不算 |
| `cred-frontend` | `frontend/src` 不许把 `api_key` / `password` / `token` / `secret` 赋成长字面量 |
| `silent-except` | 捕获后只有 `pass` / `continue` / `break`、又没有日志和注释的，失败 |
| `business-asset` | 受管资料目录不许出现受限厂商标识；已禁用的资料路径不许重新出现 |
| `engines-agents-retirement` | `engines/agents` 不许复活；全仓不许再 import 它；已下线的知识助手目录不许存在 |
| `single-agent-constructor` | `Agent(...)` 只能写在 `engines/ae_harness/agents/creator.py`，其余走 `create_agent` |
| `openapi-schema` | 生成的 OpenAPI 必须和 `openspec/openapi.yaml` 一致 |
| `openapi-coverage` | 业务路径必须全部写进契约 |

### 4.2 不挡提交

| 门禁 | 行为 |
| --- | --- |
| `cred-default-pwd` | 发现 `admin123`、`autotests2026` 这类默认密码只提示，检查仍算通过 |
| `inline-style` | 单个 Vue 的 `<style>` 超过 120 行只提示 |
| `engines-agents-style` | docstring、`Raises`、工具命名只告警。本地 `run.py check` 会跑，CI 的 `--only` 名单里没有它 |

## 5. 一次提交实际会过哪些

推到 `Kahoku` 后，CI 分两个 job。名字来自 `.github/workflows/ci-phase1.yml`。

Python job：

```text
django-check, ruff-format, ruff-lint, pytest-collect,
openapi-schema, openapi-coverage,
ruff-engines-format, ruff-engines-lint,
silent-except, business-asset, engines-agents-retirement,
single-agent-constructor,
cred-password, cred-apikey, cred-secret,
boundary, vue-file-size, mock-data
```

Frontend job：

```text
vitest, vite-build, prettier, eslint, dashed-whitelist,
vue-tsc, prettier-ts, style-gates, cred-frontend
```

`django-check`、`pytest-collect`、`vitest`、`vite-build`、`prettier`、`vue-tsc` 是正确性与格式门禁，不是写法规则。它们和 lint 一起跑，失败同样挡提交。
