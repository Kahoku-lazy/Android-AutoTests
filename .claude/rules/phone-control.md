# Phone Control Rules — Android-AutoTests

## 技术栈

uiautomator2 + ADB (Android Debug Bridge)

## 设备连接生命周期

```
ADB 扫描 → 注册到 dp_devices (ONLINE)
    ↓
激活设备 → 设为当前活动设备
    ↓
锁定设备 → dp_device_locks 创建锁记录 → status=BUSY
    ↓
使用中... (dump UI / 截图 / 执行操作)
    ↓
释放设备 → 锁记录标记为 released → status=ONLINE
    ↓ 或
心跳超时 → 自动释放 (timeout)
```

## 设备池管理

### 核心文件

> Read `apps/device_pool/` — `pool.py`（设备连接/截图/dump）、`views.py`（HTTP API）、`api.py`（跨模块写操作）、`models.py`（表结构）。

### DevicePool 单例

`DevicePool` 是线程安全的全局单例（`pool.py`），实例名为 `device`：

```python
# 延迟初始化 — 首次访问 .d 属性时才调用 u2.connect()
@property
def d(self) -> u2.Device:
    if serial not in DevicePool._instances:
        with DevicePool._lock:           # 双重检查锁定
            if serial not in DevicePool._instances:
                DevicePool._instances[serial] = u2.connect(serial)
    return DevicePool._instances[serial]
```

- `_u2_lock` 全局串行化所有 u2 操作，防止并发冲突
- WIFI 连接通过 `adb connect ip:port` 建立
- 连接时检查 ATX Agent：失败返回 502

### 测试运行器的独立连接

测试执行时创建**独立** u2 连接，不走 DevicePool 单例：

```python
# test_runner/views.py — 每个设备独立连接
d = await asyncio.get_event_loop().run_in_executor(None, lambda: u2.connect(serial))
```

> 原因：测试执行是长时间异步任务，需要隔离的设备连接，不受设备池全局锁影响。

### 设备连接

```python
import uiautomator2 as u2

# 连接设备
d = u2.connect(serial)  # USB: serial, WIFI: ip:port

# 获取设备信息
info = d.info  # {currentPackageName, displayWidth, displayHeight, sdkVersion...}
```

### 设备状态

| 状态 | 含义 | 操作权限 |
|------|------|---------|
| `ONLINE` | 可用，未锁定 | 可连接/锁定 |
| `BUSY` | 已锁定，使用中 | 仅锁定者可操作 |
| `OFFLINE` | ADB 断连 | 不可用 |
| `DISCONNECTED` | 主动断开 | 不可用 |

## UI Dump 和元素定位

### Dump 流程（3 层回退 + XML 截断修复）

```
1. 检查设备连接状态
2. d.dump_hierarchy() — 3 种参数组合依次尝试：
   a. 默认参数
   b. compressed=False
   c. compressed=False, pretty=True
3. 检测 XML 截断：结尾不是 '>' → last_complete = raw.rfind(">") 截断修复
4. ET.fromstring() 解析 XML → 递归提取 16 个元素属性
5. 每个元素生成 8 种 XPath 候选
6. 按匹配数 (count) 升序排列
7. 返回元素列表 + 截图 base64
```

### XPath 生成策略

> Read `apps/element_locator/service.py` → `gen_xpath_candidates()` — 生成 8 种 XPath，按匹配数升序排列，优先选 count=1。

### 截图

```python
# pool.py
def screenshot_b64(quality=55, max_width=0) -> str:
    img = d.screenshot(format='opencv')
    # 压缩 + base64 编码
    return base64_str

# WebSocket 推送：2fps 定时截图 → ws/screenshot
```

## 测试步骤

> **步骤类型定义**：Read `models/step_types.py` → `class StepType(Enum)` — 唯一真相源。
> **步骤执行映射**：Read `apps/test_runner/adapter.py` → 各步骤对应的 u2 操作。

## ADB 依赖

```bash
# 必须预先安装 ADB 并配置 PATH
adb devices                          # 列出已连接设备
adb -s <serial> shell wm size        # 获取屏幕尺寸
adb -s <serial> shell wm density     # 获取屏幕密度
adb -s <serial> shell uiautomator dump /sdcard/ui_dump.xml  # UI 层级 dump
adb -s <serial> pull /sdcard/ui_dump.xml <local_path>        # 拉取 dump 文件
```

## 容错处理

| 场景 | 处理方式 |
|------|---------|
| 设备断连 | `OFFLINE` 状态，API 返回 502 |
| 元素未找到 | XPath 返回空，步骤输出 "not found" |
| Toast 未出现 | 双重检测：xpath 文本 + `d.toast.get_message(0)`，任一命中即返回 |
| 截图失败 | 返回错误信息，不阻塞流程 |
| u2 连接超时 | `run_sync()` 8s 超时 + 重试机制 |
| 锁超时 | `DeviceLock.is_expired` 判断，心跳同步自动释放 |
| dump XML 截断 | `raw.rfind(">")` 截断修复，失败则抛 RuntimeError |
| 文本输入失败 | set_fastinput_ime → 降级到 `adb shell input text`，最后恢复原输入法 |
| ATX Agent 未运行 | 返回 502 "设备 ATX Agent 未运行，请在设备端启动 uiautomator2 服务" |
| 测试中断 | `should_stop()` 每 100ms 检查，所有步骤返回 "stopped" |

## 离线工具

```bash
python tools/dump_ui.py         # 不依赖 Django，直接 dump UI → ui_data.json + screenshot.png
python tools/generate_html.py   # 生成自包含 phone_ui.html 检查器（离线查看 UI 层级）
```
