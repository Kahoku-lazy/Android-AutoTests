# tests 索引 — 测试口径与文档导航

> **层级**：根 `AGENTS.md` → **本文件（口径 + 索引）** → `.agents/docs/tests/**`（分层执行细节）
>
> 本文件定义 **测试口径与红线**；目录约定、夹具与执行细节在下列文档里。口径冲突时以本文件为准。

## 简介

`tests/` 只做四件事：**功能级灰盒**、**浏览器 b2b**、**落库校验**（并入灰盒用例末尾）、**页面加载性能预算**（`tests/perf/`，默认不跑）。

单元测试不放在这里 —— 写代码时就地测一次，脚本放 `temps/`，不提交、不进 CI、不要求后人维护。

## 测试口径（红线）

1. **只收四类**：功能灰盒（`tests/<模块>/api/`、`tests/<模块>/integration/`）、浏览器 b2b（`tests/<模块>/e2e/`）、落库校验（写在灰盒用例末尾，不单独建目录）、页面加载性能预算（`tests/perf/`，只收 `perf` marker，未设置 `PERF_RUN=1` / `PERF_BASE_URL` 时一律跳过）。
2. **禁止新增单元测试**：`tests/<模块>/unit/` 已整体迁出（2026-11-24），不得再建。按函数 / 分支 / 边界值写的用例一律不进 `tests/`。
3. **颗粒度 = 功能**：一个功能一条用例，断言"调用方或用户能观察到的结果"。禁止把同一个功能拆成多条按函数或按分支的用例，对照见下节。
4. **落库校验并入灰盒**：写类功能必须在同一条用例末尾用 ORM 读回，断言"前端改过的数据确实进了库"；不另建 `db/` 层。
5. **唯一例外：`tests/arch/unit/` 契约守护** —— 零 I/O、只读源码断言前后端两侧一致（API 路径、鉴权姿态、表单校验、响应形状）。它不测业务函数实现，不受第 2 条约束；新增只允许这一类"一致性守护"。

## 四类测试怎么落地

| 类型 | 落位 | 一条用例长什么样 | 例子 |
|---|---|---|---|
| 灰盒（功能） | `tests/<模块>/api/` 或 `tests/<模块>/integration/` | 走完整功能链路（登录 → 建 → 查 → 删），断言结果状态与关键字段；写操作末尾 ORM 查库 | 仪表盘数据拉取是否正确；平台助手"新建 → 列表出现 → 删除 → 列表消失"是否闭环 |
| 浏览器 b2b | `tests/<模块>/e2e/` | Playwright 真实浏览器点交互，断言用户可见的提示词 / 弹窗 / 列表变化 | 工作流新建后是否弹出"新建已完成" |
| 落库校验 | 灰盒用例末尾（不单独建目录） | 前端触发写操作后 ORM 读回该行，断言字段值已同步 | 前端改完助手名后，`AIAssistant.name` 已是新值 |
| 契约守护（例外） | `tests/arch/unit/` | 读源码 / 路由表做一致性断言，不启服务、不连库 | 前端调用路径与后端路由表一致 |
| 页面加载性能 | `tests/perf/` | Playwright 冷缓存上下文跑 N 轮，取中位数与 `budgets.json` 逐项比较；空壳页判失败 | `/login` 的 LCP 与首屏传输是否超预算 |

### 颗粒度对照（写用例前先确认这条）

- ✅ 一个功能一条用例：`test_platform_assistant_create_and_delete` —— 新建 → 列表可见 → 删除 → 列表消失 → 库里无残留。
- ❌ 按函数拆：`test_create_serializer_validate`、`test_delete_view_status_code`、`test_model_str`。
- ❌ 按分支拆：`test_login_empty_password`、`test_login_too_long`、`test_login_unicode`（除非这些分支本身就是需求方点名的功能）。

### 性能预算怎么跑（`tests/perf/`）

1. 阈值真相源：`tests/perf/budgets.json`，按 `dev`（5173，未打包）/ `preview`（4173，生产构建）两档登记 `lcp_ms` / `load_ms` / `transfer_kb` / `requests`；同文件顶部 `basis` 记实测口径与「为什么是这个数」，`baseline` 记当次中位数。
2. 默认不跑；显式开启：`PERF_RUN=1 python -m pytest -c tests/pytest.ini -m perf`，需要前端已启动（`python -m run status` 确认）。本机 `deepeval 4.3.5` 的插件在收尾打印 skip 报告时会被 `[/login]` 触发 `rich` 标签错误，实测加 `-p no:deepeval` 规避（缺陷细节见 `openspec/changes/add-page-load-perf-budget/tasks.md` §7）。
3. 生产口径：`$env:PERF_BASE_URL="http://localhost:4173"; $env:PERF_PROFILE="preview"`（先 `npx vite build` + `npx vite preview --port 4173`）。
4. 明细落 `tests/reports/perf/page-load-*.json`（不入库）；空壳页（`renderedChars == 0`）一律判失败，不算"加载很快"。
5. 阈值调整必须写清依据（哪台机、什么构建、几轮中位数），不许为了让红变绿而放宽。
6. **字体前置**：`transfer_kb` 预算按「含 24.1MB 本地中文字体」标定（`requires_fonts: true`）。字体二进制不入库，缺失时用例**带原因 skip**，不许把 2MB 传输当通过；补齐方式见 `tests/perf/budgets.json` 的 `fonts_note`。

## 单元测试怎么办

1. 写代码时就地跑一次，脚本放 `temps/`（该目录已被 `.gitignore` 忽略）。
2. 不提交、不进 CI、不要求他人维护 —— 代码重构时直接丢弃重写。
3. 某条单元断言确实值得长期守住，把它改写成**灰盒用例**（走功能链路）或**契约守护**（读源码断言一致性），不要留在 `temps/` 里当资产。
4. 存量单元用例已整体迁出，见文末「迁移记录」；`engines/` 模块头里指向旧 `tests/engines/**/unit/` 的「测试」引用已随迁移一并清掉（无测试可指的写成 `1. 暂无`）。

## 代码规范

1. 所有的测试用例文件名称 **必须** 以 `test_` 开头。
2. 测试报告统一输出到 `reports/` 目录。

## 怎么用

1. 先读上面的「测试口径」与「代码规范」。
2. 新增 / 迁移测试目录、查某模块当前的落位与状态 → [tests_directory_conventions.md](../.agents/docs/tests/tests_directory_conventions.md)。
3. 按层改：灰盒（接口 + 集成 + 落库校验）→ [tests_integration_and_api.md](../.agents/docs/tests/tests_integration_and_api.md)；
   浏览器 b2b → [tests_e2e.md](../.agents/docs/tests/tests_e2e.md)；
   契约守护 → [tests_unit_and_contract_parity.md](../.agents/docs/tests/tests_unit_and_contract_parity.md)。
4. 跨层改动（例如新增接口用例同时动了 YAML、脚本与夹具）→ 相关的两篇都要读，契约守护那篇尤其要读。

## 主题 → 文档

| 主题 | 文档 | 讲什么 |
|------|------|--------|
| 目录约定 + 迁移状态 | [tests_directory_conventions.md](../.agents/docs/tests/tests_directory_conventions.md) | 一级按模块、二级按类型的目录；哪些层还在、哪些已退役；`__init__.py` 必要性 |
| 契约守护（原单元层） | [tests_unit_and_contract_parity.md](../.agents/docs/tests/tests_unit_and_contract_parity.md) | `tests/arch/unit` 的例外范式：只读、只做一致性断言、零外部依赖、按调用形态扫描、例外显式、规模下限；单元层退役说明 |
| 灰盒层（接口 + 集成 + 落库校验） | [tests_integration_and_api.md](../.agents/docs/tests/tests_integration_and_api.md) | 功能级灰盒的落位与写法；`api_kit` 共享设施、Jsonschema 断言、YAML 用例要求；落库校验怎么写 |
| b2b 层（浏览器端到端） | [tests_e2e.md](../.agents/docs/tests/tests_e2e.md) | 用例落位与选择器集中、提示词 / 弹窗断言、零密钥、环境前置与 skip、每步留痕、步骤报告 |

## 迁移记录

- **2026-11-24**：`tests/**/unit/` 下单元用例整体迁至 `temps/tests-unit-archive/`（118 个用例文件，含 `__init__.py` 共 134 个文件，分属 15 个 `unit/` 目录）；`tests/` 只保留 `arch/unit` 契约守护。
  同时：删除随之变空的 `tests/engines/`（引擎用例已全部迁出）、`pytest.ini` 增加 `norecursedirs = temps`（防止 `temps/` 下的临时与归档用例被收集）。
  回退：`git checkout 41dbdc71 -- tests/<模块>/unit tests/engines`（副本同时保留在 `temps/tests-unit-archive/tests/` 下，路径与仓库内一致）。
- **2026-11-24（续）**：`engines/` 56 个模块头的「测试」字段清理完毕 —— 删掉指向已迁出用例的条目并重排编号，无剩余条目的写 `1. 暂无`，`时间` 同步为 2026-11-24；模块 docstring 之外的 AST 零变化（`temps/verify_docstring_only.py` 校验 56/56）。
  规格侧口径变更单：`openspec/changes/align-spec-guards-with-test-policy/`（把 4 个规格里「由 `tests/graybox/unit` 的单元测试断言」改为「由 `tests/arch/unit` 的契约守护断言」）。
- **2026-11-24（续二）**：新增第四类「页面加载性能预算」——`tests/perf/`（采集引擎 + 会话夹具 + 两份预算 + 2 条用例），
  `pytest.ini` 注册 `perf` marker。默认不跑（`PERF_RUN=1` / `PERF_BASE_URL` 才执行），收集数 541 → 543。
  口径依据：`openspec/changes/add-page-load-perf-budget/`。
  回退：删 `tests/perf/`、回退 `pytest.ini` 的 `perf` marker 与本文件第 1 条。
- **2026-11-26**：`tests/perf` 的 `transfer_kb` 预算重标定 —— UI 字体改为 24.1MB 本地原始 TTF 后，首屏传输从 1.2/1.4MB 变为 25.7/25.9MB（preview）与 30.9/31.1MB（dev），
  预算抬到 28.3/28.6MB 与 34.0/34.3MB（实测中位数 × 1.1）；`lcp_ms` / `load_ms` / `requests` 不动。
  同时新增「字体未就位带原因 skip」的前置判定，避免字体缺失时用 2MB 传输假绿。
  依据：`openspec/changes/add-page-load-perf-budget/` D7 与 `budgets.json` 的 `basis`。
