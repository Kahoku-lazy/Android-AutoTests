## REMOVED Requirements

### Requirement: Prototype list consumes standard envelope

**Reason**: 页面流模块整体退役，`GET /api/workflow/prototypes/` 端点与前端原型列表均删除，本契约不再有承载实现。

**Migration**: 无替代接口。平台其余模块沿用全局 `{status, data}` 信封（`backend/apps/AGENTS.md` §1.3），不受影响。

### Requirement: Prototype detail consumes standard envelope

**Reason**: 页面流模块整体退役，原型详情端点与工作台均删除。

**Migration**: 无替代接口；全局信封约定不变。

### Requirement: Directory and document reads consume nested data

**Reason**: 页面流模块整体退役，目录树与文档读端点均删除。

**Migration**: 无替代接口；全局信封约定不变。

### Requirement: 目录与原型改名删除走标准方法与信封

**Reason**: 页面流模块整体退役，目录 / 原型的改名与删除端点均删除。

**Migration**: 无替代接口；全局信封约定不变。

### Requirement: 页面流写操作只有一套路由且返回标准信封

**Reason**: 页面流模块整体退役，全部写端点（集合路由创建、导入动作路由）删除，「只有一套路由」的约束对象不复存在。

**Migration**: 无替代接口。其余模块的写路由约定由 `api-path-convention` 继续守护。

### Requirement: 文档更新按提交字段合并并支持归属写入

**Reason**: 页面流模块整体退役，文档更新端点删除，合并语义与目录归属写入不再有承载实现。

**Migration**: 无替代接口；存量页面流文档实测 0 篇，无数据迁移。
