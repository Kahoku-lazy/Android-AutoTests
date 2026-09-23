## 1. 后端上传入口改造

- [x] 1.1 `apps/ai_assistant/views_toolbox_drf.py::upload_skill` 改为从 `request.data.getlist("paths")` 读取每个文件的相对路径，删除 `if "/" not in first_rel` 守卫以及"由上传文件名推导文件夹名"的逻辑（框架必然把文件名归一为 basename，该判据恒真）。验证：`python manage.py check` 通过，且带 `paths` 的 multipart 请求不再返回「只接受文件夹上传」。
- [x] 1.2 按 design D2 落实全部校验，且全部发生在 `api.create_shared_skill` 与写盘之前：`files` 非空、`paths` 数量一致、每条路径非空/非绝对/不含 `..`、同属一个顶层目录、顶层目录名与 `name` 一致、根目录存在 `SKILL.md` 且 frontmatter 的 `name`/`description` 非空、后缀在白名单、总大小不超上限。验证：3.1 的每条拒绝分支用例均 400 且不产生记录与文件。
- [x] 1.3 落盘改用 `paths[i]` 去掉顶层文件夹前缀后的相对路径，使子目录层级得以还原。验证：3.1 断言 `<SHARED_SKILLS_DIR>/<文件夹名>/references/a.md` 存在。

## 2. 前端上传与提示

- [x] 2.1 `frontend/src/modules/ai-assistant/api/toolbox.ts::uploadSharedSkill` 在追加每个文件的同时把其 `webkitRelativePath`（缺失时回退 `file.name`）追加到 `paths` 字段，顺序与 `files` 严格一一对应。验证：3.2 断言请求体里 `files` 与 `paths` 等长且顺序对应。
- [x] 2.2 `frontend/src/modules/ai-assistant/composables/useToolbox.ts::onSkillFolderPicked` 的 `catch` 改为 `ElMessage.error(formatApiError(e, '上传失败'))`，把服务端 4xx 信封里的可读 `message` 透出。验证：3.2 的 400 用例断言提示包含服务端 message。
- [x] 2.3 同步公开签名与类型（不引入 `any`、不新增魔法字符串）。验证：`npm run typecheck` 通过。**偏差记录**：`vue-tsc --noEmit` 当前仍有 3 个既存报错，全在未触碰的 `src/modules/case-manager/components/ProjectTree.vue`；本次改动文件零报错。

## 3. 测试

- [x] 3.1 新增后端用例 `tests/graybox/unit/test_ai_shared_skill_upload.py`：用 DRF `APIClient` 发真实 multipart（含嵌套子目录），并把 `views_toolbox_drf.SHARED_SKILLS_DIR` monkeypatch 到 `tmp_path`（不写真实 Skill 目录、不落库残留）；覆盖成功（含子目录）、同名拒绝且不改动既有目录、缺 `SKILL.md`、frontmatter 缺字段、缺 `paths`、数量不一致、路径穿越、绝对路径、跨顶层目录、顶层名与 `name` 不一致、后缀不合法、超大小。验证：`pytest tests/graybox/unit/test_ai_shared_skill_upload.py` 全绿。
- [x] 3.2 新增前端用例 `frontend/tests/ai-assistant/p0/useToolbox.spec.ts`：覆盖 FormData 的 `files`/`paths` 配对、400 时服务端 message 透出、成功时给出成功反馈并刷新目录。验证：`npx vitest run tests/ai-assistant/p0/useToolbox.spec.ts` 通过。**偏差记录**：`tests/ai-assistant` 整目录曾在机器满载时出现 1 次跨文件失败（本用例断言到的是兜底文案）；已把 `@/shared/api-client` 的部分 mock（`importOriginal`）换成只取真实 `formatApiError` 的工厂 mock、并把 mock 拒绝改为持续生效，之后连续 6 次整目录运行 48/48 通过。

## 4. 文档与门禁

- [x] 4.1 把 AI 助手接口文档 §6.6「上传共享 Skill」同步到真实契约：新增 `paths` 字段、文件夹语义与子目录保留、frontmatter/后缀白名单/50MB 限制、错误码与文案表、落盘位置 `engines/ai/skills/<文件夹名>/`（现文档仍描述重构前的 `name is required` 与 `engines/ai/skills/{id}/`）。验证：文档逐条与 `upload_skill` 代码对照一致。
- [x] 4.2 后端门禁：`python manage.py check`、`ruff check`、`ruff format --check`（改动路径）、`pytest tests/graybox/unit`。验证：全部通过且无新增告警。
- [x] 4.3 架构门禁：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。
- [x] 4.4 前端门禁：`npm run build:check`（含 `vue-tsc --noEmit`）+ `/vue-frontend-check` 清单逐项记录。验证：构建与类型检查无错、门禁项全部有结论。**偏差记录**：`npm run build:check` 的 `vue-tsc` 段被既有错误挡住（同 2.3），单独跑 `npm run build` 已通过（✓ built in 2m 32s）；`/vue-frontend-check` 三块报告已出（缺陷 0，六.4 数据流走查逐项）。
- [x] 4.5 端到端复验：用真实浏览器在运行中的平台上上传一个含子目录的 Skill 文件夹，确认返回 200、卡片出现在「自定义 Skill」目录、Skill 查看页能看到子目录层级，并核对磁盘结构；完成后删除该临时 Skill。验证：`logs/backend.log` 中该次请求为 200 且磁盘层级与提交一致。**实测**：真实 Chromium 经 `POST /api/ai/toolbox/upload-skill/` 得 200（id=113），目录树返回 `references/a.md`，列表项 `origin=uploaded`、`missing=false`；磁盘 `probe-skill-e2e/references/a.md` 存在；已用 `api.delete_shared_tool` 清理，`engines/ai/skills` 与 skill 记录回到原状。

## 5. 上传 Skill 的介绍（frontmatter description）

- [x] 5.1 `apps/ai_assistant/views_toolbox_drf.py::upload_skill` 把已解析的 `SKILL.md` frontmatter `description`（trim 后）传给 `api.create_shared_skill(..., description=...)`，不再落到「{file_count} 个文件 — {features}」兜底。验证：5.2 的断言通过。
- [x] 5.2 在 `tests/graybox/unit/test_ai_shared_skill_upload.py` 的成功用例中断言该 Skill 记录的 `description` 等于 frontmatter 的 `description`，且不等于「N 个文件」摘要。验证：`pytest tests/graybox/unit/test_ai_shared_skill_upload.py` 全绿。
- [x] 5.3 接口文档 §6.6 补一句：该 Skill 的介绍 = `SKILL.md` frontmatter 的 `description`。验证：文档与 `upload_skill` 代码一致。
- [x] 5.4 复验前序上传的 `appliance-test-cases`（id=114）介绍改为 frontmatter 那段（一次性，不动目录），并从共享工具箱列表读取确认。验证：列表 `description` == frontmatter `description`。**实测**：`temps/fix_uploaded_skill_intro.py` 一次性回填，列表接口返回 114=`家电测试用例编写 — 面向 IoT 智能家电…`（原为「2 个文件 — MD: 2」）；同一脚本还发现并修正了本地 `platform-tools-manual` 的**陈旧介绍**（库中仍写「12 个工具/三类」，磁盘 SKILL.md 已是「17 个工具/六类」——`ensure_disk_skills` 只补缺失行、不刷新已有行）。
