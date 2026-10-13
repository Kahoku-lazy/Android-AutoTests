## 1. 设备动作层：原始帧与一次编码（已实施）

- [x] 1.1 设备控制契约新增"取原始帧"方法（无损字节），Android 实现用 PNG；验证：`python -c "import engines.device.action"` 通过、`ruff check engines` 通过
- [x] 1.2 截图动作改为"原始帧 → 只编一次"：模型图（最长边 1280 / JPEG 85 → base64）+ 本地图（全分辨率 / JPEG 90 / `capture_YYYYmmdd_HHMMSS_mmm.jpg`）；验证：新增单测断言只取一次帧、毫秒命名、本地全分辨率、模型图在档位内
- [x] 1.3 `keep_local=false` 分支：不写本地文件、路径留空，但仍返回模型图；验证：单测断言不产生 `inspector/` 目录且 base64 非空
- [x] 1.4 工具层改用一次编码结果并删除重复编码函数；验证：`ruff check engines` 通过、工具返回仍为 `{"image": {...}, "summary": {...}}` 形状
- [x] 1.5 真机验证：`temps/verify_screenshot.py` 实测本地文件 `capture_20261009_115955_995.jpg`（1080×2340 JPEG 180KB）、模型图 591×1280 JPEG（base64 ≈65KB）
- [x] 1.6 全仓 grep 消费方（按 `.png` 硬筛、`image_bytes`、`screenshot_b64`）：确认无引擎外消费方受影响

## 2. 回归与归档

- [x] 2.1 截图链路单测 4 项全绿；`pytest tests/graybox/unit -q -k "screenshot or device or tool"` 无新增失败
- [x] 2.2 门禁：`python manage.py check`、`ruff check` + `ruff format --check`（相关路径）、`python tools/gen_arch_stats.py --check-boundaries`
- [ ] 2.3 归档：`openspec validate --strict` 通过，delta 同步进主规格

## 遗留（不在本单范围）

- 模型图档位对照实验（1280/q85 与 1600/q90）：不改代码即可跑，用数据再决定是否常设。
- 存量历史文件的命名/扩展名（旧 `.png` 内实为 JPEG）：本单只对新记录生效。
