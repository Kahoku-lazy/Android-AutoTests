## Context

动机见 `proposal.md` - Why。上一变更的口径是「改指针到现址」，本变更的口径是「**不再保留对已删文档的任何提及**」——两者的差别正是这三处历史提及与页脚文案。

## Goals / Non-Goals

**Goals:**

- 全仓（含 gitignored 的 `plans/`）不再出现 `VUE_API_CONTRACT.md` / `DEVELOPMENT_CHECKLIST.md` / `android-autotests-rules` 的提及
- 删除已无入站引用的 `frontend/README.md`

**Non-Goals:**

- 不改 `openspec/changes/archive/**` 里对本轮清理过程的记录（那是变更档案，就该写清删了什么）
- 不重建 `frontend/README.md` 的内容到别处（`frontend/AGENTS.md` 已覆盖约束与结构；根 `README.md` 已有文档索引）

## Decisions

### 1. 删文件前先证明无入站引用

- **选择**：全仓检索 `frontend/README` 得到 0 命中后才删除
- **理由**：删文档最怕留下新的悬空指针；0 入站引用是删除的前提条件

### 2. `plans/*.md` 一并修（推翻上一变更的「有意保留」）

- **选择**：改这 2 处，不再以「gitignored / 私有计划」为由保留
- **理由**：用户明确要求清干净；这两处是具体依据与待办项，改掉不会破坏计划语义

### 3. 页脚文案直接删片段

- **选择**：`config/api_docs.py` 的页脚去掉 `· VUE_API_CONTRACT.md`
- **理由**：它只是印在 API 文档页脚的说明文字，删除不改变页面结构与行为；换成其它链接属于加需求，不做

## 模块防火墙自检

- 纯文档 + 1 行 HTML 文案：不涉及跨 App import、写库、引擎边界、通信通道

## Risks / Trade-offs

- [删掉 `frontend/README.md` 后有人找不到前端入口] → 根 `README.md` 已有文档索引，且 `frontend/AGENTS.md` 是前端约束真相源；删除记录在本变更里可追溯，必要时 `git checkout` 恢复
- [gitignored 计划文档被改] → 改动仅限「去掉已删引用」，计划语义不变

## Migration Plan

1. 删 `frontend/README.md`（先确认 0 入站引用）
2. 改 2 份 `plans/*.md` 与 `config/api_docs.py`
3. `python -m py_compile config/api_docs.py` + 全仓检索三个关键字
4. 归档；回滚 = `git checkout`（`plans/` 与已删 README 亦可从 git 恢复）
