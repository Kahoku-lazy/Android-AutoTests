## REMOVED Requirements

### Requirement: 文件夹式自定义 Skill 上传

**Reason**: AI 工具箱整体下线，共享 Skill 的上传入口与列表随之删除。
**Migration**: 引擎侧 Skill 仍由 `engines/agents/skills/` 目录装配，随代码发布；平台不再提供上传。

### Requirement: 上传入参校验不依赖文件名

**Reason**: 上传端点已删除。
**Migration**: 无。

### Requirement: 上传失败原因对用户可见

**Reason**: 上传端点已删除。
**Migration**: 无。

### Requirement: 上传 Skill 的介绍取自 SKILL.md

**Reason**: 共享工具箱列表已删除。
**Migration**: 无。
