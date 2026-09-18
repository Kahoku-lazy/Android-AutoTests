## 1. 复核（已完成）

- [x] 1.1 实测 `str, Enum` 陷阱：`str(DeviceStatus.ONLINE)='DeviceStatus.ONLINE'` · `f"{LockStatus.ACTIVE}"='LockStatus.ACTIVE'`
- [x] 1.2 实测 `Device._meta.get_field("status").get_prep_value(DeviceStatus.ONLINE)` **原样返回成员**（Django 不强制 `str()`）→ 落库值交驱动决定，MySQL 的 `%s` 参数化会写错值
- [x] 1.3 实测 `enum.StrEnum` 对照四象限：`str`/`f-string` 均返回取值；`isinstance(str)` / `==` / `hash` / `json.dumps`（值与其作字典键）与旧基类一致
- [x] 1.4 定性严重度：全仓「枚举成员 → ORM 字段」赋值点 **0 处**（唯一命中是 `contracts.py` 的 dataclass 默认值）→ **潜伏** 写库错值陷阱，非现网 bug → 🟠
- [x] 1.5 全仓枚举盘点：`models/constants.py` 10 个 + `models/test_models.py` 3 个为 `(str, Enum)`；`models/step_types.py` 3 个为裸 `Enum`（非 str 混入，不属本缺陷类）
- [x] 1.6 确认消费方形态：`test_models` 的 `terminal_values` / `fail_values` / `choices` 与唯一消费测试 `test_example_unit.py` 全部走 `.value`

## 2. 修改

- [x] 2.1 `models/constants.py`：`Enum` → `StrEnum`，10 个基类 `(str, Enum)` → `(StrEnum)`
- [x] 2.2 `models/test_models.py`：同上 3 个
- [x] 2.3 新增 `tests/graybox/unit/test_ssot_enum_strenum.py`：动态发现（`obj.__module__ == module.__name__` 过滤，排除 `enum` 基类）+ 4 项不变量断言

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → **`No changes detected`**
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → **246 files already formatted**
- [x] 3.3 新测试 **4 passed**；**回退到 HEAD 后 `test_member_stringifies_to_value` FAILED**，报出 **45 个违规成员**（如 `DeviceStatus.ONLINE: str='DeviceStatus.ONLINE' value='ONLINE'`）—— 正是本单要拆的地雷；其余 3 条不变量在旧基类下本就成立（故未失败），符合预期
- [x] 3.4 `pytest tests/graybox/unit tests/arch -q` → **99 passed**（改动前 95 + 新增 4）；`--check-boundaries` → 零违规
- [x] 3.5 复扫 `models/*.py` → `(str, Enum)` **零命中**；范围核对 `git diff --numstat` = constants.py 12/12 · test_models.py 4/4 · 新增测试 68 行

## 4. 续做

1. **D4-1 字面量收敛现在安全了**：`StrEnum` 已是前置条件，`LockStatus.ACTIVE` / `LockReleaseReason.MANUAL` 这类 `name≠value` 的枚举也可安全替换进 `device_pool`（约 70 处）
2. `models/step_types.py` 的裸 `Enum` 是否改 `StrEnum`，取决于 STEP 域是否有「成员写 CharField」的需求；当前无消费方，不属本缺陷类
3. `models/constants.py` 的 10 个枚举中仍有 8 个零消费（本单只修基类，未处理消费面）
