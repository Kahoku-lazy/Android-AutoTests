## MODIFIED Requirements

### Requirement: 文件夹式自定义 Skill 上传

系统 SHALL 支持以「文件夹」为单位上传自定义 Skill：请求 MUST 同时提交文件集合与每个文件相对路径的对应集合，系统 MUST 按配对后的相对路径把文件写入该 Skill 的目录，且 MUST 保留子目录层级。Skill 名 MUST 取自请求的 skill 名（文件夹名）。文件夹根目录 MUST 存在 `SKILL.md`，其 frontmatter MUST 含非空 `name` 与 `description`。上传成功后该 Skill MUST 出现在共享工具箱列表中，且 Skill 目录树读取 MUST 能反映刚上传的层级。已存在同名 Skill 文件夹时 MUST 拒绝，MUST NOT 覆盖或改动既有内容；校验未通过时 MUST NOT 创建 Skill 记录，也 MUST NOT 写出任何文件。共享技能目录 MUST 是 `engines/agents/skills/shared`。SOP 使用的 `engines/agents/skills/common` 与 `engines/agents/skills/executor` MUST NOT 被这次扫描列入共享工具箱，也 MUST NOT 被上传覆盖。

#### Scenario: 含子目录的 Skill 上传成功

- **WHEN** 已登录用户上传文件夹 `my-skill`，其中含 `SKILL.md`（frontmatter 有 name/description）与 `references/a.md`
- **THEN** 返回 200 与新 Skill 的 id
- **AND** 磁盘上出现 `engines/agents/skills/shared/my-skill/references/a.md`（子目录层级保留）
- **AND** 该 Skill 的目录树读取返回 `references/a.md`，共享工具箱列表出现该 Skill

#### Scenario: 同名文件夹拒绝且不覆盖

- **WHEN** 用户上传的文件夹名与 `engines/agents/skills/shared` 下已有目录同名
- **THEN** 返回 400 与可读 message
- **AND** 既有目录内容与 Skill 记录逐字节不变

#### Scenario: 根目录缺少 SKILL.md

- **WHEN** 用户上传的文件夹根目录没有 `SKILL.md`
- **THEN** 返回 400 与可读 message
- **AND** 不创建 Skill 记录，也不写出任何文件

#### Scenario: SKILL.md frontmatter 缺字段

- **WHEN** `SKILL.md` 的 frontmatter 缺少 `name` 或 `description`（或为空）
- **THEN** 返回 400 与可读 message
- **AND** 不创建 Skill 记录，也不写出任何文件

#### Scenario: 角色技能目录不进共享列表

- **WHEN** 共享工具箱扫描技能目录
- **THEN** 列表不包含 `common` 与 `executor` 这两个角色目录
- **AND** 这两个目录下的已有技能文件保持不变
