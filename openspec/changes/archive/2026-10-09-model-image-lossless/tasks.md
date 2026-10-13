## 1. 模型图改为无损原尺寸（已实施）

- [x] 1.1 设备动作层：模型图编码由"最长边 1280 / JPEG 85"改为"原尺寸 / 无损 PNG"，媒体类型改为 `image/png`，去掉模型侧缩放与质量档位；验证：`ruff check engines` 通过、`tests/graybox/unit/test_screenshot_pipeline.py` 断言 PNG 签名与尺寸等于原始帧
- [x] 1.2 本地图不变（全分辨率 JPEG 90、毫秒命名、相对路径形状不变）；验证：真机实测本地图仍为 1080×2340 JPEG
- [x] 1.3 真机验证并记录体积变化：同一张原始帧，给模型的图由 base64 ≈65 KB 变为 ≈621 KB（原尺寸 PNG），确认无缩放
- [x] 1.4 单测 6 项全绿（截图链路 4 + 截图工具 2）；`ruff check` / `ruff format --check` 通过

## 2. 归档

- [x] 2.1 门禁：`python manage.py check`、`python tools/gen_arch_stats.py --check-boundaries`
- [x] 2.2 归档：`openspec validate --strict` 通过，delta（MODIFIED 截图需求）并入主规格

## 遗留与风险（如实记录）

- 单张给模型的图由约 65 KB 涨到约 621 KB（约 9.5 倍）：视觉 token 与请求延迟会上升；若某供应商对图片体积有限制，报错如实回传，不做静默降级。
- 上下文里图片数量上限仍为 5 张；无损图会更快占满，真机回归时留意是否出现"图片被挤出上下文"导致的判断退化。
- 若日后发现成本不可接受，再按数据决定是否分档（例如"小控件区域无损裁剪 + 全图压缩"，或按步骤类型选择档位），本次不做隐藏缩放。
