## Why

平台数据根 `data/` 已膨胀到 3.25 GB（其中 `uploads` 3.13 GB），挤占项目所在盘；同时数据根路径散落在 5 处定义里，其中 3 处是硬编码或依赖进程 CWD 的相对路径，无法整体换盘。本次把数据根迁到 `D:\Govee\data`，并把「数据根」收敛成唯一可配置项。

## What Changes

- 新增 `DATA_DIR` 环境变量（`.env`）：绝对路径直接使用，相对路径相对 `BASE_DIR` 解析，缺省 `BASE_DIR/data` → 未配置时行为与现状完全一致。
- `SCREENSHOT_DIR`、`MEDIA_ROOT` 改为由 `DATA_DIR` 派生，消除三处各自拼路径。
- 消除 ai_assistant 的 3 处硬编码 / CWD 相对路径：`kb_files.RAG_DATAS_DIR`、`upload_cleanup.UPLOAD_DIR`、`rag_service` 的 `data/rag_vector` 与默认 `data/rag_datas`，统一从 settings 取值。
- `.env` 写入 `DATA_DIR=D:\Govee\data`；`.env.example` 补该变量说明（留空即用缺省）。
- **物理搬运不由本次变更执行**：数据目录 3.25 GB，由用户停机后手动搬运；本次只保证平台引用路径正确。
- 无 **BREAKING**。

## 关联文档

- 纯配置 / 基础设施变更，无 PRD、无需求级 ARCH 变更。
- 相关（仅示意存储布局，不构成需求来源）：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（架构图 `data/chromadb` 标注）、`dev_docs/03-设计与架构/技术栈参考.md`（`data/chromadb/`）。
- 上述文档描述的是「数据根内部的相对布局」，数据根换盘后依然成立，本次不改动。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。数据根位置属部署配置，不改变任何 spec 级可观察行为（API 入出参、错误码、业务规则均不变），故在 `.openspec.yaml` 设 `skip_specs: true`。

## Impact

- `config/settings.py`：`DATA_DIR` / `SCREENSHOT_DIR` / `MEDIA_ROOT` 定义。
- `apps/ai_assistant/kb_files.py`、`apps/ai_assistant/upload_cleanup.py`、`apps/ai_assistant/rag_service.py`：路径来源改为 settings。
- `.env`（本地，已 gitignore）、`.env.example`（入库）。
- 不变：所有 HTTP/WS 契约、前端、DB、依赖；`data/` 内容与子目录结构不变（整体搬运）。
- 门禁：`manage.py check`、`ruff`、`pytest tests/graybox/unit/test_kb_files.py`。
