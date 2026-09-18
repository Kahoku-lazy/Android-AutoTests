## Why

🟠 **仓库级 lint 门禁实际失效**（D2-7）：`ruff.toml` 的豁免清单停留在旧的 `.claude/skills/` 目录布局，而 skill 脚本现落在 `.agents/skills/**` 与 `engines/ai/skills/**`，于是 `ruff check .` 报 **229 个错误** —— `AGENTS.md`「快速上手」第 4 条与 `django-backend-check` §7 都把 `ruff check .` 当作强制命令，命令常年红灯等于门禁形同虚设。

实测分解（2026-09-15，`python -m ruff check . --statistics`）：

| 来源 | 错误数 | 性质 |
|------|-------:|------|
| `.agents/skills/skill-creator/**` | 111 | 供应商（vendored）skill 脚手架 |
| `engines/ai/skills/skill-creator/**` | 113 | 同上（另一份拷贝） |
| `tests/graybox/unit/test_case_manager_ids.py:3` | 1 | I001 —— 本会话 `fix-stale-case-id-test` 新增 import 行造成 |
| `tests/graybox/unit/test_task_progress_persist.py:3` | 1 | I001 —— 既有债 |
| `tools/cli.py:20,21,24` | 3 | F401 —— 未使用 import（既有债） |
| **合计** | **229** | |

规则分布：`T201` 146 · `Q000` 58 · `I001` 20 · `F401` 5。224 个落在两份 vendored `skill-creator` 拷贝里，只有 **5 个**属本项目自有代码。

`ruff.toml:53` 的 `".claude/skills/**/*.py" = ["T201"]` 是**指向不存在路径的死配置**：作者本意是「skill 脚本允许 print()」，但目录改名后该条既没跟上、也没能豁免任何文件。

## What Changes

- `ruff.toml`：
  - `exclude` 增 `".agents/skills/skill-creator/**"` 与 `"engines/ai/skills/skill-creator/**"` —— 两份 vendored 脚手架不适用本项目 lint 规则（改它等于下次 skill 更新即丢失）
  - 删除 `[lint.per-file-ignores]` 里指向不存在路径的 `.claude/skills/**/*.py`（`skill-creator` 被 exclude 后该条恒不命中）
- `tools/cli.py`：删除未使用的 `random` / `string` / `datetime` 三个 import（F401）
- `tests/graybox/unit/test_case_manager_ids.py`：合并 `apps.case_manager.models` 的三行 import（I001，本会话引入）
- `tests/graybox/unit/test_task_progress_persist.py`：修正 import 分组空行（I001，既有债）

- **BREAKING**：无（纯静态检查配置 + 死 import 清理；不改任何运行期行为）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 门禁真相源：`AGENTS.md`「快速上手」第 4 条（`ruff check .`）· `.agents/skills/django-backend-check/references/calibration.md` §2 🟠「`ruff check` 失败」· §7 强制命令
- 前置分析：本会话 D2 复查（缺陷 D2-7）
- **纠错**：本会话曾把 `engines/device/connection.py` 直 import `uiautomator2` 记为「引擎边界泄漏 / 绕过 `DEVICE_ENGINE`」（D5-3）—— 经 `ARCH-00-平台总体架构.md` §1.1 的 L1c 行核实为**误报**：该模块**就是** L1c 引擎层（登记能力含 `probe_u2` / `fetch_device_info`），且实测 `gen_arch_stats.py --check-boundaries` 零违规。本单不涉

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 配置：`ruff.toml`（+2 exclude、-1 死 per-file-ignore）
- 源码：`tools/cli.py`（-3 import 行）
- 测试：`tests/graybox/unit/test_case_manager_ids.py` · `tests/graybox/unit/test_task_progress_persist.py`（仅 import 块）
- 验证：`python -m ruff check .` 必须 0 错 · `pytest tests/graybox/unit -q` 不回归
- 不在本单范围：`ruff format --check` 报的 9 个既有未格式化文件（🟡 债，见 `design.md`）
