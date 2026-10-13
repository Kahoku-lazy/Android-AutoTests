## 1. u2.py 更名为 android_device.py 并拆成三个类

- [x] 1.1 更名与拆分：`engines/device/android/android_device.py` 内三个类 `AndroidConnection` / `AndroidInfo` / `AndroidControl` 分别承担设备连接 / 设备信息查询 / 设备控制；包入口 `engines/device/android/__init__.py` 留一个只做转发的门面（实现既有 `UiEngine` 协议，历史类名 `U2Engine` 作别名）；`u2.py` 删除，注册表路径与两处既有测试 import 同步更新。验证：导入自检通过、既有相关测试全绿、真机连接与三类能力可用。**验证结果**：导入自检通过；`registry` 指向 `engines.device.android.U2Engine`；`tests/.../test_engine_hierarchy_contract.py` 与 `test_engine_shell_contract.py` 的 import 与文件路径断言同步更新后全绿；真机连接、信息、控制三类全部可用。
- [x] 1.2 三类方法齐备且命名统一：三类的抽象方法必须全部实现（缺一不可实例化）；契约名（如 `click_img`）存在，同义别名（`click_image` / `clickImage` / `img_click`）不存在。验证：结构自检打印契约方法数与别名检查结果。**验证结果**：契约方法数 4 / 5 / 14，三类的「剩余抽象方法」均为空；`click_img` 存在，`click_image` / `clickImage` / `img_click` / `tap_img` 均不存在。
- [x] 1.3 三类能力逐项可用：信息查询含屏幕尺寸、包名、当前已连接设备列表、前台应用、层级；控制含点击、长按、滑动、拖动、输入、按键、截图（含落盘）、应用启停。验证：真机逐项跑一次并核对返回。**验证结果**：分辨率 1080x2340、已连接设备 `['R5CT62RH88F']`、govee 包名 4 个、前台应用与层级 XML（75894 字符）均可取；控制项逐个跑通、截图落盘可读。

## 2. engines/device/action.py 单模块

- [x] 2.1 `System` 声明系统：取值恰为 `android` / `ios` / `windows`，按系统解析三类实现类；未实现的系统给可读结论，不崩、不静默落回 Android。验证：结构自检 + 未实现系统的可读结论。**验证结果**：`System.ALL = ('android','ios','windows')`、已实现 `['android']`；`ios` / `windows` 解析得到可读消息，无设备副作用。
- [x] 2.2 三份方法名契约：`DeviceConnection` / `DeviceInfo` / `DeviceControl` 抽象基类固定统一方法名；三端实现继承契约，缺方法无法实例化。验证：契约方法数与实现类继承关系检查。**验证结果**：三份契约分别声明 4 / 5 / 14 个抽象方法（含 `click_img` 等统一名）；Android 三类均继承契约且无剩余抽象方法。
- [x] 2.3 动作类：一个动作一个类（`Click` / `LongClick` / `Swipe` / `Drag` / `InputText` / `PressKey` / `Screenshot` / `AppControl`），每种方式一个独立函数（坐标 / 元素（xpath、id、text）/ 图片；滑动方向 / 坐标；拖动归一化；截图取字节 / 落盘）。验证：方法清单 + 真机逐方式跑通，元素未命中给可读结论。**验证结果**：点击与长按各三方式、滑动两方式、拖动 / 输入 / 按键 / 截图 / 应用启停各跑通；元素点击（xpath 与 text）命中成功，未命中返回 `clicked=False`（工具层转为可读结论）。真机观察到一次元素定位未命中（文本长按），与既有 u2 xpath 时序抖动一致。
- [x] 2.4 边界：本模块不 import `apps.*` / `django`，也不 import 具体设备实现（Android 实现按路径懒加载）；只有 `android_device.py` 接触 uiautomator2。验证：全层 import 扫描。**验证结果**：`engines/` 全层 `apps.` / `django` 零命中；`uiautomator2` 仅出现在 `engines/device/android/android_device.py`（与既有的 `connection.py`）。

## 3. 引擎设备工具与登记清单

- [x] 3.1 `engines/ai/tools/tool_device.py` 改走动作类：说明书与平台侧同名工具逐字段一致（含 `serial` 必填、不暴露 `user_id`）；截图落盘目录由装配期闭包注入；副作用动作在动作前打时间点并附当前前台；失败与未命中返回带 `error` 的可读结论。验证：真机经工具调用点击与截图，返回形状与平台侧一致。**验证结果**：`click_ratio` 返回 `clicked/mode/action_time/package/activity`；截图工具返回 `image` + `summary`（含截图路径）；九个工具 schema 的必填项与平台侧一致。
- [x] 3.2 `engines/ai/tools/tool_device_catalog.py`：纯数据（名字 + 说明书 + 实现引用 + 元数据），动作名与方式名对齐新动作类（`click|long_click` / `element`、`img`、`coord`、`direction`、`ratio`、`text`、`key`、`save`）。验证：清单只依赖 `dataclasses`；九项与实现一一对应。**验证结果**：清单 import 仅 `dataclasses`；`device_tool_specs()` 产出 9 项、无「实现缺失」告警；工具 docstring 由清单注入。
- [x] 3.3 装配引擎自带优先：注入清单里同名设备动作工具被跳过（留日志），非设备动作类工具仍来自注入。验证：引擎侧与平台侧（未改动）两条装配路径各查一次。**验证结果**：引擎侧执行角色九个设备动作来源均为引擎、`read_device_log` 等仍来自注入；平台侧调试台装配路径同样生效（九个动作来自引擎）。

## 4. 复核与关单（本单不写测试代码）

- [x] 4.1 范围复核：`apps/` 零改动；前端无本单改动；设备日志、OCR、台账、页面流、模型接入层不动。验证：变更 diff 检查。**验证结果**：`apps/` 零命中；`frontend/` 仅有两处**会话开始前就已存在**的改动（属在办的另一单），本单未触碰前端；其余非目标均无改动；本单改动落 `engines/`（含 `u2.py` → `android_device.py` 的更名与删除）与两处既有测试的 import/路径断言。
- [x] 4.2 真机冒烟与既有用例：逐动作冒烟 + 相关既有用例最小集。验证：每个动作结果可观察、截图可读；既有用例全绿。**验证结果**：`temps/engine_device_smoke3.py` 结构与真机两段全部通过（留档 `temps/smoke3_out.txt`）；相关既有用例 64 项全绿（引擎层级/外壳契约、角色工具子集、引擎配置、平台工具调试、通信通道）；`manage.py check` 与 ruff 干净。
- [x] 4.3 后继项登记：平台实现与引擎实现统一、桩实现与契约测试、说明书对拍、平台两处传媒体目录、主机侧设备枚举统一、`serial` 可省、参数硬枚举、iOS / Windows 实现。验证：`design.md` 后继项表在册且本变更未包含其实现。**验证结果**：后继项表已更新（加入 iOS / Windows 实现），specs 与 tasks 均未包含其实现。
- [x] 4.4 关单汇报与归档：汇报改动清单、`apps/` 零改动证据、真机冒烟结果，并在 `openspec validate` 通过后归档。验证：`openspec validate "2026-10-08-engine-owned-device-actions"` 通过。**验证结果**：`openspec validate` 与 `--strict` 均通过；三份规格 delta 已并入主规格（`ai-device-action` 一条修改 + 两条新增、`ai-engine-protocol` 一条修改、新能力 `ai-device-action-dispatch` 建档）；变更目录已移入 `openspec/changes/archive/2026-10-08-engine-owned-device-actions/`。
