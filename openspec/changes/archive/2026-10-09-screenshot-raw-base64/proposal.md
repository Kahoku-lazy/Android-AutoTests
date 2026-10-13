## Why

截图现在被压两次（设备层先压 JPEG 质量 55，引擎再缩再压一次送模型），模型看到的是已经掉过细节的图；落盘文件名精确到微秒、且扩展名 `.png` 里装的其实是 JPEG，看图工具会拒读。用户要求：**取原始帧后直接转 base64 给模型，另外保存一张本地图，工具同时返回 base64 与本地路径，本地图名用毫秒精度时间戳**。

## What Changes

- 截图链路改为**从原始帧只编一次**：模型输入 = 原始帧 → 最长边 1280 → JPEG 85 → base64（不再经中间压缩）。
- **另存一张本地图**：原始帧 → 全分辨率 → JPEG 90，文件名 `capture_YYYYmmdd_HHMMSS_mmm.jpg`（**毫秒**精度），扩展名与真实格式一致。
- **工具返回同时给出**给模型的 base64 与本地图片相对路径（`image.base64` + `summary.screenshot_path` / `screenshot_name`）。
- `keep_local=false` 时不写本地文件，但仍把 base64 给模型（保持既有开关语义）。
- 设备控制层新增"取原始帧"能力；既有 `screenshot()`（平台快照链路在用）保持不变，避免影响设备检查器。

## 关联文档

- 关联需求编号：`PRD-08-AI助手`（智能体管理 · 设备操控）。
- 说明：该子 PRD 文件尚未建立；本单需求来自使用反馈（模型看图被二次压缩、落盘命名与格式不一致）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-device-action`: 新增「截图工具只编一次并同时返回模型 base64 与本地图片路径」的需求（含毫秒命名与格式一致的口径）。

## Impact

- **引擎 · 设备层**：`engines/device/action.py`（新增取原始帧契约方法、重写截图动作的编码与落盘）、`engines/device/android/android_device.py`（原始帧实现）。
- **引擎 · 工具层**：`engines/ai/tools/tool_device.py`（截图工具改用一次编码结果，删掉重复编码函数）。
- **测试**：新增截图链路单测（一次取帧、毫秒命名、本地全分辨率、模型图档位、不落盘分支）。
- **平台与前端**：无接口变化；落盘相对路径形状不变（仍是 `inspector/shots/…`），仅文件名精度与扩展名变化，前端按 `/media/` 渲染不受影响。
- **存量数据**：历史文件仍是旧的 `.png`（实际 JPEG），本单只对新记录生效。
