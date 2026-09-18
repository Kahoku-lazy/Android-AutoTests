## Context

element_locator 的 DRF 写路径有两处问题：一处越权写（`serializer.save()`），一处因 Serializer 的 FK 字段全只读而**必现 500**。本单同时修契约与收敛写路径。

## Goals / Non-Goals

**Goals:**

- `POST /api/elements/web-flows/` 按文档契约工作（不再是 500）
- 两处 DRF 写路径都经 `api.py`；视图不再直接写库

**Non-Goals:**

- 不动 legacy 平铺路径（它们本就直调 api）
- 不动 `views_projects_drf.py` 的 ViewSet（另单）

## Decisions

### 1. 让 FK 用 `IntegerField` 可写，而不是 `PrimaryKeyRelatedField`

- **选择**：`from_group_id` / `to_group_id` → `IntegerField`；`trigger_element_id` → `IntegerField(allow_null=True, required=False)`
- **理由**：与 `fix-workflow-directory-update-atomicity` 的 `parent_id` 同一裁决 —— 文档写的是裸 id，**存在性与业务校验归 api.py**；
  用 `PrimaryKeyRelatedField` 会把校验前移到 DRF 并产生技术化文案，且 `validated_data` 拿到的是对象而非 id

### 2. 校验（源/目标不能是目录）留在视图、写留在 api

- **选择**：`perform_create` 里取 `WebGroup` 实例做目录判定，再调 `api.create_web_page_flow(...)`
- **理由**：这是**入参校验**（apps/AGENTS.md：serializer/view 管校验），写归 api；且该判定需要 `is_folder`，属读操作

### 3. `create_web_page_flow` 返回 dict

- **选择**：返回 `{"id": flow.id}`
- **理由**：§6 规则 4 禁止 api 返回 ORM；`perform_create` 需要 id 但**不能**依赖 ORM 返回值。调用方 `web_flows_handler` 忽略返回值，故零适配

## Risks / Trade-offs

- [字段可写后的入参风险] → `from_group_id` 指向不存在的组时由 `api.create_web_page_flow` 的 FK 约束抛 IntegrityError → 500；已用「先取实例再判目录」覆盖常见非法输入，极端情况（不存在的 id）留给 DB 约束（与既有 legacy 路径同口径）
- [行为变化] → web-flows create 由 500 → 正常/400；这是修 bug，已在 proposal 标注
- [死局部变量删除] → 它们引用的 `alias`/`notes` 字段不存在，删除无行为影响

## Migration Plan

1. 改 `WebPageFlowSerializer` 三字段；重写两处 `perform_*`；`create_web_page_flow` 返回 dict
2. 新增 HTTP 级测试（成功 / 目录 400 / spy 断言）
3. 验证 `manage.py check` · `makemigrations --check` · ruff · 全量单测/集成 · `--check-boundaries`
4. 归档；回滚 = `git checkout` 三文件 + 删测试
