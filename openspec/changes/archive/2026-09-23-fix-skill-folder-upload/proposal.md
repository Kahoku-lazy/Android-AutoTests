## Why

AI 工具箱「自定义 Skill」的「+ Skill 文件夹」上传**自 2026-09-12 重构起 100% 失败**：后端把"上传文件名含相对路径"当作文件夹上传的判据，而 Django 的 `UploadedFile._set_name` 必然把文件名归一为 `os.path.basename`（实测 `probe-x/SKILL.md` → `SKILL.md`），判据永真命中，接口只回 400「只接受文件夹上传，请选择包含 SKILL.md 的文件夹」。服务器日志里两次真实点击（2026-09-16、2026-09-22）响应体均为 93 字节，逐字节等于该错误信封，**从未出现过 200**。前端又把服务端 `message` 吞掉换成了通用文案「上传失败」，现场无法自证；且子目录层级从未落盘（即使判据修好，现状也会把 `references/`、`scripts/` 拍平，破坏 skill-creator 这类多目录 Skill）。

## What Changes

- 上传请求新增 multipart 字段 `paths`（与 `files` 一一对应，值 = 浏览器 `webkitRelativePath`），作为**目录结构的唯一来源**；不再从上传文件名推断目录。
- 后端 `upload_skill` 改为按 `paths` 校验与落盘：同一顶层文件夹、无 `..`、非绝对路径、`paths` 与 `files` 数量一致；文件夹名以既有 `name` 字段为准并与其首段一致。
- 落盘 MUST 还原子目录层级（`engines/ai/skills/<文件夹名>/…`），使 Skill 目录树接口能读回真实结构。
- 上传成功后，该 Skill 的**介绍** MUST 取自 `SKILL.md` frontmatter 的 `description`：现在落库的是兜底摘要「N 个文件 — MD: N」，卡片因此没有介绍（本地 Skill 的介绍本就来自 frontmatter）。
- 前端上传失败时 MUST 展示服务端可读 `message`（改用项目统一的 `formatApiError`），MUST NOT 只给通用文案。
- **不**改权限模型（仍为已登录用户可上传）、**不**改响应信封、**不**改 Skill 目录树/文件读取端点契约、**不**改上传大小与后缀白名单策略。

## 关联文档

- PRD-需求总纲（AI 助手条目：工具箱 / 技能）
- PRD-08-AI助手（工具箱·技能增量；总纲登记的模块 PRD，仓库当前缺正文）
- 相关既有能力：无（工具箱上传此前没有 spec 覆盖）

## Capabilities

### New Capabilities

- `ai-shared-skill-upload`: 自定义 Skill 文件夹上传的端到端行为——以文件夹为单位落盘并保留子目录层级、入参校验与拒绝语义、上传失败原因对用户可见。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/views_toolbox_drf.py`（`upload_skill` 入参来源、校验与落盘，并把 SKILL.md frontmatter 的 `description` 作为 Skill 介绍落库；写库仍走既有 `api.create_shared_skill`）
- 前端：`frontend/src/modules/ai-assistant/api/toolbox.ts`（新增 `paths` 字段）、`composables/useToolbox.ts`（错误提示）
- 接口契约：`POST /api/ai/toolbox/upload-skill/` 新增请求字段 `paths`（**新增**，不破坏既有调用方的其它字段）
- 测试：新增后端 multipart 端到端与拒绝分支用例；新增前端 `useToolbox` 上传用例
- 文档：AI 助手接口文档 §6.6「上传共享 Skill」与真实契约对齐（现文档仍描述重构前的 `name is required` / `engines/ai/skills/{id}/`）
- 迁移 / 依赖：无

## 非目标

- 同类"吞掉服务端 message"的另外三处（平台工具、平台配置、知识库）不在本单范围。
- `python-frontmatter` 未在 `requirements.txt` 声明一事不在本单范围。
- 落盘中途失败可能留下无目录的 DB 行（既有 `missing` 标记已可见）不在本单范围。
