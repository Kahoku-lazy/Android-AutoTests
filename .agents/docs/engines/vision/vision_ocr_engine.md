# vision · OCR 视觉引擎
> 归属模块：`engines/vision` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/vision/ocr.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../../../engines/AGENTS.md) → **本文件**。本文件只写 OCR 视觉领域增量；**冲突时本文件的领域规则优先**。

## 职责

页面文本识别（OCR）。**底座能力**：原调用方 `engines/agents/tools/tool_ocr.py` 随该包退役，当前无生产调用方；重依赖（cnocr）在本模块导入时加载，调用方须在函数内导入本模块，避免引擎启动即拉起重依赖。

| 路径 | 职责 |
| --- | --- |
| `ocr.py` | `recognize(screenshot_path)`：整图 OCR，返回文本区域与设备像素坐标（与 dump 元素口径一致） |
| `__init__.py` | 包导出 |

## 红线（禁止）

1. **禁止**在引擎启动路径顶层无条件 `import engines.vision.ocr`（或本包）导致强制加载 cnocr；工具侧保持函数内导入。
2. **零 Django**：禁止 `import apps.*` / `django.*` / `backend.apps.*`。
3. **调用面**：上层如需页面文字，经工具层（`ae_harness` 的 `tools/<域>/`）接入；不要在 View 里直接跑 OCR。
4. **坐标口径**：`bounds` 与 dump 元素同格式；改坐标语义必须同步工具与验收逻辑。
5. **引擎单例**：CnOcr 懒加载缓存；不要每次 recognize 新建引擎（除非刻意重置并写明）。

## AI 阅读与检查流程（必读）

1. 先读 [`engines/AGENTS.md`](../../../../engines/AGENTS.md)。
2. 改 OCR 输出契约或加载策略时再读**本文件**。
3. 写代码前读 style rules；自检：`--path engines/vision`。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层入口 | [`engines/AGENTS.md`](../../../../engines/AGENTS.md) |
| 工具层接入点 | `engines/ae_harness/tools/<域>/` |
| 风格检查 | [`.agents/skills/engines-agents-style-check/`](../../../../.agents/skills/engines-agents-style-check/) |
