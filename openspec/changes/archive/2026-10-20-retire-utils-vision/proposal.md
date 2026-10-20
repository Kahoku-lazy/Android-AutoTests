## Why

`utils/vision` 本应在 `move-ocr-into-engine` 中删除，却在 `e14cf891`（retire 提交）被 `git add -A` 夹带改名重新入库，随后又被一次跨目录批量文件还原写回工作区，最终与 `engines/vision` 形成两份并存的 OCR 实现。旧包无任何代码引用，但会漂移、且一旦被误 import 会拉起 cnocr 重依赖，违反「页面文本识别只经引擎工具」的单一实现约束。

## What Changes

- 删除 `utils/vision/`（`__init__.py`、`ocr.py`），只保留 `engines/vision/` 作为 OCR 唯一实现。
- 在测试中补「Git 层 + 源码层」双重守卫：`utils/vision` 不得被版本库跟踪、不得出现在磁盘；Python 源码中不得出现该路径的导入。
- 补记 `retire-inspector-and-element-locator` 与 `move-ocr-into-engine` 的归档说明：记录 `algorithms → utils` 未申报改名、`utils/vision` 复活路径与 git 层复核结论。
- 记录 `2026-10-20 18:13:34` 批量文件还原的证据与结论，明确「删除类验收必须复核 git 索引」的流程要求。
- 非破坏性：无 API、表结构、前端交互变更。

## 关联文档

无独立 PRD 编号；本次为 `move-ocr-into-engine` 与 `retire-inspector-and-element-locator` 的收尾清理，关联能力 `ai-screen-vision`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-screen-vision`: 新增「页面文本识别实现唯一」要求——旧实现包不得存在、不得被版本库跟踪，且源码不得引用第二份实现。

## Impact

- 代码：删除 `utils/vision/__init__.py`、`utils/vision/ocr.py`（当前零引用）。
- 测试：`tests/engines/agents/test_ocr_tool.py` 增加 git 层与源码层守卫。
- 文档：`openspec/changes/archive/2026-10-20-retire-inspector-and-element-locator/`、`openspec/changes/archive/2026-10-20-move-ocr-into-engine/` 各补一节「事后订正」。
- 不涉及 `apps/`、`engines/` 运行时代码，不涉及迁移与依赖。
