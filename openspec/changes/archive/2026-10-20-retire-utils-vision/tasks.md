## 1. 删除旧识别包

- [x] 1.1 删除 `utils/vision/` 两个文件（`__init__.py`、`ocr.py`），保留 `utils/` 其余文件；验证：`git ls-files utils/vision` 为空、`Test-Path utils/vision` 为 False、`git grep -n "utils\.vision" -- "*.py"` 零命中
- [x] 1.2 确认 `engines/vision/ocr.py` 与 `engines/agents/tools/tool_ocr.py` 未被改动；验证：`git status --porcelain -- engines/vision engines/agents/tools/tool_ocr.py` 为空

## 2. 补 Git 层与源码层守卫

- [x] 2.1 在 `tests/engines/agents/test_ocr_tool.py` 增加 Git 层断言：`git ls-files --error-unmatch utils/vision` 非零退出、`utils/vision` 目录不存在；验证：`pytest tests/engines/agents/test_ocr_tool.py -q` 通过
- [x] 2.2 在同文件增加源码层断言：任何 `.py` 中不得出现 `utils.vision` 或 `utils import vision`；用 `tmp_path` 构造违规导入验证守卫确实会失败（`test_retired_vision_guard_catches_reintroduction`）；验证：同一 pytest 通过
- [x] 2.3 守卫对无 git 环境降级：`git` 不可用时跳过 Git 层断言、仍执行源码层；验证：`pytest tests/engines/agents/test_ocr_tool.py -q` 通过

## 3. 归档订正

- [x] 3.1 在 `openspec/changes/archive/2026-10-20-retire-inspector-and-element-locator/tasks.md` 末尾追加「事后订正」小节，写明 `algorithms → utils` 未申报改名被 `git add -A` 夹带、`utils/vision` 由此重新入库；验证：该文件含「事后订正」且提到 `e14cf891`
- [x] 3.2 在 `openspec/changes/archive/2026-10-20-move-ocr-into-engine/tasks.md` 末尾追加「事后订正」小节，写明删除只在工作区生效、18:13:34 批量还原把包写回、验收须复核 `git ls-files`；验证：该文件含「事后订正」且提到 `18:13:34`

## 4. 验收

- [x] 4.1 跑目标测试与静态检查；验证：`pytest tests/engines/agents/test_ocr_tool.py -q` 通过（9 passed）、`ruff check tests/engines/agents/test_ocr_tool.py` 通过
- [x] 4.2 跑架构边界检查；验证：`python tools/gen_arch_stats.py --check-boundaries` 通过（零违规，不跑全量回归）
- [x] 4.3 归档本 change；验证：`openspec validate retire-utils-vision --strict` 通过后执行 `/opsx:archive`（已归档为 `2026-10-20-retire-utils-vision`，`openspec validate --all` 92 passed / 0 failed）
