# linting —— 模块依赖规则与红线

本文是模块依赖规则的唯一说明文档。配置文件是仓库根的
[`.linting`](../../.linting)，它是**纯数据、不带注释**：所有解释性内容都在本文，改规则前先读本文。

## 1. 组成与位置

| 东西 | 位置 | 作用 |
|---|---|---|
| 配置 | 仓库根 `.linting` | 允许清单（`[[modules]]`）+ 红线（`[[forbid]]`） |
| 执行器 | `utils/linting/` | `config` 读取校验 → `scan` 抽 import → `graph` 建图 → `checks` 判定 → `report` 输出 |
| 命令行 | `python -m utils.linting` | 本地检查；退出码 0 通过 / 1 违规 / 2 配置错误 |
| 门禁 | `linting` | `utils/check_gates.py` 的阻塞项；CI 的 python job 点名 |
| 备份通道 | `python -m utils.linting export` | 按 `.linting` 生成 `tach.toml` / `.importlinter`，供第三方工具复跑 |

`tach` 与 `import-linter` 已从依赖中移除；`export` 只是回滚/对照通道，日常不用。

## 2. 模块化规则（允许清单）

规则一句话：**只有登记过的模块才受约束；每个模块只能 import 它 `depends_on` 里列出的模块。**

### 2.1 模块划分（19 个）

| 层 | 模块 | 允许依赖 |
|---|---|---|
| 平台 App | `backend.apps.accounts` | `ai_assistant` |
| | `backend.apps.ai_assistant` | `knowledge_search`、`usage_ledger`、`engines.ae_harness`、`engines.backend_bridge` |
| | `backend.apps.bug_manager` | `task_list` |
| | `backend.apps.case_manager` | 无 |
| | `backend.apps.dashboard` | `ai_assistant`、`case_manager`、`device_pool`、`task_list`、`usage_ledger` |
| | `backend.apps.device_pool` | `engines.device` |
| | `backend.apps.knowledge_search` | `ai_assistant`、`usage_ledger`、`engines.ae_harness` |
| | `backend.apps.ops_console` | `accounts`、`ai_assistant` |
| | `backend.apps.report_generator` | `ai_assistant`、`task_list` |
| | `backend.apps.serial_log` | `engines.device`、`engines.uart_log` |
| | `backend.apps.task_list` | `ai_assistant`、`bug_manager`、`case_manager`、`device_pool`、`usage_ledger`、`engines.ae_harness`、`engines.backend_bridge`、`engines.device` |
| | `backend.apps.usage_ledger` | `engines.backend_bridge` |
| 引擎包 | `engines.ae_harness` | 无 |
| | `engines.backend_bridge` | `engines.ae_harness` |
| | `engines.device` / `engines.uart_log` / `engines.vision` / `engines.utils` | 无 |
| 公共包 | `utils`（`utility = true`） | 谁都可以 import，不必逐个登记 |

### 2.2 语义细节

- **空清单 = 谁都许不**：`depends_on = []` 的模块不能 import 任何其它已登记模块。
- **`utility = true`**：`utils` 是公共包，任何模块 import 它都不需要登记。
- **`exact = true`**：清单多写一条未使用的依赖也会失败，删代码时要同步删清单。
- **未登记的代码**（`backend/shared`、`backend/gateway`、`config`、`models` 等）属于 root 模块，默认 `ignore`，谁 import 它们都不判。
- **只查直接 import**：tach 式允许清单没有间接传递检查。

## 3. 红线（禁止合同）

红线写在 `[[forbid]]`，回答“谁**绝不许** import 谁”。分四组共 16 条：

| 组 | 合同（slug） | 范围 | 禁止 |
|---|---|---|---|
| 引擎纯度 | `engines-purity` | `engines` | `django`、`backend.apps`、旧包 `apps` |
| 引擎方向 | `engine-base-direction` | `engines.device` / `vision` / `uart_log` | 反向依赖 `engines.backend_bridge`、`engines.ae_harness` |
| 引擎隔离 | `ae-harness-isolation` | `engines.ae_harness` | 其它引擎包与根 `utils` |
| 设备实现 | `no-device-implementation-leak` | `backend.apps`、`backend.gateway` | `uiautomator2`、`engines.device.android` |
| App 公开面（12 条） | `accounts-cross-app` … `usage-ledger-cross-app` | 每个 App | 其它 App 的内部模块；只放行白名单里的 `api` / `models` 等 |

12 条 App 合同的判定方式一致：**默认禁止 import 对方任何子模块，只放行 `ignore_imports` 列出的公开面**。
例如 `task-list-cross-app` 只允许：

```text
ai_assistant.api / ai_assistant.models / bug_manager.api / case_manager.api
device_pool.api / usage_ledger.api / usage_ledger.pricing
```

### 3.1 判定顺序（改规则前必须知道）

```text
同一模块？            → 放行
目标是 utility？       → 放行
命中 cannot_depend_on？→ 报错（优先于白名单）
depends_on 没写？      → 放行（本仓库每个模块都写了）
在白名单里？           → 放行
都不在？               → 报“未声明依赖”
```

红线（`[[forbid]]`）是独立的一层：先按 `ignore_imports` **删边**，再按 `allow_indirect_imports`
决定查直接边还是最短链，最后逐个 source×forbidden 组合出违规链。两套判定都跑，谁红都算失败。

## 4. 使用方法

```bash
python -m utils.linting                    # 全量检查（19 个模块的允许清单 + 16 条红线）
python -m utils.linting --json             # 机器可读，便于 CI 或脚本消费
python -m utils.check_gates --only linting # 只跑这一条门禁
python -m utils.check_gates --only boundary,linting  # 与边界检查一起跑
```

退出码：`0` 通过；`1` 有违规或多写的依赖；`2` 配置错误（含白名单表达式没匹配到任何 import）。

输出含义：

| 前缀 | 含义 |
|---|---|
| `[FAIL] <合同名>` + 缩进的链 | 红线被破，链上每一跳带 `文件:行号` |
| `[FAIL] file:line 未声明依赖 X（A → B）` | 允许清单违规 |
| `[FAIL] file:line 禁止依赖 X（A → B）` | 命中 `cannot_depend_on` |
| `[UNUSED] A 声明了未使用的依赖 B` | `exact = true` 下的多余依赖 |
| `[WARN]` | 白名单未命中但告警级别为 `warn` |

## 5. 怎么验收红线确实生效

门禁全绿只是必要条件，不能证明红线有效。按下面五步验收：

**① 常规全绿**

```bash
python -m utils.check_gates --only linting   # 期望 PASS，退出码 0
```

**② 确认每条红线都真的在检查（防“空展开”假绿）**

```bash
python -m utils.linting --json
```

看输出里 `contracts` 的数量与 `slug` 是否齐全（应为 16 条、全部 `kept: true`）。任何一条 red line
的 `source` / `forbidden` 展开为空（例如拼错的模块名）都会让该条永远通过——这类问题只能靠造违规发现，见第 ③ 步。

**③ 造违规验证（唯一能证明“会红”的方法）**

在 `temps/probe/` 建一个最小项目（`a → b → c`，`c` 被合同禁止），写入自己的 `.linting`，然后：

```bash
python -m utils.linting --root temps/probe
```

期望：退出码 1，输出形如

```text
[FAIL] a must not import c
        a -> b (a/__init__.py:1)
        b -> c (b/__init__.py:1)
```

三种红线类型都要各造一次：内部包、外部包（如 `json`）、`ignore_imports` 白名单（把违规边列进白名单后应转绿）。

**④ 白名单失效检测**

把某个 `ignore_imports` 表达式改成不存在的边后重跑，期望退出码 2 并提示
`ignore 表达式没有匹配到任何 import`。这保证白名单不会越积越多、过期后无人清理。

**⑤ 盲区审计（不改变门禁口径）**

```bash
python -m utils.linting --check-type-checking   # 连 TYPE_CHECKING 里的 import 一起查
python -m utils.linting --strict-indirect       # 连间接链一起查（无视 allow_indirect_imports）
```

两个开关只影响本次运行，不写回 `.linting`，输出会带 `[AUDIT]` 提示。当前口径下这两类都是**放过**的，
所以定期跑一次审计，可以把“藏在 `if TYPE_CHECKING:` 里”或“绕一层间接依赖”的越界找出来。

> 基线记录（2026-11-24）：`--check-type-checking` 全绿；`--strict-indirect` 有 **6/16** 条合同存在间接越界
> （如 `serial_log.views → backend.shared.users → ai_assistant.api → … → usage_ledger`）。是否把红线从
> “只查直接 import”收紧为“连间接链一起查”，属于收紧依赖方向，需按 `AGENTS.md` 第 4 条提变更申请后再改 `allow_indirect_imports`。

## 6. 已知边界

| 边界 | 现状 | 影响 |
|---|---|---|
| 仅直接 import | 16 条合同都设了 `allow_indirect_imports = true` | `A → B → C(禁止)` 不报；用 `--strict-indirect` 审计 |
| `TYPE_CHECKING` 内 import | 默认忽略（`ignore_type_checking_imports = true`） | 可以藏违规；用 `--check-type-checking` 审计 |
| 动态 / 字符串 import | 不解析 `__import__`、`importlib` | 这类越界看不见 |
| 外部包粒度 | 只到顶层包（`django`、`uiautomator2`） | 无法禁到第三方子模块 |
| 无行内豁免 | 不支持 `# linting-ignore` 之类注释 | **红线不能被局部注释掉**，只能改配置（要变更申请） |
| 运行时行为 | 只做静态 AST | 跨 App 直接写库归 `boundary` 门禁 |

## 7. 改规则的正确姿势

1. **放宽或收紧依赖方向 = 改架构**：按根 `AGENTS.md` 第 4 条先提变更申请（改什么、为什么、影响面、怎么回退），批准后才动 `.linting`。
2. 只改 `.linting`，不改 `utils/linting/` 的判定逻辑；改完按第 5 节验收一遍。
3. 新增 App：在 `[[modules]]` 加一条（先 `depends_on = []`），再给它加一条 `*-cross-app` 红线。
4. 删除依赖：代码与清单同时删，否则 `exact` 报“声明了未使用的依赖”。
5. 白名单过期先删表达式，不要修改告警级别来绕开。
