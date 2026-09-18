## Context

动机见 proposal.md - Why。方案所需事实（已核对）：

- 现状 5 处路径定义：`config/settings.py:320-321`（`DATA_DIR`/`SCREENSHOT_DIR`）、`config/settings.py:340`（`MEDIA_ROOT` 独立拼接）、`apps/ai_assistant/kb_files.py:14`、`apps/ai_assistant/upload_cleanup.py:14`、`apps/ai_assistant/rag_service.py:34`（相对路径 `data/rag_vector`，另有 279/350 的默认值 `data/rag_datas`）。
- 相对路径以进程 CWD 为基准，只有从仓库根启动 `python run.py` 时才恰好正确。
- `config/env.py` 在 `config/settings.py` 第 23 行加载 `.env`，且**已存在的真实环境变量优先**。
- `config/test_settings.py` 用 `from config.settings import *` 继承，因此测试同样受 `DATA_DIR` 影响。
- `data/` 整个被 `.gitignore` 忽略，与 Git 无关。
- 目标目录 `D:\Govee\data` 已存在且为空。

## Goals / Non-Goals

**Goals:**

- 数据根可通过 `.env` 切换，缺省值保持向后兼容。
- 平台内所有数据落点都从单一 `DATA_DIR` 派生，消除硬编码与 CWD 依赖。

**Non-Goals:**

- 不执行 3.25 GB 物理搬运（用户手动，见 proposal）。
- 不改数据根内部的子目录结构与命名。
- 不改任何 API / 前端 / DB / 依赖。
- 不做运行时热重载（重启生效）。

## Decisions

**D1 环境变量名用 `DATA_DIR`。** 与现有 `settings.DATA_DIR` 同名、语义一致，避免引入第二个同义概念。备选 `PLATFORM_DATA_DIR` 否决：收益为零。

**D2 相对值相对 `BASE_DIR` 解析。** 规则：值为空 → 用缺省 `BASE_DIR/data`；值为绝对路径 → 直接使用；否则 `BASE_DIR / 值`。备选「原样交给 `Path()`」否决：相对值会随 CWD 漂移，与本次要消除的问题同源。

**D3 `SCREENSHOT_DIR` / `MEDIA_ROOT` 从 `DATA_DIR` 派生。** `MEDIA_ROOT = DATA_DIR / "uploads"`，与现状字符串等价，但只有一处真相源。备选「三处各自读 env」否决：重复解析、易漏。

**D4 `kb_files.RAG_DATAS_DIR` → `settings.DATA_DIR / "rag_datas"`；`upload_cleanup.UPLOAD_DIR` → `settings.MEDIA_ROOT`。** `UPLOAD_DIR` 语义上就是 `data/uploads`，直接引用 `MEDIA_ROOT` 可让二者永不脱节。两者均为模块级常量，现有测试用 `monkeypatch.setattr(kb_files, "RAG_DATAS_DIR", root)`，不受影响。

**D5 `rag_service` 的 `data/rag_vector` 与默认 `data/rag_datas` 改为模块级绝对路径常量。** 新增 `from django.conf import settings`，模块级计算 `_VECTOR_DIR`、`_RAG_DATAS_DIR` 为 `str(...)`（`chromadb.PersistentClient(path=...)` 与 `Path(dir_path).rglob` 都接受 str）。`rag_service` 仅在 Django 配置完成后被 `apps/ai_assistant/api.py` 调用，引入 settings 依赖安全。

**D6 `.env` 写 `DATA_DIR=D:\Govee\data`；`.env.example` 写空值 + 注释。** `.env` 已 gitignore，每台机器自配。

**D7 搬运不由本次执行。** 平台当前在运行，chromadb / sqlite / 上传文件有打开句柄，运行中搬运会损坏向量库。用户停机后搬运，本次交付「引用路径已就绪」。

## 模块防火墙自检

- 跨 App import：无新增。改动仅限 `config/` 与 `apps/ai_assistant/` 内部。
- ORM 写：无，不涉及任何表。
- api.py 契约：无签名 / 返回值变化。
- 前端直连：无。
- 唯一新增依赖方向是 `apps/ai_assistant/rag_service.py` → `django.conf.settings`（同 App 内取配置），未跨越模块边界。

## Risks / Trade-offs

- [`.env` 指向尚未搬运的空目录，平台读到空数据] → 搬运与重启由用户按顺序执行；本次的设备无关校验统一用 `DATA_DIR` 环境变量覆盖到工作区临时目录，不写 `D:\Govee\data`。
- [硬编码残留导致部分数据写回项目内] → 交付前 grep 校验仓库 `.py` 不再出现 `BASE_DIR / "data"` 与 `"data/` 相对字面量。
- [测试受 `.env` 影响，在 `D:\Govee\data` 建目录] → 测试命令统一用 `DATA_DIR` 环境变量覆盖到 `temps/`。
- [Docker / 其他机器路径不同] → `.env` 不入库；缺省回退项目内 `data/`，行为与现状一致。
- [相对路径 CWD 漂移] → D4/D5 已消除，不再依赖启动目录。

## Migration Plan

1. 用户 `python run.py stop` 停机。
2. 用户把 `D:\Github\Android-AutoTests\data\*` 整体搬到 `D:\Govee\data\`（保留子目录结构）。
3. 平台侧引用已由本次变更就绪（`.env` → `DATA_DIR=D:\Govee\data`）。
4. 用户 `python run.py start`，验证知识库文档列表、设备检查器截图、上传文件链路。
5. 回滚：清空 `.env` 的 `DATA_DIR`（回退项目内 `data/`），把目录搬回即可。
