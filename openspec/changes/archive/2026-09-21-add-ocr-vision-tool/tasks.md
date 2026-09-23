## 1. 算法层：透出文本框坐标

- [x] 1.1 `algorithms/vision/ocr.py:recognize()` 在每条结果上新增坐标键（最终形态见第 6 组：左上/右下两个对角点），既有键（`text`/`confidence`/`x`/`y`/`width`/`height`/`bounds`/`thumbnail`/`thumbnail_format`）**一个都不改**。验证：真实截屏跑一次，确认新键为数组格式且既有键齐全；`pytest tests/graybox/unit -q` 全绿
- [x] 1.2 确认既有唯一调用方 `apps/device_inspector/service.py:capture_ocr_payload` 未受影响（它只读 `text`/`x`/`y`/`width`/`height` 并 pop 缩略图，未知键应被忽略）。验证：读源码确认无键名依赖变更；`python manage.py check` 通过

## 2. 设备检查器：新增只读编排 `ocr_screen`

- [x] 2.1 在 `apps/device_inspector/api.py` 新增 `ocr_screen(serial)` 并加入 `__all__`：按 `open_inspector_engine` 校验设备 → 截屏 → 调算法层识别 → 映射为设计 D1 契约（`serial`/`screen_w`/`screen_h`/`count`/`texts[]`，每条含 `text`/`confidence`/`coordinates`/`center`，其中 `screen_w`/`screen_h` 取**截图自身像素尺寸**而非 `device_info`）→ 返回。验证：`python manage.py check && ruff check apps/device_inspector`
- [x] 2.2 `center` = 包围盒中心 ÷ **截图像素尺寸**，保留 4 位小数，取值 0~1；整除边界（screen 为 0）时不得抛 ZeroDivisionError，应给出明确错误。验证：灰盒单测对 `screen_w=0` 断言报错而非 500
- [x] 2.3 复用让路规则：设备未注册、被执行引擎前缀占用两条路径返回可读错误，不执行识别。验证：`pytest tests/graybox/unit -q -k inspector` 覆盖两条错误分支
- [x] 2.4 识别完成后删除本次截图文件（`MEDIA_ROOT/inspector/shots/`），删除失败仅告警不抛出。验证：真实设备调用后确认 `shots/` 下无本次 `capture_<ts>.png` 残留；工具结果仍正常返回

## 3. AI 工具注册与工具箱分类

- [x] 3.1 在 `apps/ai_assistant/tools.py` 新增工具函数 `ocr_page`：只调 `apps.device_inspector.api.ocr_screen`，把结果以 JSON 字符串返回（与既有工具返回风格一致）。验证：`ruff check apps/ai_assistant/tools.py`；`python manage.py check`
- [x] 3.2 `TOOLS["ocr_page"] = (ocr_page, True)`（只读）且 **不加入** `AUTO_ALLOW_TOOLS`；`TOOL_META["ocr_page"] = ("视觉识别工具", "inspector", "ocr")`。验证：`resolve_by_module_action("inspector", "ocr")` 返回该函数；`list_tool_schemas()` 中该项 `read_only` 为 true
- [x] 3.3 `TOOL_CATEGORIES` 追加 `{"key": "视觉识别工具", "icon": "🔍", "color": "#A78BFA"}`（`#A78BFA` = 令牌 `--color-indigo-76`，与既有分类色 `#6BCB77`/`#FFB5A7`/`#38BDF8` 均不重复）。验证：`GET /api/ai/available-tools` 返回含 `视觉识别工具` 的分类且其 `tools` 含 `ocr_page`

## 4. 前端零改动确认

- [x] 4.1 确认工具箱渲染无需改动：`ToolboxPanel.vue` 按 `cat.key`/`cat.icon` 数据驱动渲染分类。验证：本变更文件清单不含任何 `frontend/` 路径（`git diff --stat frontend/` 在本仓为**非空**——工作区存在与本次变更无关的既存前端改动，故以变更文件清单为准）
- [ ] 4.2 人工验收：打开 AI 助手工具箱「装配台」，新分类「视觉识别工具」下出现该工具、标记只读；整类停用后工具对智能体不可用，重新启用后恢复。验证：页面实际操作观察（接口层已由 `test_available_tools_endpoint_exposes_vision_category` 与 `test_toggle_vision_category_disables_then_restores_ocr_page` 覆盖，剩下的是浏览器肉眼确认）

## 5. 按文本过滤（`texts` 多文本入参）

- [x] 5.1 `apps/device_inspector/service.py:ocr_page_payload(screenshot_path, texts="")` 增加关键词过滤：入参按英文/中文逗号、顿号、换行拆成关键词表（去空、忽略大小写去重），条目文本命中**任一**关键词即保留；`texts` 为空时返回全部。验证：灰盒单测覆盖「单关键词 / 多关键词 OR / 忽略大小写 / 无命中 / 不传返回全部」五种情形；真机 `R5CT62RH88F` 复核：全量 24 条 → 按「设备」过滤 8 条（全部命中且为全量子集）→ 无命中查询返回 0 条
- [x] 5.2 `apps/device_inspector/api.py:ocr_screen(serial, texts="")` 透传该入参；`apps/ai_assistant/tools.py:ocr_page(serial, texts="", user_id="")` 暴露给智能体，docstring 写明分隔符与匹配语义（供 schema 推导）。验证：`get_tool_debug_schema("ocr_page")` 含 `texts` 参数且 `type` 为 `str`、非必填；`ruff check` 通过

## 6. 坐标精简为对角两点

- [x] 6.1 `algorithms/vision/ocr.py:recognize()` 的 `coordinates` 由四个角点改为**左上/右下两个对角点** `[[x,y],[x+width,y+height]]`（轴对齐包围盒的对角，不依赖模型角点顺序）；`center` 语义不变，仍是这两点的中点。验证：真机跑一次确认每个条目恰好两个点且 `center == 两点中点`；灰盒单测断言两点形状与数值
- [x] 6.2 同步规格与设计措辞（「4 个原始角点」→「左上/右下两个对角点」）。验证：`openspec validate --strict` 通过

## 7. 门禁、端到端与文档同步

- [x] 7.1 架构边界零违规：`python tools/gen_arch_stats.py --check-boundaries`（新增跨 App 调用只有 `ai_assistant` → `device_inspector/api.py`）。验证：命令 0 违规
- [x] 7.2 后端门禁：`python manage.py check`、`ruff check apps/ algorithms/`、`pytest tests/graybox/unit -q`。验证：全部通过
- [ ] 7.3 真实设备端到端：让智能体对在线设备调用 OCR 工具读当前页面 → 取某条文本的 `center` → 调 `click_ratio` 点击 → 确认命中。验证：人工 E2E 观察页面变化（OCR 侧已在真机 `R5CT62RH88F` 验完：契约键正确、坐标两点、中心点即两点中点、截图无残留；智能体侧的点击动作需平台在跑，且会真实改动设备屏幕，留人工执行）
- [x] 7.4 接口文档同步：更新 AI 助手接口文档中 `available-tools` 的工具分类清单（新增「视觉识别工具」）。验证：文档两处分类示例已同步；`--check-md` 对接口文档不适用（该文档无 `ARCH_STATS` 区域，命令返回「需要初始化」且 exit 0），实际一致性由 `available-tools` 接口测试对拍
