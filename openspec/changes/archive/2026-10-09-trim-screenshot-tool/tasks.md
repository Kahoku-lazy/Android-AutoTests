## 1. 收敛截图工具职责（已实施）

- [x] 1.1 删掉截图工具里的两次额外设备查询（当前前台应用、屏幕尺寸），返回收敛为模型图 + 本地路径与文件名；验证：`tests/graybox/unit/test_screenshot_tool_return.py` 断言 `info.current_app` / `info.screen_size` 一次都没被调用
- [x] 1.2 确认无消费方：全仓 grep `screen_w` / `screen_h` / 截图返回里的 `package`，平台侧命中的都是设备信息与快照链路（与本工具无关）
- [x] 1.3 单测：返回只含 `screenshot_path` / `screenshot_name`；`keep_local=false` 时不落盘但仍给模型图；用完断开连接
- [x] 1.4 真机验证：本地 `inspector/shots/capture_20261009_120701_721.jpg`（1080×2340 JPEG 180KB）、模型图 591×1280 JPEG（base64 ≈65KB），返回摘要只剩路径与文件名

## 2. 回归与归档

- [x] 2.1 相关单测 6 项全绿（截图链路 4 + 截图工具 2）；`ruff check` / `ruff format --check` 通过
- [x] 2.2 归档：`openspec validate --strict` 通过；本单置 `skip_specs: true`（无需求级变化），归档时无需并入主规格

## 遗留（不在本单范围）

- 若日后确认模型需要屏幕分辨率（例如步骤直接给像素坐标），另立一单加一个只读的"设备信息"工具，而不是塞回截图工具。
