# API-用例管理 — /api/cases/*

> 用例管理（`apps/case_manager`）：**项目 → 无限目录 → 文件（表格）→ 用例行**。  
> 真相源：`apps/case_manager/urls.py` + `api.py` + `views_drf.py`。  
> 日期：2026-09-09（文件/Excel 行模型；四类型可执行用例 / 编辑锁 / YAML / step-types 已移除）

## 通用约定

- 鉴权：`Authorization: Bearer <JWT>`
- 信封：成功 `{status: true, data}`；失败 `{status: false, message}`（由 `EnvelopeJSONRenderer` 包装；View 返回裸 data）
- JSON：snake_case
- 数据隔离：按 `created_by` / 项目所有者过滤

## 枚举

| 字段 | 取值 |
|------|------|
| test_type | `app` / `web` / `api` / `func` |
| business_type | `appliance`（家电）/ `lighting`（照明）/ `app`（APP） |

用例 ID：平台生成 `TC-YYYYMMDD-NNNN`。展示时间：`YYYY-MM-DD-HH:mm:ss`。

## 信息架构

```
项目 → 目录* → 文件(CaseFile) → 用例行(TestDefinition)
```

树接口只返回 `directory` / `file`；点文件进入表格页编辑多行用例。

## 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cases/projects/` | 当前用户项目列表 |
| POST | `/api/cases/projects/` | 创建项目 `{name, description?}` |
| GET | `/api/cases/projects/{id}/` | 项目详情 |
| PATCH | `/api/cases/projects/{id}/` | 更新名称/描述 |
| DELETE | `/api/cases/projects/{id}/` | 删除项目（级联） |
| GET | `/api/cases/projects/{id}/tree/` | 目录+文件树 |
| POST | `/api/cases/directories/` | `{project_id, name, parent_id?}` |
| PATCH | `/api/cases/directories/{id}/` | 改名/排序 |
| DELETE | `/api/cases/directories/{id}/` | 删目录（级联子树） |
| POST | `/api/cases/files/` | `{project_id, name, directory_id?}` 新建文件 |
| GET | `/api/cases/files/{id}/` | 文件 + 行：`{file, rows}` |
| PATCH | `/api/cases/files/{id}/` | 改名/排序 |
| DELETE | `/api/cases/files/{id}/` | 删文件（级联用例行） |
| POST | `/api/cases/definitions/` | 新建用例行（必填 `project_id` + `file_id`） |
| GET | `/api/cases/definitions/{id}/` | 用例详情 |
| PATCH | `/api/cases/definitions/{id}/` | 更新（保存时标题/步骤/预期必填） |
| DELETE | `/api/cases/definitions/{id}/` | 删除 |
| POST | `/api/cases/definitions/batch-delete/` | `{ids: [...]}` |
| POST | `/api/cases/move/` | `{item_type: directory\|file, item_id, target_directory_id?, sort_order?}` |

## 错误

| HTTP | 场景 |
|------|------|
| 400 | 校验失败（空标题/步骤/预期、非法枚举、缺 file_id） |
| 404 | 项目/目录/文件/用例不存在或无权 |
| 409 | 同名冲突；目录拖入自身子孙 |

## 已移除

`/cases/ui|web|api|storage` 四类型定义路径、`step-types`、YAML 导出、lock/visibility、`/ws/case-editing/`。
