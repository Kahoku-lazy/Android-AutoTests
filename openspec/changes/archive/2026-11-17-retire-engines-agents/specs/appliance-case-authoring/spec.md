## REMOVED Requirements

### Requirement: 用例编写角色按需求原子产出完整用例文档

**Reason**: 用例产物的承载格式是用例 YAML 模型，随 `workflow/case_file.py` 与 `case_artifact*.py` 下线，编写角色失去产出物与验收判据。

**Migration**: 无替代。需要批量产出用例时，改为按 SOP 步骤 YAML（`engines/ae_harness/workflow/sop/steps/*.yaml`）编写，交由后端 `task_list` 执行。

### Requirement: 用例验收角色独立判卷

**Reason**: 判卷对象（用例文档产物）不再存在。

**Migration**: 无替代。

### Requirement: 编写与验收成对运行

**Reason**: 编写侧下线，成对运行的编排随之删除。

**Migration**: 无替代。

### Requirement: 需求按模块切分

**Reason**: 该切分服务于用例文档的模块化产出，产出格式已下线。

**Migration**: 无替代。

### Requirement: 输出截断检测与拆分

**Reason**: 检测针对用例文档的流式输出，链路已删除。

**Migration**: 无替代。

### Requirement: 模块化结果拼装

**Reason**: 拼装目标是用例文档，链路已删除。

**Migration**: 无替代。

### Requirement: 模块文档存储

**Reason**: 用例文档的模块存储目录与写入实现随包删除。

**Migration**: 无替代。

### Requirement: 确定性校验

**Reason**: 校验对象是用例 YAML 的确定性字段，YAML 模型已下线。

**Migration**: 无替代。保留 SOP 步骤 YAML 的结构校验，由后端在提交与执行前完成。

### Requirement: 编写角色用计划模式跟踪五阶段

**Reason**: 编写角色本身删除。

**Migration**: 无替代。
