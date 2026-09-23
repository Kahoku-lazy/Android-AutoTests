## Why

AI 智能体目前判断页面只有两条路：截图像素（`screenshot_page`）与 UI 层级 dump。前者把坐标交给视觉模型目测，精确度不足；后者只覆盖原生控件，画布、图片、WebView 里的文字拿不到。而平台其实已有 OCR 识别能力（`algorithms/vision/ocr.py`），但它只挂在设备检查器的抓取链路上——该分支前端已下线（前端恒发 `dump`），OCR 对 AI 完全不可达。补一只只读 OCR 工具，让 AI 拿到页面**全部文本 + 精确坐标 + 归一化中心点**，即可与既有 `click_ratio` 直接闭环。

## What Changes

1. 新增只读平台工具 `ocr_page`（分类「视觉识别工具」，模块动作 `inspector/ocr`）：对指定在线设备识别**当前页面**，返回 JSON —— 每段文本的文本、置信度（浮点）、OCR 模型原始角点坐标（`[[x,y],...]` 数组格式）、归一化中心点（`[x,y]`，0~1）。
2. 算法层 `algorithms/vision/ocr.py` 的 `recognize()` 增补原始角点坐标输出；既有键（`text`/`confidence`/`x`/`y`/`width`/`height`/`bounds`/`thumbnail`）保持不变，向后兼容。
3. 设备检查器 `api.py` 新增白名单函数 `ocr_screen(serial)`，封装「截屏 → OCR → 归一化 → 清理截图」；AI 工具只调它，不直接触引擎或算法层。
4. AI 工具箱新增分类「视觉识别工具」并在其中展示该工具（`TOOL_CATEGORIES` + `TOOL_META`），工具箱按分类启停随之可用。

无 **BREAKING** 变更：新增工具与新分类，既有工具、检查器抓取链路、`di_snapshots` 表结构均不变。

## 关联文档

- PRD-03（设备检查器）
- PRD-08（AI 助手）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-screen-vision`: 新增「智能体可读取当前页面文本坐标」需求——AI 经只读 OCR 工具读取页面文本、置信度、OCR 原始角点坐标与归一化中心点；该工具与截屏工具共享同一设备可用性约束。

## Impact

- 后端：`apps/device_inspector/api.py`（新增 `ocr_screen` 并入 `__all__`）、`apps/device_inspector/service.py`（OCR 编排与截图清理）、`algorithms/vision/ocr.py`（补原始角点）、`apps/ai_assistant/tools.py`（`ocr_page` + `TOOLS` + `TOOL_META` + `TOOL_CATEGORIES`）
- 前端：**无改动**。AI 工具箱分类与工具由 `GET /api/ai/available-tools` 数据驱动（`ToolboxPanel.vue` 按 `cat.key`/`cat.icon` 渲染），服务端加分类即出现
- 数据：不新增表、不新增迁移（`ai_platform_tools` 无记录即默认启用）
- 测试：`python manage.py check`、`ruff check`、`pytest tests/graybox/unit`、`python tools/gen_arch_stats.py --check-boundaries`
