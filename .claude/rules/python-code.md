# Python 代码约束 — Android-AutoTests

> Python 编码规范的**唯一真相源**。所有 Python 代码必须遵守本文约束。
> 架构问题（中间件/配置/模块边界）→ `backend.md` `api-conventions.md`
> 安全问题 → `security.md` | 数据库 → `database.md`

---

## 1. 命名规范

| 对象 | 规范 | 示例 |
|------|------|------|
| 变量 / 函数 / 参数 | `snake_case` | `test_runner`, `get_device()`, `user_id` |
| 类 | `PascalCase` | `Device`, `TestCase`, `TestRun` |
| 常量 | `UPPER_CASE` | `_VIRTUAL_SERIALS`, `U2_CONNECT_TIMEOUT` |
| 模块文件 | `snake_case.py` | `state_machine.py`, `execution_steps.py` |
| JSON 字段 | `snake_case` | `{"test_case_id": 1, "run_status": "OK"}` |
| 数据库表 | `{prefix}_snake_case` | `dp_devices`, `cm_test_cases` |
| Django Model 类 | `PascalCase` | `Device`, `TaskCard` |

---

## 2. 文件行数限制（阶梯式）

| 文件类型 | 上限 | 说明 |
|----------|:---:|------|
| `urls.py` | **200** | 纯路由注册，应极薄 |
| `views.py` | **300** | HTTP 入口，重逻辑抽到 api/service |
| `api.py` | **400** | 写操作函数，允许适度增长 |
| `service.py` | **400** | 内部业务逻辑 |
| `executor` / `adapter` | **500** | 执行器编排，允许更多 |
| `models.py` | 不限 | 声明式代码，行数不反映复杂度 |
| 数据导入/迁移脚本 | 豁免 | 数据非逻辑 |

**阶梯处理**（`urls.py` 除外，无阶梯直接上限）：

| 达到上限 | ⚠️ 关注，下个 PR 评估 |
| 超过 1.5 倍 | 🟠 禁止新增代码，必须附带拆分计划 |
| 超过 2 倍 | 🔴 只允许拆分重构，禁止堆代码 |

> **自查**：`find apps -name "*.py" -exec wc -l {} \; | sort -rn | head -20`

---

## 3. Import 规范

```
✅ 所有 import 放文件顶部
✅ 顺序：标准库 → 第三方 → 项目内（每组间空一行）
✅ 按需导入，不用 `from module import *`
❌ 禁止函数内 import（循环导入除外——说明架构问题，应修复而非回避）
❌ 禁止未使用的 import
```

循环导入出现时，说明两个模块的边界画错了——提取公共依赖到更底层模块，而不是用局部 import 回避。

---

## 4. 类型注解 & Docstring

```python
# ✅ 函数签名必须有类型注解
def acquire_device(serial: str, user_id: int, timeout: int = 300) -> dict:
    """锁定设备。由 views.py 或 AgentScope Tool 调用。

    Args:
        serial: 设备序列号
        user_id: 操作用户 ID
        timeout: 锁超时秒数

    Returns:
        dict: 锁记录，含 lock_id 和过期时间

    Raises:
        ValueError: 设备不存在或状态不是 ONLINE
    """
    ...

# ✅ 类必须有 docstring
class TestRunRecord(models.Model):
    """测试执行审计记录，与 TaskCard 一一对应。"""

# ✅ 模块必须有 docstring
"""Core test executor — 编排测试执行生命周期。"""
```

---

## 5. 面向对象设计约束

> 不使用抽象时，代码堆砌在一起"能跑"。但项目已 232 个 Python 文件、3 种执行器——没有设计约束的堆砌就是维护噩梦。

### 5.1 函数设计

**单一职责**：一个函数做一件事，通过命名能完整描述其行为。

```python
# ❌ 300 行 God function — 同时做: 快照用例 → 走状态机 → 创建记录 → 调 runner → 写结果 → 聚合 → 释放设备
async def _execute_tests(run_id, runner, test_cases, ...):
    ...

# ✅ 编排器 + 独立步骤 — 每个函数可独立测试
async def _execute_tests(run_id, runner, test_cases, ...):
    run_record = await _persist_run_start(client_tid, run_id, ...)   # 只做启动记录
    run_model = await runner.run(...)                                  # 只做执行
    await _persist_case_results(run_record, run_model)                # 只做结果写入
    await _finalize_run(run_record, run_model, client_tid)            # 只做终态收敛
```

**显式参数优于闭包**：通过参数显式传递数据，不用嵌套函数隐式捕获外部变量。

```python
# ❌ 闭包隐藏数据流 — 不知道 start_run 读了哪些外部变量
async def _execute_tests(run_id, runner, test_cases, ...):
    client_tid = ...
    run_record = None

    @_bg_sync
    def start_run():                    # 闭包捕获 test_cases, client_tid, run_id...
        ...tc_card = TaskCard.objects.get(task_id=client_tid)...

    run_record = await start_run()

# ✅ 显式参数 — 从函数签名就能看出读什么、返回什么
@_bg_sync
def _persist_run_start(client_tid: str, run_id: str, dev_serial: str,
                       test_cases: list, loop_count: int) -> TestRunRecord:
    ...

run_record = await _persist_run_start(client_tid, run_id, dev_serial, test_cases, loop_count)
```

**函数行数指南**：

| 函数类型 | 建议上限 | 说明 |
|----------|:---:|------|
| 编排器 (orchestrator) | **80** | 只做步骤调度，不含业务细节 |
| 业务步骤 | **60** | 一个步骤 = 一件事 |
| 纯辅助函数 | **40** | 无副作用的数据转换 |

### 5.2 类设计

**优先用函数，有必要时才用类。** 以下信号出现任一，考虑引入类：

| 信号 | 说明 |
|------|------|
| 3+ 个函数共享同一组参数 | 用类封装状态，避免参数传递链 |
| 多态行为（同类操作不同实现） | 定义 ABC，子类实现差异部分，调用方不感知 |
| 需要管理生命周期（init → use → cleanup） | 上下文管理器或生命周期模板 |
| 同一概念的状态 + 行为紧密耦合 | 数据和对数据的操作放一起 |

**模板方法模式**（项目已有 3 种执行器，但无共同接口）：

```python
# ❌ 3 个 executor 结构相似但无契约 — 改一个，另外两个不知道要不要跟着改
# ui/executor.py    UIDeviceExecutor.run()
# web/executor.py   WebExecutor.run()
# api/executor.py   ApiExecutor.run()

# ✅ 模板方法 — 固定步骤顺序，子类只填差异
class TestExecutionLifecycle(ABC):
    async def run(self, ctx: TestRunContext) -> RunModel:
        """模板方法 — 固定 6 步顺序，子类不可覆盖。"""
        await self._on_before_start(ctx)
        run_model = await self._do_execute(ctx)    # ← 子类差异
        await self._persist_results(ctx, run_model)
        await self._finalize(ctx, run_model)
        return run_model

    @abstractmethod
    async def _do_execute(self, ctx) -> RunModel: ...  # 子类必须实现

    async def _on_before_start(self, ctx): pass         # 钩子，默认空
```

**继承深度**：最多 2 层（ABC → 具体实现）。禁止 3 层及以上的继承链。

### 5.3 模块设计 — 高内聚低耦合

**高内聚**：一个模块内的所有代码为同一个目标服务。

```
✅ 好的模块边界:
  execution_steps.py  — 4 个 @_bg_sync 持久化函数 + 2 个纯辅助
  state_machine.py    — 状态转移表 + 验证 + 原子写
  callbacks.py        — WebSocket 广播协议

❌ 坏的模块边界:
  helpers.py 堆积了工具函数、状态管理、设备锁、队列调度、后台任务 — "什么都放的抽屉"
```

**低耦合**：模块间只依赖接口，不依赖实现细节。

```python
# ❌ 紧耦合 — 直接依赖具体实现
from ..callbacks import test_callbacks          # 全局单例
from apps.device_pool.api import release_device  # 具体函数

# ✅ 松耦合 — 依赖注入
class TestExecutor:
    def __init__(self, callbacks: TestCallbacks, device_mgr: DeviceManager):
        self._callbacks = callbacks              # 接口，可 mock
        self._device_mgr = device_mgr            # 接口，可替换
```

**模块拆分信号**：出现以下任一就该拆：

| 信号 | 阈值 |
|------|------|
| 模块内函数/类服务于不同目标 | > 1 个目标 |
| 模块超过行数限制 | 见 §2 |
| 模块被超过 5 个其他模块 import | 考虑提取接口 |
| 修改一个功能需要改 3+ 个模块 | 耦合过高，合并或提取中间层 |

### 5.4 组合优于继承

```python
# ❌ 通过继承复用 — 只是为了用 Device 的 serial/status 就继承它
class LockedDevice(Device):
    ...

# ✅ 通过组合复用
class DeviceLock:
    def __init__(self, device: Device, user_id: int, timeout: int):
        self.device = device          # 持有 Device 实例
        self.user_id = user_id
```

---

## 6. 文件职责分工

```
apps/{app_name}/
├── models.py     # ORM Model 定义（只定义表结构）
├── views.py      # HTTP 请求入口（解析 JSON → 逻辑 → JsonResponse）
├── api.py        # 可被跨模块调用的公共写操作函数（__all__ 白名单）
├── urls.py       # URL 路由（app_name + urlpatterns）
├── consumers.py  # WebSocket Consumer（如有）
└── service.py    # 内部业务逻辑（可省略）
```

### 6.1 models.py — 只定义表结构

```python
class Device(models.Model):
    serial = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="ONLINE")

    class Meta:
        db_table = "dp_devices"       # 必须显式指定表名
        indexes = [models.Index(fields=["status"])]
```

- 表名必须带正确前缀（`grep -rn "db_table" apps/*/models.py` 查看当前所有前缀）
- 外键用 `CASCADE` 或 `SET_NULL`，不删关联数据用 `SET_NULL`
- JSON 字段优先 `models.JSONField`

### 6.2 views.py — HTTP 入口

```python
@csrf_exempt  # JWT 鉴权替代 CSRF
def list_devices(request):
    user_id = getattr(request, "user_id", None)  # 由中间件注入
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)

    # 业务逻辑...
    return JsonResponse({"ok": True, "data": devices})
```

| 规则 | 说明 |
|------|------|
| 装饰器 | 所有 view 用 `@csrf_exempt` |
| JSON 解析 | `request.body` → `json.loads`，失败返回 400 |
| 用户身份 | 通过 `request.user_id` 获取（中间件注入） |
| 响应格式 | 始终 `JsonResponse({"ok": True/False, ...})` |
| 状态码 | 错误必须带 HTTP 状态码：400/401/403/404/409/500 |
| 简洁 | view 只做分发，重逻辑抽到 `api.py` 或 `service.py` |

### 6.3 api.py — 跨模块写操作

```python
# __all__ 控制白名单
__all__ = ["acquire_device", "release_device"]

def acquire_device(serial: str, user_id: int, timeout: int = 300) -> dict:
    """锁定设备。由 views.py 或 AgentScope Tool 调用。"""
    device = Device.objects.get(serial=serial)
    # 确保状态合法，创建锁记录...
    return lock_record
```

| 规则 | 说明 |
|------|------|
| `__all__` | 文件头显式声明导出白名单 |
| 参数 | 简单类型（str/int/dict），**不收 `request` 对象** |
| 返回值 | `dict` 或 `list[dict]`，**不返回 ORM 对象**（防止跨模块 Model 依赖） |
| 不返回 JsonResponse | 那是 views.py 的职责 |
| 异常 | 写操作可能 `raise ValueError`，调用方自行 try/except |
| 校验 | 内部做完整的参数校验和状态检查 |
| 调用方 | views.py 和 AgentScope Tool 都通过 api.py 写入 DB |

### 6.4 urls.py — 路由注册

```python
app_name = "devices"

urlpatterns = [
    path("", list_devices, name="list"),
    path("<str:serial>/lock", lock_device, name="lock"),
]
```

- `app_name` 必须与 URL 前缀一致
- 路由名用 `snake_case`
- 具体路由在通配符路由之前

---

## 7. 写操作铁律

```
前端 HTTP → Django View → api.py → ORM
AgentScope → Tool.call() → api.py → run_sync() → ORM
Django Admin → ORM（仅管理员）

❌ 禁止任何组件直接 ORM INSERT/UPDATE/DELETE
✅ 读操作放开：同模块和跨模块都可直接 ORM 查询
```

---

## 8. 异常处理

```python
# ✅ 精确捕获
try:
    tc_card = TaskCard.objects.get(task_id=client_tid)
except TaskCard.DoesNotExist:
    tc_card = None

# ✅ 状态冲突用特定异常
except sm.InvalidTransition as e:
    _log.warning("transition %s: %s", client_tid, e)

# ✅ 兜底捕获加注释（finally 中释放资源等）
except Exception:
    _log.exception("release failed")  # 兜底，不能阻断设备释放

# ❌ 禁止静默吞错
try:
    await delete_item(id)
except Exception:
    pass  # ← 禁止！

# ❌ 禁止裸 except:
except:  # ← 会吞掉 KeyboardInterrupt / SystemExit
```

---

## 9. 错误响应码

```python
# 资源不存在 → 404
if not device:
    return JsonResponse({"ok": False, "error": "not found"}, status=404)

# 状态冲突 → 409
if device.status != "ONLINE":
    return JsonResponse({"ok": False, "error": "设备不可用"}, status=409)

# 外部服务不可用 → 502
except ConnectionError:
    return JsonResponse({"ok": False, "error": "设备连接失败"}, status=502)

# JSON 解析失败 → 400
except json.JSONDecodeError:
    return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)
```

---

## 10. 响应格式

```json
{"ok": true,  "data": {...}}
{"ok": false, "error": "具体错误描述"}
```

- 错误描述面向用户，不暴露技术术语（堆栈、SQL、文件路径）
- `error` 字段始终是字符串

---

## 11. 其他

| 规则 | 说明 |
|------|------|
| 缩进 | 4 空格，不用 Tab |
| 引号 | 字符串用双引号 `"`（与 Django 项目保持一致） |
| 尾随逗号 | 多行列表/字典/参数最后加逗号 |
| 空行 | 模块级函数间 2 空行，类方法间 1 空行 |
| `__init__.py` | 即使空也要存在；可做 re-export |
| 调试代码 | ❌ 禁止 `print()` 残留，统一用 `logging` 模块 |
