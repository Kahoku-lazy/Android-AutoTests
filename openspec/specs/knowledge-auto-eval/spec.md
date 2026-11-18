# knowledge-auto-eval Specification

## Purpose
在知识库检索页提供一键自动评测：用 LLM 从模块语料合成带正确答案的评测集，对检索桥跑 Recall@k / MRR / 误命中率并出具可审计报告，为阈值与切块调优、以及将来接回 Agent 的评测门槛提供量化依据。

## Requirements

### Requirement: 合成评测集生成

系统 SHALL 对选定模块以只读方式生成合成评测集：从资料目录采样块（与索引相同的切块参数），经运营选定的 chat 类模型配置生成正题（每题正确答案 = 来源块所在文档，文档级 gold）与负样本（与该模块语料无关的问题）。出题 MUST NOT 创建 Agent，MUST NOT 写资料目录。题量 SHALL 默认 30 正题 + 10 负样本，上限 100；超限请求 MUST 拒绝。评测集 MUST 随运行落库（问题、正确文档、正/负类型、来源块），可复现可审计。

#### Scenario: 生成成功并落库

- **WHEN** 超管对一个已索引模块触发自动评测
- **THEN** 生成默认题量的正题与负样本并随运行落库
- **AND** 每条正题带正确文档与来源块标识

#### Scenario: 超过题量上限被拒绝

- **WHEN** 触发请求的题量超过 100
- **THEN** 返回 400 与可读原因
- **AND** 不创建运行、不调用模型

#### Scenario: 资料目录只读

- **WHEN** 评测集生成完成
- **THEN** 资料目录内文件无任何新增、修改或删除

### Requirement: 指标评分与报告口径

系统 SHALL 以纯函数计算指标：Recall@1/3/5（正题的正确文档出现在前 k 条命中的比例）、MRR（首条正确命中排名倒数的均值，无正确命中记 0）、误命中率（负样本返回 ≥1 条过阈值命中的比例）。命中与 gold 的匹配 MUST 用文档编号，避免同名文件歧义。报告 MUST 含样本数 n 与逐题明细（问题、正确文档、命中列表与排名），MUST 显著标注「合成评测集，结果偏乐观」，MUST NOT 把指标呈现为人工标注结果。

#### Scenario: 手算样例对拍

- **WHEN** 对构造的命中序列与 gold 计算指标
- **THEN** Recall@k、MRR、误命中率与手算期望值一致

#### Scenario: 同名文件按文档编号区分

- **WHEN** 模块内两个不同子目录存在同名文件且只有其一为 gold
- **THEN** 命中匹配按文档编号判定，不因同名误判为命中

#### Scenario: 报告带样本数与合成标注

- **WHEN** 评测完成查看报告
- **THEN** 报告含 n、逐题明细与「合成评测集，结果偏乐观」标注

### Requirement: 评测运行生命周期与权限

`POST /api/knowledge-search/evaluations/` SHALL 仅超级管理员可用，入参为模块、模型配置与题量；该模块已有运行中评测时 MUST 返回 409。运行 SHALL 在后台执行，状态 MUST 可查询（进行中 / 完成 / 失败）；`GET /api/knowledge-search/evaluations/{id}/` SHALL 登录可读，返回进度（已完成 / 总题数）与终态报告；评测列表 SHALL 登录可读。触发时 MUST 冻结模块登记快照，运行期间模块变更 MUST NOT 影响该运行。运行失败 MUST 记录可读原因且 MUST NOT 影响检索入口。触发前 SHALL 展示预估 token 成本。

#### Scenario: 触发后轮询到完成

- **WHEN** 超管触发评测并轮询运行详情
- **THEN** 进度从 0 递增到总题数，终态为完成并带报告

#### Scenario: 非超管触发被拒绝

- **WHEN** 普通登录用户触发评测
- **THEN** 返回 403
- **AND** 仍可读取已有评测报告

#### Scenario: 同模块重复触发被拒绝

- **WHEN** 某模块已有运行中评测时再次触发
- **THEN** 返回 409 与可读原因

#### Scenario: 运行期间模块变更不影响运行

- **WHEN** 评测运行中超管修改该模块路径或禁用该模块
- **THEN** 该运行按触发时快照继续执行并产出报告

#### Scenario: 失败记录原因不拖垮检索

- **WHEN** 出题模型调用失败导致运行失败
- **THEN** 运行终态为失败并带可读原因
- **AND** 知识库提问入口照常可用

### Requirement: 评测用量逐调用入账

评测中的 chat 调用与嵌入调用 SHALL 逐调用向 `ai_usage_records` 写入恰好一条记录：chat category=LLM、嵌入 category=Embedding，source=knowledge_eval，execution_id=运行 ID。幂等键 MUST 为「来源:运行 ID:轮次」，重复提交 MUST NOT 翻倍。入账失败 MUST 只记日志，MUST NOT 阻断评测。费用 SHALL 按既有价目表与通用公式计算，MUST NOT 伪造金额。

#### Scenario: 一次运行的两类用量各自入账

- **WHEN** 一次评测运行完成
- **THEN** 出题 chat 调用与检索嵌入调用各有对应记录，source=knowledge_eval
- **AND** token 数与模型返回用量一致

#### Scenario: 入账失败不阻断评测

- **WHEN** 账本暂时不可写
- **THEN** 评测照常执行并产出报告
- **AND** 失败只记日志

### Requirement: 前端评测区

知识页 SHALL 提供「自动评测」区：触发按钮与参数弹窗（模型下拉取自运营模型配置的 chat 类条目、题量输入）仅超管可见；运行中 SHALL 轮询展示**阶段等待文案**（建索引 / 出题 / 逐题检索）与进度，并**实时展示已完成的逐题明细**；点击某题 SHALL 展示该题的检索命中原文与来源片段。完成 SHALL 展示报告（Recall@1/3/5、MRR、误命中率指标卡 + 逐题明细表 + 合成集标注）。评测区 SHALL 提供「评测原理与判断依据」说明（合成集生成、gold 定义、rank 与三指标口径、合成偏差）。三态 SHALL 用共享组件，加载期间 MUST NOT 渲染空态。非超管 SHALL 可查看历史报告但 MUST NOT 看到触发入口。

#### Scenario: 超管触发与非超管只读

- **WHEN** 超管打开知识页评测区
- **THEN** 可见触发按钮与参数弹窗
- **WHEN** 普通用户打开评测区
- **THEN** 只见历史报告列表，无触发入口

#### Scenario: 运行中可见过程

- **WHEN** 评测运行中
- **THEN** 评测区显示当前阶段文案与已完成 / 总题数进度
- **AND** 已完成的题目实时出现在明细表，点击某题可见其检索命中原文与来源片段

#### Scenario: 进度与报告展示

- **WHEN** 运行完成
- **THEN** 展示指标卡、逐题明细与「合成评测集，结果偏乐观」标注
- **AND** 评测原理说明可见，含 gold 定义与三指标口径
