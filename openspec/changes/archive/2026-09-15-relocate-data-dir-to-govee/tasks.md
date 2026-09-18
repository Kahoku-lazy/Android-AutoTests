## 1. 配置层：数据根可配置

- [x] 1.1 `config/settings.py` 增加 `DATA_DIR` 环境变量解析（空 → 缺省 `BASE_DIR/data`；绝对路径直用；相对路径相对 `BASE_DIR`），并让 `SCREENSHOT_DIR`、`MEDIA_ROOT` 由 `DATA_DIR` 派生；验证：`$env:DATA_DIR="<工作区临时路径>"; python manage.py check` 通过且无告警新增
- [x] 1.2 `.env` 写入 `DATA_DIR=D:\Govee\data`，`.env.example` 补注释说明（留空 = 缺省）；验证：`python -c` 打印 `settings.DATA_DIR` 输出预期路径

## 2. ai_assistant 引用收敛

- [x] 2.1 `apps/ai_assistant/kb_files.py`：`RAG_DATAS_DIR` 改为 `settings.DATA_DIR / "rag_datas"`；验证：`pytest tests/graybox/unit/test_kb_files.py` 通过
- [x] 2.2 `apps/ai_assistant/upload_cleanup.py`：`UPLOAD_DIR` 改为 `settings.MEDIA_ROOT`；验证：断言 `UPLOAD_DIR == settings.DATA_DIR / "uploads"`
- [x] 2.3 `apps/ai_assistant/rag_service.py`：`_VECTOR_DIR` 与 `data/rag_datas` 默认值改为从 `settings.DATA_DIR` 派生的绝对路径；验证：导入后打印两值均落在 `DATA_DIR` 下

## 3. 校验与关单

- [x] 3.1 静态检查：`$env:DATA_DIR="<临时>"; python manage.py check` 与 `ruff check` 四个改动文件通过
- [x] 3.2 残留校验：仓库 `.py` 内不再出现 `BASE_DIR / "data"` 与 `"data/` 相对字面量（文档除外）
- [x] 3.3 单测：`$env:DATA_DIR="<临时>"; pytest tests/graybox/unit/test_kb_files.py -m unit` 通过

## 4. 验证记录

- `$env:DATA_DIR="D:\Github\Android-AutoTests\temps\data-dir-check"; python manage.py check` → `System check identified no issues (0 silenced).`（exit 0）
- 配置解析（读 `.env`）：`DATA_DIR = D:\Govee\data`、`MEDIA_ROOT = D:\Govee\data\uploads`、`SCREENSHOT_DIR = D:\Govee\data\screenshots`
- 相对值规则：`DATA_DIR=temps/rel-check` → `D:\Github\Android-AutoTests\temps\rel-check`
- ai_assistant 常量：`RAG_DATAS_DIR` / `UPLOAD_DIR` / `_VECTOR_DIR` / `_RAG_DATAS_DIR` 与 `index_rag_directory.__defaults__` 均落在 `DATA_DIR` 下
- `python -m ruff check` → `All checks passed!`；`python -m ruff format --check` → `4 files already formatted`
- `python -m pytest tests/graybox/unit/test_kb_files.py -m unit -q` → `6 passed in 0.24s`
  - 环境说明：workspace-write 文件沙箱下 pytest 的 `tmp_path` 因 `WinError 5` 无法建临时目录（已用最小控制用例独立复现，与本变更无关）；该单测在无文件沙箱下执行通过。
- 残留校验：`*.py` 中仅剩 `config/settings.py:323` 的缺省分支 `BASE_DIR / "data"`（预期保留）；`*.{yml,yaml,json,conf,sh,ps1,toml,cfg,ini}` 中 0 处 `data/(uploads|screenshots|rag_datas|rag_vector|chromadb)`。
