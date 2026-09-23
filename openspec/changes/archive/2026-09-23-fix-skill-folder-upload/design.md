## Context

现状链路（本单全部涉及）：`ToolboxPanel.vue` 的「+ Skill 文件夹」（`input[type=file][webkitdirectory]`）→ `useToolbox.onSkillFolderPicked` → `api/toolbox.ts::uploadSharedSkill`（FormData：`name` + 每个文件的 `files`，第三参数传 `webkitRelativePath`）→ `POST /api/ai/toolbox/upload-skill/` → `ToolboxViewSet.upload_skill` → `api.create_shared_skill` + 写 `engines/ai/skills/<文件夹名>/`。

本单成立所依赖的实测事实（真实 Chromium + axios 抓包、把抓到的原始字节回放给运行中的服务）：

1. 浏览器发出的 multipart 请求头带合法 boundary，body 里也确实写着 `filename="probe-x/SKILL.md"`；显式设置 `Content-Type: multipart/form-data` 无害（浏览器自行补 boundary）。
2. Django 的 `UploadedFile._set_name` 必然执行 `name = os.path.basename(name)`，于是 `request.FILES[...].name` 恒为纯文件名（实测 `'SKILL.md'`）。用 Django 自己的 `MultiPartParser` 解析同一份字节得到同样结果。
3. 因此 `upload_skill` 里 `if "/" not in first_rel` 的守卫恒真：日志里两次真实点击（2026-09-16、2026-09-22）响应体均 93 字节 = 错误信封 + `只接受文件夹上传，请选择包含 SKILL.md 的文件夹`。
4. 目录结构是用户可见行为：`SkillTreeAPIView` 经 `build_skill_tree` 按磁盘真实结构输出，Skill 查看页据此渲染树。

## Goals / Non-Goals

**Goals:**

- 让「+ Skill 文件夹」真正可用，且落盘保留子目录层级。
- 让上传失败的原因可定位（服务端可读 message 直达用户）。
- 为这条路径补上自动化测试（此前后端/前端均无任何覆盖，回归得以无声上线）。

**Non-Goals:**

- 不改权限模型（仍为已登录用户可上传）、不改响应信封、不改 Skill 目录树 / 文件读取端点契约。
- 不统一其它三处吞服务端 message 的写法（平台工具 / 平台配置 / 知识库）。
- 不把 `python-frontmatter` 补进依赖声明。
- 不为写盘中途失败引入事务或回滚改造。

## Decisions

**D1 相对路径以独立 multipart 字段 `paths` 传递，与 `files` 平行一一对应。**
理由：这是唯一能可靠携带目录层级的通道（文件名通道已被框架抹平）。备选与取舍：(a) 继续从文件名推断目录——已证不可行；(b) 前端把路径拼进文件名字符串——同样被 basename，无效；(c) 只用 `name` 字段当文件夹名、文件拍平落盘——丢掉层级，会让 `references/`、`scripts/` 这类 Skill 失效（`skill-creator` 即是）；(d) 自定义 `FileUploadHandler` / `MultiPartParser` 保留相对路径——改动面大且依赖框架内部行为，收益不划算。客户端 MUST 按 `files` 与 `paths` 各自保持提交顺序配对。

**D2 所有入参校验前移到"创建记录与写盘之前"一次完成。**
校验项：`files` 非空；`paths` 与之数量一致；每条路径非空、非绝对、不含 `..` 段；所有路径同属一个顶层目录；顶层目录名与请求的 `name` 一致；根目录存在 `SKILL.md` 且 frontmatter 的 `name`/`description` 非空；后缀在白名单内；总大小不超上限。任一不符 → 4xx + 可读 message，且不产生记录与文件。不做"猜测式修正"（不自动去掉前缀、不自动改名）。

**D3 落盘相对路径 = 该文件 `paths[i]` 去掉顶层文件夹前缀，直接用 `os.path.join(skill_dir, rel)`。**
与现状唯一的差别是 `rel` 来自 `paths` 而非被 basename 过的 `f.name`；`os.makedirs(os.path.dirname(dest))` 即自然还原子目录。

**D4 保留"先建 DB 行、再写盘"的既有顺序，只调整校验位置。**
最小 diff；中途写盘失败留下的孤儿行由列表里既有的 `missing` 标记暴露（不静默）。

**D5 前端失败提示统一走 `formatApiError(e, '上传失败')`。**
项目既有约定（`shared/types/api-error.ts`），4xx 信封的 `message` 会被原样透出；第二参数仍是兜底文案，网络类错误不至于无话可说。

**D6 上传 Skill 的「介绍」唯一来源是 SKILL.md frontmatter 的 `description`。**
本地 Skill 的介绍就来自 frontmatter（`scan_skill_folders` → `_parse_skill_md` → `ensure_disk_skills` 写库），上传路径也已经把该字段解析出来（用于必填校验）却没往下传，于是 `api.create_shared_skill` 落到了兜底摘要「{file_count} 个文件 — {features}」，卡片因此没有介绍。上传时 MUST 把解析出的 `description`（trim）传给它（该参数本已存在）。备选与取舍：(a) 列表读取时改从磁盘 frontmatter 取介绍——与既有 `update_shared_tool`（可改 description）形成「盘 vs 库」两套真相源，且要额外重扫磁盘，舍弃；(b) 新增一个「技能介绍」字段——库里不存在第二个字段、本地 Skill 也无先例，舍弃；(c) 取正文首个 H1 当介绍——本地 Skill 无此行为，属新规则，舍弃。前端不需要改动：`ToolboxPanel.vue:230` 已在渲染 `item.description`，`.tb-card-desc` 无行数截断。

## 模块防火墙自检

- 后端只改 `apps/ai_assistant/views_toolbox_drf.py`，写库仍走既有 `apps/ai_assistant/api.py::create_shared_skill`，无直接 ORM 写、无跨 App import、无跨 App 文件写。
- 前端只改本模块 `api/toolbox.ts` 与 `composables/useToolbox.ts`，HTTP 仍只经 `shared/api-client`；不新增端点、不直连数据库。
- 本设计不引入新的跨模块依赖。

## Risks / Trade-offs

- [`paths` 与 `files` 顺序错配会导致落错位置] → 数量一致性 + 同顶层目录 + 顶层名与 `name` 一致三重校验，不符即 400，不做修正。
- [`paths` 是契约新增，旧客户端不带] → 返回明确 400（message 指明缺少相对路径信息）；仓库内只有本前端一个调用方，与后端同版本发布。回滚只需还原两个文件。
- [写盘中途失败留下无目录的记录] → 既有 `missing` 标记可见；事务化列为非目标。
- [后缀白名单偏窄可能拒绝真实 Skill] → 维持现状（本单不改策略），仅在接口文档写明白名单与 50MB 上限，避免再被误判为 Bug。
- [同名判定在 Windows 上不区分大小写] → 沿用既有 `os.path.isdir` 判定，与删除/列表行为保持一致。

## Migration Plan

- 无数据库迁移、无数据回填、无依赖变更。
- 发布：后端与前端必须同批（新增 `paths` 字段）。
- 回滚：还原 `views_toolbox_drf.py`、`api/toolbox.ts`、`useToolbox.ts` 三个文件即可；期间成功上传的 Skill 目录与记录不受影响。

## Open Questions

（无）
