## Context

`ruff check .` 是 `AGENTS.md` 与 calibration §7 指定的强制命令，实测 **229 错**。根因是「vendored skill 脚手架」与「本项目代码」共用同一条 lint 通道，而豁免清单用的是已废弃目录名（`.claude/skills/`）。

## Goals / Non-Goals

**Goals:**

- `python -m ruff check .` 归零，让该命令重新可作为关单门禁
- 清理本会话自己引入的 I001（`fix-stale-case-id-test` 的残留）

**Non-Goals:**

- 不修 vendored `skill-creator` 脚本里的 224 个错（Q000 / T201 / I001 / F401）—— 供应商产物，改了会在下次 skill 更新时丢失
- 不 reformat `ruff format --check` 报的 9 个文件 —— 与本单「lint 门禁」不同根因，属 🟡 格式债，另行处理以免 diff 里混入无关重排

## Decisions

### 1. 用 exclude 而非 per-file-ignores 处理 vendored 脚手架

- **选择**：`exclude` 精确到两份 `skill-creator` 目录
- **理由**：per-file-ignores 只能按规则逐条放宽，而 vendored 脚本需要放宽的是 4 类规则、未来还可能引入新规则；exclude 表达的是「这段代码不属本项目规范管辖」，语义更准、维护成本更低

### 2. exclude 精确到 `skill-creator` 子目录，而不是整个 `skills/`

- **选择**：`.agents/skills/skill-creator/**` + `engines/ai/skills/skill-creator/**`
- **理由**：`.agents/skills/` 下另有本项目自写的 skill（`django-backend-check` / `boundary-check` / `doodle-craft` / `vue-frontend-check` 等），其中的脚本若存在仍应受本项目规范约束；实测这 229 错也未命中这些目录

### 3. 删除 `.claude/skills/**/*.py` 死配置

- **选择**：删掉 `per-file-ignores` 中该条
- **理由**：该路径在仓库中不存在（旧目录布局残留），`skill-creator` 被 exclude 后更无可命中对象；保留会让下一位读者误以为 skill 脚本仍在 lint 覆盖内

### 4. 两个测试文件的 I001 用 `ruff check --fix` 而非手改

- **选择**：跑 safe fix（I001 属可自动修复）
- **理由**：isort 的合并/空行规则由工具保证，手改易再犯；改动限于 import 块，可精确 review

## Risks / Trade-offs

- [隐性放宽] → 仅放宽两份 vendored 目录，本项目自有代码仍全量受检；`ruff check .` 归零后任何新错都会立即暴露
- [测试文件改动风险] → 只动 import 块，跑 `tests/graybox/unit` 全量确认无回归

## Migration Plan

1. 改 `ruff.toml`（+2 exclude、-1 dead ignore）
2. `ruff check --fix` 修两个测试文件的 I001；手工删 `tools/cli.py` 三个死 import
3. 验证：`python -m ruff check .` → 0 errors；`pytest tests/graybox/unit -q` 无回归
4. 归档；回滚 = `git checkout ruff.toml tools/cli.py tests/graybox/unit/test_case_manager_ids.py tests/graybox/unit/test_task_progress_persist.py`
