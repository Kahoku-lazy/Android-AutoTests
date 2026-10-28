## MODIFIED Requirements

### Requirement: 编写与验收成对运行

引擎 SHALL 先按模块切分需求，再为每个模块单独运行一次 GoalPipeline：编写角色只拿本模块的需求片段与原子编号区段，把完整七节文档保存到模块存储，最终 `report` 只写摘要；验收角色从模块存储读取实际文档，只按该片段判卷并给出 `result` / `message`。单个模块不通过时把驳回说明与上一版文档拼进下一轮输入，最多三轮；一个模块通过后继续下一个模块，MUST NOT 因前一个模块通过而跳过后续模块。全部模块通过时整轮运行才标记完成；任一模块达到三轮仍未通过时整轮标记失败，并保留该模块的最后文档与历次判决。

#### Scenario: 第一次驳回后重写

- **WHEN** 某个模块的验收角色第一次给出 `result=fail`
- **THEN** 该模块的编写角色收到驳回说明与上一版文档并定点重写，其它模块不受影响；后续任一轮 `result=pass` 则该模块完成

#### Scenario: 尝试次数用尽

- **WHEN** 某个模块第三轮仍为 `result=fail`
- **THEN** 该模块标记失败，整轮运行阶段为 failed，结果里保留该模块的最后文档与历次判决说明

#### Scenario: 全部模块通过

- **WHEN** 每个模块的验收角色都给 `result=pass`
- **THEN** 整轮运行阶段为 completed，结果文档按模块顺序拼接且每个模块带验收结论

## ADDED Requirements

### Requirement: 模块文档存储

系统 SHALL 为一次用例编写任务提供任务级模块存储，按模块 KEY 保存完整 Markdown 文档与编写报告。编写角色 MUST 通过 `save_case_module_document` 保存完整七节文档；验收角色 MUST 通过 `read_case_module_document` 读取实际文档，MUST NOT 只依据 `report` 自述判卷。

保存工具 MUST 只写入当前模块 KEY，MUST NOT 允许模型跨模块覆盖。存储内容缺失或短于 200 字符时 MUST 视为空交付，按截断处理并进入模块拆分。最终结果文档 MUST 从存储内容拼装，MUST NOT 依赖 `report` 里的摘要。

#### Scenario: 保存后验收读取

- **WHEN** 编写角色调用 `save_case_module_document` 保存 20K 字符的七节文档
- **THEN** 验收角色的 `read_case_module_document` 能读到同一份全文
- **AND** 最终 `Task.result.document` 使用这份存储内容，而不是 `report` 摘要

#### Scenario: 未保存文档

- **WHEN** 编写轮次结束但模块存储里没有该 KEY 的文档
- **THEN** 该模块标记 `truncated=true`，不进入最终拼装，并按截断路径拆分/失败
