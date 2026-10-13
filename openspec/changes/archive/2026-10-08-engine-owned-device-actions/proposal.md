## Why

引擎要动手机，今天必须先由平台把「平台工具函数」注入进来——设备动作的实现住在平台侧，引擎离开平台就无法驱动设备。本变更按引擎侧自建的路子解决：设备能力在引擎内分三类归口，加一层按系统选择的中转，引擎自带设备工具与登记清单；**平台侧一行不改**，引擎装配时改用自己的工具。

## What Changes

- `engines/device/android/u2.py` 更名为 `android_device.py`：文件内三个类分别承担**设备连接 / 设备信息查询 / 设备控制**，各自实现同名方法名契约；包入口另留一个只做转发的引擎门面，供既有引擎协议（`open_engine` 的消费方）继续使用。
- 新增单模块 `engines/device/action.py`：`System` 声明系统（ANDROID / IOS / WINDOWS，当前只实现 ANDROID）；三个抽象类固定**统一方法名**（例如图片点击一律 `click_img`，别名不合法）；动作类（`Click` / `LongClick` / `Swipe` / `Drag` / `InputText` / `PressKey` / `Screenshot` / `AppControl`）一个动作一个类，**每种方式一个独立函数**（坐标 / 元素（xpath、id、text）/ 图片）。
- 新增 `engines/ai/tools/tool_device.py`：引擎侧设备工具（工具函数 + 说明书），经中转模块操作设备。
- 新增 `engines/ai/tools/tool_device_catalog.py`：设备动作登记清单（名字 + 说明书 + 实现引用 + 元数据：只读 / 串行 / 是否设备动作），**纯数据、零框架依赖**。
- 引擎装配改为挂自己的设备工具：注入清单里的同名设备动作工具被跳过，保证「平台不改也能生效」。
- **apps 端零改动**；测试代码本单不写，登记为后继项。
- 非目标（明确不动）：设备日志工具、设备信息类平台工具（`current_app` / `list_apps`）、OCR、设备池台账、页面流工具、模型接入层（模型清单 / provider / 密钥 / 探测 / 模型调试台）、任务分发与记录链路、验收链路、前端页面。

## 关联文档

- `PRD-08-AI助手`（需求总纲登记的 AI 助手模块）
- `ARCH-00-平台总体架构`（§1.1 分层口径 · §1.4 四条通信通道 ③ 进程内）

## Capabilities

### New Capabilities

- `ai-device-action-dispatch`: 设备动作按目标系统分派（当前 Android，预留 iOS / PC），以及「点击」的四种定位方式（坐标 / 视觉截图坐标 / 文本 / 元素定位）；未实现的系统与方式给可读结论。

### Modified Capabilities

- `ai-device-action`: 设备动作的执行归属由「平台写工具」改为「引擎侧设备工具 + 登记清单」，并明确平台侧工具在本变更中保持现状不变；新增三类能力归口（连接 / 信息查询 / 控制）与四种点击方式的要求；保留设备可用性与占用校验、动作返回前台应用、动作发出时刻三条既有要求。
- `ai-engine-protocol`: 「引擎零 apps 依赖、业务工具经 `TaskRequest.tools` 注入」这一条要开一个精确口子——设备动作类工具不再经注入，改由引擎自带；同名注入工具在装配时被跳过；数据类工具（页面流、日志、设备池台账）仍按注入方式提供。

## Impact

- **引擎设备层**：`engines/device/android/u2.py`（方法归位）、`engines/device/action/`（新增中转与系统分派）。
- **引擎 AI 层**：`engines/ai/tools/tool_device.py`、`engines/ai/tools/tool_device_catalog.py`（新增），装配处改为引擎自带设备工具优先。
- **平台后端**：`apps/` 零改动（平台那份设备工具保持现状，继续服务外部工具通道与工具箱调试页）。
- **前端**：零改动。
- **测试**：本变更不新增测试代码（登记为后继项）；架构通道测试与边界说明按新口径复核。
