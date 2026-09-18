## Context

`models/` 是 D4 规定的枚举 SSOT，但全部 13 个枚举用 `(str, Enum)`，其 `str()`/f-string 输出限定名。这既是潜在写库错值，也是 D4-1 字面量收敛的阻塞。

## Goals / Non-Goals

**Goals:**

- 消除 `models/` 内 `(str, Enum)` 的 `str()` 语义陷阱，使「枚举成员当字符串用」与「取 `.value`」等价
- 用动态发现的门禁把该不变量固定下来

**Non-Goals:**

- 不做 D4-1 的字面量替换（本单只拆地雷，替换是下一个变更）
- 不动 `models/step_types.py` 的裸 `Enum`（非 str 混入，另一语义）
- 不碰 `apps/*/models.py` 的 `choices` 与字段默认值（避免触发迁移）

## Decisions

### 1. 用 `enum.StrEnum` 而不是自定义 `__str__`

- **选择**：标准库 `StrEnum`（py3.11+，本项目 `target-version = "py313"`，实测解释器 3.13.14）
- **理由**：标准库已把 `__str__`/`__format__`/`__repr__` 与 `str` 的对齐处理正确（含 `hash` 继承 `str`），自写 `__str__` 无法覆盖 `__format__` 的全部路径，且增加维护面

### 2. 一次覆盖 `constants.py` + `test_models.py` 全部 13 个

- **选择**：同一缺陷类、同一 SSOT 包，一并迁移
- **理由**：半个包迁移会让「`models/` 的枚举是安全的」这一心智模型不成立，下一位读者仍要逐文件确认基类

### 3. 门禁用动态发现

- **选择**：遍历模块的 `vars()` 取出 `Enum` 子类，逐个断言
- **理由**：硬编码清单会在新增枚举时静默失效；动态发现让新枚举自动纳入，无需改测试

## Risks / Trade-offs

- [是否有消费方依赖旧的 `str()` 输出] → 实测消费方全部走 `.value`（`test_models` 的 `terminal_values` / `fail_values` / `choices`；`constants` 的生产消费方仅 `device_pool/contracts.py` 的转发）。改基类反而修正了 `str()`
- [是否触发迁移] → 未改任何模型字段与 `choices`；`makemigrations --check` 必须仍为 `No changes detected`
- [`StrEnum` 与 `str, Enum` 在 `json`/`dict` 键上的差异] → 实测四象限一致（`json.dumps(m)` 与 `json.dumps({m: 1})` 均输出取值）

## Migration Plan

1. 改两个模块的 import 与基类
2. 新增动态发现门禁测试
3. 验证 `manage.py check` · `makemigrations --check` · `ruff` · 全量单测 · `--check-boundaries`
4. 归档；回滚 = `git checkout models/constants.py models/test_models.py` + 删测试
