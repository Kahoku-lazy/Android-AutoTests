## Context

动机见 proposal.md - Why。方案需要知道的现状：

- 算法层 `algorithms/vision/ocr.py:recognize(screenshot_path)` 已存在，基于 cnocr；当前返回 `{text, confidence, x, y, width, height, bounds, thumbnail, thumbnail_format}`，其中 `bounds` 是**字符串** `"[x,y][r,b]"`，且**丢弃了 cnocr 的原始角点 `position`**（只在函数内部用于算包围盒）。
- 唯一调用方是 `apps/device_inspector/service.py:capture_ocr_payload`（检查器抓取的 OCR 分支）。该分支前端已下线（前端恒发 `dump`），后端入参与 `capture_ocr_payload` 仍在。
- 检查器已有一次性的只读截屏能力：`apps/device_inspector/api.py:capture_screen(serial)` —— 只校验设备、截图落盘、返回路径与屏幕尺寸，**不 dump、不 OCR、不落库**；`apps/ai_assistant/tools.py:screenshot_page` 正是调它。
- 设备可用性约束集中在 `service.py:open_inspector_engine`：未注册报错；被执行引擎前缀（`runner-`/`ai_agent`/`task-`/`run-`）占用时报 409 让路；**不取锁**。
- AI 工具注册表 `apps/ai_assistant/tools.py`：`TOOLS`（名 → (函数, is_read_only)）、`TOOL_META`（名 → (分类, module, action)）、`TOOL_CATEGORIES`（分类 → icon/color）。`GET /api/ai/available-tools`（`views_drf.py:665`）按 `TOOL_CATEGORIES` 顺序组装分类，只输出**有工具的分类**；前端 `ToolboxPanel.vue` 按 `cat.key`/`cat.icon` 数据驱动渲染，无硬编码分类。
- 点击工具的坐标口径是**归一化 0~1**：`click_ratio(serial, nx, ny)`、`drag_ratio`。
- **实测（真实截图 1080×2340 / 23 条文本）**：`CnOcr().ocr(path)` 返回 `list[dict]`，每条**只有 3 个键**——`text`(str)、`score`(Python float，未取整)、`position`(`numpy.ndarray` shape=(4,2) dtype=int32)。角点顺序稳定为**左上→右上→右下→左下**（顺时针），23/23 一致。`recognize()` 目前把 `position` 算完包围盒后**直接丢弃**。

## Goals / Non-Goals

**Goals:**

- AI 可一次性拿到当前页面**全部文本 + 精确坐标 + 归一化中心点**，并与 `click_ratio` 直接闭环。
- 复用既有截屏与设备可用性链路，不新造设备访问路径。
- 工具在 AI 工具箱中以「视觉识别工具」分类可查、可整类启停。

**Non-Goals:**

- 不改检查器抓取链路的 OCR 分支（`method=ocr` 入参、`capture_ocr_payload`、`di_snapshots.ocr_json/ocr_count`）—— 属另一变更。
- 不把 `screenshot_page` 迁入新分类（会改变既有工具归属）。
- 不给 OCR 结果落库、不生成快照记录、不产缩略图。
- 不引入置信度阈值或条数上限（按需求返回全部识别结果）。

## Decisions

### D1 返回契约（用户指定形状）

`ocr_page(serial)` 返回 JSON：

```json
{
  "serial": "H717D...",
  "screen_w": 1080,
  "screen_h": 2340,
  "count": 2,
  "texts": [
    {
      "text": "设置",
      "confidence": 0.9871,
      "coordinates": [[100, 210], [300, 210], [300, 268], [100, 268]],
      "center": [0.1852, 0.1021]
    }
  ]
}
```

- `coordinates` = 文本框的**左上与右下两个对角点** `[[x, y], [x2, y2]]`（设备像素）。只留对角两点而非模型给的四个角点：四点信息冗余（轴对齐框下两点即定框），返回体随之缩小，且 `center` 恰好是这两点的中点，两者自洽。取 `[[min_x, min_y], [max_x, max_y]]`（轴对齐包围盒的对角），不依赖 cnocr 的角点顺序。
- `center` = 归一化中心点 `[nx, ny]`，取值 0~1，保留 4 位小数（1080 宽下 1e-4 ≈ 0.11px，足够点击）。分母取**截图自身的像素尺寸**（与 OCR 坐标同一像素空间），而非 `engine.device_info`：两者通常一致（实测截图 1080×2340 = 显示尺寸），但用截图尺寸能保证「坐标与中心点同源」，截图一旦被缩放也仍自洽。
- `confidence` 浮点，沿用 cnocr `score`（4 位小数）。
- 带 `serial`/`screen_w`/`screen_h`：像素坐标与归一化中心的解释都依赖屏幕尺寸，缺它 AI 无法自校验。
- 不含缩略图/base64：需求只要文本与坐标，去掉图片可显著压缩返回体。

**为什么 center 用包围盒中心而非多边形质心**：既有 `bounds` 就是由 min/max 角点算的轴对齐盒；沿用同一基准可让 `coordinates` 与 `center` 自洽，AI 用两者交叉校验时不会出现「中心不在角点范围内」的错觉。cnocr 返回的文本四边形近轴对齐，两者差异可忽略。

### D2 角点从算法层透出：`recognize()` 增键，不新建函数

在 `recognize()` 的每条结果上**新增** `coordinates` 键（原始角点数组），既有键全部保留。

- 备选 A：新建 `recognize_regions()` 复制一份 cnocr 循环 —— 两份实现要同步维护，违反「不要重复造轮子」。
- 备选 B：把 `bounds` 从字符串改成数组 —— **BREAKING**，且检查器既有快照/前端按字符串消费，拒绝。
- 选增键：唯一既有调用方 `capture_ocr_payload` 只读 `text/x/y/width/height` 并 pop 缩略图，忽略未知键即天然兼容。
- 实现要点：`position` 是 `numpy.ndarray(int32)`，**必须 `.tolist()`** 转成 Python `list[int]` 才能 JSON 序列化（标准库 `json` 不认 numpy 标量）。实测 `.tolist()` 后全为 int，可直接序列化。

### D3 编排归属：`device_inspector.api.ocr_screen(serial)`

新增白名单函数 `ocr_screen(serial)`，职责：`open_inspector_engine` 校验设备 → `capture_page_screenshot` 截图 → `algorithms.vision.ocr.recognize` → 映射为 D1 契约（含归一化） → 删除截图文件 → 返回。

- AI 工具 `ocr_page` 只调 `apps.device_inspector.api.ocr_screen`，与既有 `screenshot_page` 调 `capture_screen` 同一模式（跨 App 只经对方 `api.py`）。
- 备选：让 `apps/ai_assistant/tools.py` 直接 import `algorithms.vision.ocr` —— 把引擎/算法访问散到上层，违反边界纪律，拒绝。

### D4 截图文件用完即删

`capture_page_screenshot` 会把 PNG 落在 `MEDIA_ROOT/inspector/shots/`。OCR 工具契约只回 JSON、不回图片，因此识别完成后删除该文件。

- 备选 A：照 `capture_screen` 保留文件 —— AI 可能每步都调 OCR，磁盘无界增长，拒绝。
- 备选 B：新增「截图到内存」路径 —— 需要动引擎接口，成本大于收益，拒绝。
- 删除失败只记日志不抛出（`service.py` 既有清理函数就是「尽力清理」语义），不影响工具结果。

### D5 注册与分类

- `TOOL_CATEGORIES` 追加 `{"key": "视觉识别工具", "icon": "🔍", "color": <取既有色板未用色>}`。
- `TOOLS["ocr_page"] = (ocr_page, True)` —— **只读**。
- `TOOL_META["ocr_page"] = ("视觉识别工具", "inspector", "ocr")`：module 取 `inspector`（代码归属设备检查器），action 取 `ocr`，供 HTTP 工具网关 `resolve_by_module_action` 解析，且与既有 `("inspector","screenshot")` 不冲突。
- **不进 `AUTO_ALLOW_TOOLS`**：那是一组「设备控制类」放行名单（acquire/release/click/swipe…），OCR 无设备副作用，走只读常规路径即可。
- 不写 `ai_platform_tools` 记录：无记录即默认启用（`AIPlatformTool` 语义），因此**无需迁移**。

### D6 不落库

OCR 工具不产生任何 `di_snapshots` 记录。快照是检查器页面的资产（有所有权、可回看、可删），AI 的工具调用是即时读取，两者不应混同。

### D7 文本过滤入参用「分隔符字符串」而非数组

`ocr_page(serial, texts="")`：一个可选入参，可一次指定多个文本，命中任一即返回；为空则返回全部（向后兼容）。

- 匹配语义：**忽略大小写的子串匹配**（`casefold()` 包含）。OCR 常把邻近文本合并或截断，精确等值会频繁漏命中；子串是 AI「找这个字样在哪」的实际意图。
- 分隔符：英文/中文逗号、顿号、换行都接受，内部统一拆成关键词表并去重。
- **为什么不声明成 `list[str]`**：平台自有调试表单的类型推导（`tools.py:_annotation_type_name`）只认 `str/int/float/bool`，其余一律回落成 `str`；`_coerce_param` 对未知类型会 `str(value)`，把数组变成 `"['设置']"` 这种字符串，调试面直接不可用。改这两个助手等于顺带动共享调试链路，超出本次范围。分隔符字符串在三处（LLM 调用、调试表单、内部网关）都直白可用，代价只是文档里写清分隔符。
- 备选：新增 `texts_`+`text` 双入参 —— 语义重复且更难解释，拒绝。

## 模块防火墙自检

- 新增跨 App 依赖仅一处：`apps/ai_assistant` → `apps/device_inspector/api.py` 的 `ocr_screen`（白名单导出）。符合「跨 App 读 Model / 写走 api.py；上层只调 api.py」。
- 无反向依赖：`apps/device_inspector` 不 import `apps.ai_assistant`。
- `apps/device_inspector/api.py` → `service.py` → `algorithms.vision.ocr`：App 内部调用 + L1a 算法层，与既有 `capture_ocr_payload` 同一路径，非新增模式。`algorithms/` 不反向 import `apps/`。
- 无跨 App import `service`/`runner`/`consumer`/`state_machine`。
- 无新增写库：本变更的 INSERT/UPDATE/DELETE 为零，不触碰 `di_snapshots`；不需要「写库收敛」例外。
- 前端无直连数据库；工具箱数据仍走 `GET /api/ai/available-tools`，本次前端零改动。

## Risks / Trade-offs

- [cnocr 首次调用需下载模型到 `~/.cnocr`，首次 OCR 慢且离线环境会失败] → 失败由工具层翻译为明确错误返回，不静默；部署时预热（先跑一次 OCR）记入验收步骤。
- [页面文本很多时返回体偏大，挤占模型上下文] → **实测已量化**：1080×2340 页面 23 条文本，本契约整包 JSON 约 **3.2 KB / 每条 138 字符**，量级安全。关键是**不带缩略图**——既有 `recognize()` 每条都附一个 base64 缩略图，照搬会让返回体膨胀两三个数量级。仍按需求返回全部，如需上限见 Open Questions。
- [低置信度噪声文本一并返回，AI 可能误点] → **实测噪声确实存在**：同一页面 confidence 分布 **0.1957~0.9996**，23 条中 2 条 < 0.5（如状态栏图标被误读成 `.al`）。置信度随条目返回，由 AI 自行判据；本变更不替 AI 设阈值。
- [删除截图失败导致磁盘残留] → 仅告警不抛出，影响面限于磁盘，正则化清理由既有 `inspector/shots` 生命周期承担。
- [与执行引擎抢设备] → 复用 `open_inspector_engine` 的让路规则，占用即报错，不做抢占。
- [新增分类漏配 icon/color 导致工具箱显示降级] → `views_drf.py` 只输出 `TOOL_CATEGORIES` 中存在的分类，漏配会让工具**不显示**；tasks 中列为显式验收项（调 `available-tools` 确认分类出现）。

## 迁移 / 回滚

- 无数据迁移、无 schema 变更、无前端构建依赖。
- 部署即生效；回滚 = 撤销注册（从 `TOOLS`/`TOOL_META`/`TOOL_CATEGORIES` 移除并回滚 `recognize()` 增键），无残留数据需要清理（本工具不落库）。

## Open Questions

- 是否把既有 `screenshot_page` 一并归入「视觉识别工具」分类？会改变既有工具在工具箱中的归属，属独立变更，本次不动。
- 是否需要置信度阈值或返回条数上限？当前按需求返回全部，若上下文压力实际出现，可后续加可选参数。
