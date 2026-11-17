## REMOVED Requirements

### Requirement: 用例工作台分栏版式

**Reason**: 目录和文件已删除，项目页不再有左树右预览。
**Migration**: `/cases/projects/:projectId` 直接打开该项目的一张表。旧的 `/cases/projects/:projectId/files/:fileId` 重定向到对应项目；项目不存在时进入项目列表。

### Requirement: 右栏用例预览只读且固定五列

**Reason**: 右栏预览依赖用例文件，文件层已删除。
**Migration**: 用例的查看与编辑都在项目表完成，不再提供「进入页面编辑」。

### Requirement: 目录树行不标注节点类型且在窄左栏内不溢出

**Reason**: 项目页不再渲染目录树。
**Migration**: 分类改由项目表的筛选、排序和分组视图完成。

### Requirement: 用例工作台与元素定位工作台共用同一套工作台视觉

**Reason**: 用例项目页不再使用分栏工作台。元素定位工作台不在本次范围。
**Migration**: 用例项目页使用单张表纸。元素定位的分栏视觉保持不变。

### Requirement: 树行只表达结构与名称

**Reason**: 用例项目不再有树行。
**Migration**: 项目名称显示在页头标题，行内容显示在项目表。
