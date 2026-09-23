## 1. 对照 CI 原文，固化检查口径

- [x] 1.1 逐条抄录 `.github/workflows/ci-phase1.yml` 六个 job 的全部检查，形成 20 项清单：backend-check（manage.py check · ruff format · ruff lint）· frontend-check（npm test · vite build · prettier vue/js/css）· advisory-checks（ruff engines 格式与 lint · eslint · vue-tsc · prettier .ts）· security-scan（5 条凭据规则）· boundary-check（gen_arch_stats --check-boundaries）· frontend-quality（gen_arch_stats --check-frontend · 硬编码假数据 · 内联样式体积）
- [x] 1.2 记录三段内联脚本的原文口径并逐条对齐：
  - 凭据扫描 5 条规则的正则与排除串逐条照搬（`password\s*=\s*'[^']+'` 排除 `password\s*=\s*''` 与 `PASSWORD`；`(api_key|apikey|API_KEY)\s*=\s*'sk-[A-Za-z0-9]+'`；`'admin123'|'autotests2026'|'password'\s*[:=]` 排除 `PASSWORD`/`test`/`__pycache__`；`(secret_key|SECRET_KEY|private_key)\s*=\s*'[^']+'` 排除 `os.environ`/`getenv`；前端 `(api_key|password|token|secret)\s*[=:]\s*['\"]\w{8,}` 排除 `node_modules`/`.test.`）
  - 硬编码假数据：`ref\(\s*\[\s*\{[^}]*id:` → 命中即失败（阻塞）
  - 内联样式体积：阈值 120 行
  - **分级差异（按 CI 实际行为，不按注释）**：规则 3「常见默认密码」与内联样式体积在 CI 中**只打印、不置违规**（前者不设 `VIOLATIONS=1`，后者带 `|| true`），故本地归为告警项
  - **两处显式差异（已核对并记录）**：① 内联样式检查在 CI 中因 bash 未开 globstar，`frontend/src/modules/**/*.vue` 实际只展开一层；本地改为递归遍历（范围更完整，且该项为告警不影响结论）。② CI 的 `python manage.py check --deploy` 带 `|| true`、不参与判定，本地未纳入
  - 走查时跳过 `node_modules` / `__pycache__` / `.venv` / `dist` / `.git` / `.pytest_cache`（不改变判定口径，仅避免扫进依赖与缓存）

## 2. 实现检查脚本

- [x] 2.1 新建 `tools/check_gates.py`：声明式 `Gate` 清单（名称 · 描述 · 级别 · 执行器）+ 统一执行器；`python tools/check_gates.py` 可独立运行
- [x] 2.2 接入工具链阻塞项：Django 系统检查 · ruff 格式（平台范围）· ruff lint（平台范围）
- [x] 2.3 接入前端阻塞项：前端单元测试 · 前端构建 · prettier（`src/**/*.{vue,js,css}`）
- [x] 2.4 接入脚本类阻塞项：`tools/gen_arch_stats.py --check-boundaries` 与 `--check-frontend`
- [x] 2.5 按 CI 原文重写三段内联检查为等价 Python（对照结果见 1.2）
- [x] 2.6 接入四道告警项：ruff（`engines/` 格式与 lint）· eslint · vue-tsc · prettier（`.ts`）
- [x] 2.7 实现输出格式与退出码：每项一行结论 + 失败项摘要 + 结尾汇总；退出码逻辑抽为 `exit_code()` 并通过 4 组构造用例验证（全通过 → 0；仅告警失败 → 0；有阻塞失败 → 1；两者都失败 → 1），全部符合预期

## 3. 接入 CLI

- [x] 3.1 `run.py` 新增 `check` 子命令（choices + 分发 + 文档串），以子进程调用脚本并透传退出码；实跑比对两条入口的 20 行结论**逐行一致**（无差异）

## 4. 实跑核对基线

- [x] 4.1 `python run.py check` 实跑完成，结论见文末基线记录；模块边界检查通过（与预期一致）
- [x] 4.2 告警项结论与预期一致：ruff（`engines/`）两项通过 · eslint 通过（69 警告、退出码 0）· vue-tsc 未通过（3 处报错，均在 `ProjectTree.vue`）· prettier（`.ts`）未通过（98 个文件）
- [x] 4.3 退出码由阻塞项决定，已用构造用例验证（见 2.7）；实跑中"告警 2 项未通过 + 阻塞 3 项失败"→ 退出码 1，符合约定
- [x] 4.4 `python -m ruff check tools/check_gates.py run.py` 与 `ruff format --check` 均通过（期间修正 1 处 import 分组、1 处格式）

## 5. 收尾

- [x] 5.1 `AGENTS.md`「项目工具」登记 `python run.py check`，说明作用、退出码约定与唯一真相源位置

---

## 基线记录（2026-09-23 本地实测，`python run.py check` 首次真实运行）

阻塞项 **10/13 通过，3 失败**；告警项 **5/7 通过，2 未通过**；退出码 1。

| 门禁 | 级别 | 结论 |
| --- | --- | --- |
| Django 系统检查 | 阻塞 | 通过 |
| Python 格式 / lint（平台范围） | 阻塞 | 通过 |
| 前端单元测试 / 构建 | 阻塞 | 通过 |
| prettier（vue/js/css） | 阻塞 | **失败：109 个文件格式不合规** |
| 硬编码凭据扫描（5 条规则） | 阻塞 | **失败：前端规则命中 2 处（经查为误报，见下）** |
| 模块边界检查 | 阻塞 | 通过 |
| Vue 文件体积（<500 行） | 阻塞 | **失败：6 个文件超标**（最大 `PageFlowVueFlow.vue` 868 行） |
| 硬编码假数据 | 阻塞 | 通过 |
| ruff（`engines/`）格式与 lint | 告警 | 通过 |
| eslint | 告警 | 通过（69 条警告、0 报错，退出码 0） |
| vue-tsc | 告警 | **未通过：3 处报错**（均在 `ProjectTree.vue`） |
| prettier（`.ts`） | 告警 | **未通过：98 个文件** |
| 常见默认密码 / 内联样式体积 | 告警 | 无命中级问题（内联样式 >120 行者 12 个，仅提示） |

### 两项值得单独记录的发现

1. **前端凭据扫描命中 2 处，均为误报**：命中的是 Vue 的密码输入框绑定 `v-model:password="loginPassword"`，被正则 `(api_key|password|token|secret)\s*[=:]\s*['\"]\w{8,}` 当作硬编码凭据。该正则直接照搬 CI 原文，因此**CI 上同一规则也会误报**——只是 CI 从未真正执行过，这个误报一直没被发现。修不修属独立决策（修则需要收紧规则，超出本变更"逐条对齐"的范围）。
2. **Vue 文件体积超标是 6 个而非 1 个**：此前仅看到 CI 日志末行得出的印象不准确；本次完整输出为 6 个超标文件（868 / 722 / 675 / 613 / 602 / 528 行）。
