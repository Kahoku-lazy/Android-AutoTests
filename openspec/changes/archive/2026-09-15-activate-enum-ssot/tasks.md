## 1. 复核（已完成）

- [x] 1.1 读契约真相源：`设计方案-Django设计系统分层.html` 行 269 / 331 / 375 均写「枚举与领域类型唯一真相源在 `models/`」
- [x] 1.2 实测 `models/constants.py` **零外部消费**（全仓唯一匹配是它自己的 docstring 示例）
- [x] 1.3 实测 `models/` 四模块消费面：`ui_nodes.Node` ✅ 生产在用（`engines/device/base.py` · `engines/device/android/u2.py`）· `constants` ❌ 0 · `step_types` ❌ 0（`StepResult`/`CaseType` 外部零命中）· `test_models` ⚠️ 仅 `tests/graybox/unit/test_example_unit.py`
- [x] 1.4 确认 `apps/device_pool/contracts.py` 重复定义了 `DeviceStatus` / `ConnectionType`，成员与值与 `models.constants` 逐字一致
- [x] 1.5 确认既有调用方形态：`manager.py:26` 走 `from .contracts import ...` —— 保持该导出面即可零调用方改动
- [x] 1.6 量化续做面：`device_pool` 内约 70 处字面量；`LockStatus.ACTIVE="active"` / `LockReleaseReason.MANUAL="manual"` 为 `name≠value`（`Enum.__hash__` 基于 name，当字典键会与字面量键失配）

## 2. 修改

- [x] 2.1 `apps/device_pool/contracts.py`：删 `DeviceStatus` / `ConnectionType` 类定义，改 `from models.constants import ConnectionType, DeviceStatus`（转发导出）
- [x] 2.2 新增 `tests/graybox/unit/test_enum_ssot.py`：`is` 同一对象 + 成员值一致 + `str, Enum` 语义保持

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → **`No changes detected`**（枚举定义搬家未触碰模型字段默认值）
- [x] 3.2 `python -m ruff check .` → **All checks passed!**（`contracts.py` 首次引入的 I001 已修复）；`ruff format --check .` → **245 files already formatted**
- [x] 3.3 新测试 **3 passed**；**回退到 HEAD 后 2 failed**（`assert <enum 'ConnectionType'> is <enum 'ConnectionType'>` —— 两份定义的确凿证据），证明是真门禁
- [x] 3.4 `pytest tests/graybox/unit tests/arch -q` → **95 passed**（改动前 92 + 新增 3）；`--check-boundaries` → 零违规
- [x] 3.5 复扫 `apps/device_pool/*.py` → `class DeviceStatus` / `class ConnectionType` **零命中**；范围核对 `git diff --numstat` = contracts.py 3/15 · 新增测试 48 行

## 4. 续做（D4-1 剩余，需独立变更）

1. `device_pool` 内约 70 处字面量 → 枚举成员；⚠️ `LockStatus` / `LockReleaseReason` 的 `name≠value` 陷阱
2. `models/step_types.py` 零消费（随 `test_runner` 下线失活）—— 删除或保留需先判定 `config/api_docs.py` 文本与 ARCH-00 叙述是否同改
3. `models/test_models.py` 仅测试消费 —— 同上
4. `apps/ai_assistant` 侧字面量（`"failed"` / `"running"` / `"dashscope"` 等）未使用任何 `models/` 枚举，属同一缺陷域的另一半
