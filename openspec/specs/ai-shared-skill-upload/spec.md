# ai-shared-skill-upload Specification

## Purpose
让用户把本地 Skill 文件夹整目录上传为平台共享 Skill：以文件夹为单位落盘并保留子目录层级，入参不合法时给出可定位的原因，上传失败时把服务端原因如实呈现给用户。

## Requirements

### Requirement: 文件夹式自定义 Skill 上传

系统 SHALL 支持以「文件夹」为单位上传自定义 Skill：请求 MUST 同时提交文件集合与每个文件相对路径的对应集合，系统 MUST 按配对后的相对路径把文件写入该 Skill 的目录，且 MUST 保留子目录层级。Skill 名 MUST 取自请求的 skill 名（文件夹名）。文件夹根目录 MUST 存在 `SKILL.md`，其 frontmatter MUST 含非空 `name` 与 `description`。上传成功后该 Skill MUST 出现在共享工具箱列表中，且 Skill 目录树读取 MUST 能反映刚上传的层级。已存在同名 Skill 文件夹时 MUST 拒绝，MUST NOT 覆盖或改动既有内容；校验未通过时 MUST NOT 创建 Skill 记录，也 MUST NOT 写出任何文件。

#### Scenario: 含子目录的 Skill 上传成功

- **WHEN** 已登录用户上传文件夹 `my-skill`，其中含 `SKILL.md`（frontmatter 有 name/description）与 `references/a.md`
- **THEN** 返回 200 与新 Skill 的 id
- **AND** 磁盘上出现 `engines/ai/skills/my-skill/references/a.md`（子目录层级保留）
- **AND** 该 Skill 的目录树读取返回 `references/a.md`，共享工具箱列表出现该 Skill

#### Scenario: 同名文件夹拒绝且不覆盖

- **WHEN** 用户上传的文件夹名与 `engines/ai/skills` 下已有目录同名
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

### Requirement: 上传入参校验不依赖文件名

系统 MUST NOT 把「文件名是否含路径分隔符」作为文件夹上传的判据；MUST NOT 因此拒绝合法的文件夹上传。入参不合法时系统 MUST 返回 4xx 与可读 message，覆盖：文件集合为空、相对路径集合与文件集合数量不一致、相对路径缺失、路径穿越（含 `..`）、绝对路径、文件不在同一顶层文件夹、相对路径首段与请求的 skill 名不一致、后缀不在白名单、总大小超限。校验 MUST 在创建 Skill 记录与写盘之前完成。

#### Scenario: 缺少相对路径集合的请求

- **WHEN** 客户端只提交文件、未提交每个文件的相对路径
- **THEN** 返回 400，且 message 指明缺少相对路径信息
- **AND** 不返回「只接受文件夹上传」这类把合法文件夹上传彻底挡死的判定

#### Scenario: 文件与相对路径数量不一致

- **WHEN** 提交的文件数与相对路径数不相等
- **THEN** 返回 400 与可读 message，且不创建任何记录或目录

#### Scenario: 路径穿越被拒绝

- **WHEN** 某文件的相对路径为 `my-skill/../evil.md` 或为绝对路径
- **THEN** 返回 400 与可读 message
- **AND** Skill 目录之外不产生任何文件

#### Scenario: 单文件上传被拒绝

- **WHEN** 用户只选了一个文件（没有文件夹相对路径）
- **THEN** 返回 400 与可读 message，且不创建任何记录或目录

#### Scenario: 上传大小与后缀限制仍生效

- **WHEN** 文件夹内某文件后缀不在白名单，或该文件夹总大小超过上限
- **THEN** 返回 400 与可读 message，且不创建任何记录或目录

### Requirement: 上传失败原因对用户可见

上传失败时前端 MUST 展示服务端返回的可读 `message`（经项目统一错误格式化），MUST NOT 用固定通用文案替代服务端 message。上传成功时 MUST 给出成功反馈并刷新目录。

#### Scenario: 服务端 400 原因透出

- **WHEN** 上传因「已存在同名 skill 文件夹」被 400 拒绝
- **THEN** 页面提示包含服务端该 message，而不是「上传失败」这类无成因文案

#### Scenario: 上传成功后刷新

- **WHEN** 上传成功
- **THEN** 给出成功反馈，且「自定义 Skill」目录出现新上传的 Skill 卡片

### Requirement: 上传 Skill 的介绍取自 SKILL.md

上传成功后，该 Skill 记录中的介绍 MUST 取自 `SKILL.md` frontmatter 的 `description`（去除首尾空白），MUST NOT 用文件数量或文件类型摘要替代。共享工具箱列表下发给前端的 `description` MUST 与之一致，使卡片展示该 Skill 自己的介绍。

#### Scenario: 卡片显示 Skill 自己的介绍

- **WHEN** 已登录用户上传文件夹 `my-skill`，其 `SKILL.md` frontmatter 的 `description` 为「家电测试用例编写 — 面向 IoT 智能家电…」这段文本
- **THEN** 该 Skill 在共享工具箱列表中的 `description` 等于该 frontmatter 文本（去首尾空白）
- **AND** 不等于形如「N 个文件 — MD: N」的文件摘要

#### Scenario: 介绍不随文件类型统计变化

- **WHEN** 同一份 `SKILL.md` 所在文件夹增删其它类型的文件后重新上传
- **THEN** 该 Skill 的介绍仍是 frontmatter 的 `description`，不随文件数量或类型统计变化
