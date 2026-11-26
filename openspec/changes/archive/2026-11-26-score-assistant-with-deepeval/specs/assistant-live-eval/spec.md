## REMOVED Requirements

### Requirement: 评测使用草稿自己的模型且不触达真实副作用

**Reason**: 真模型假世界自测整条链路退役；新的评分只调判分模型，用 G-Eval 打分，不需要假世界替身。
**Migration**: 评测入口下架，替代路径见 `assistant-eval-score`（评分）；历史 `ai_assistant_live_runs` 记录随表删除。

### Requirement: 助手与 SOP 走各自的运行链

**Reason**: 不再用两轮探针判断对话实例，也不再用剧本回放判断 SOP；评分对两类对象都只做「提示词 + 交接文本」两件事。
**Migration**: 助手与工作流共用同一套评分；目标类型只影响交接文本来源（对话栏日志 / 任务报告）。

### Requirement: 评测过程可逐条查看

**Reason**: 评分产物是「分数 + 理由」，没有逐样本过程可看；旧的过程视图与进度轮询一并下线。
**Migration**: 前端评测页改为评分卡与历史对比；旧 `/api/ai/evals/runs/{id}/` 下架。

### Requirement: 发布只认四条规则

**Reason**: 四把规则（未勾选工具、验收者写操作、连续重复、实例变化）不再作为发布条件。
**Migration**: 发布改由「草稿 + 编辑权」判定；这些现象若仍要观察，属于日志/报告范畴，不再阻塞发布。

### Requirement: SOP 发布认当前评测，其它组合不被新门误伤

**Reason**: 发布门禁整体消失，该要求的「认当前评测」前提不复存在。
**Migration**: 目标流、团队流、SOP、名片的发布口径统一为「草稿 + 编辑权」。

### Requirement: 评测用量按次入账且失败不阻断

**Reason**: 入账口径转移到评分链路（判分模型调用单独入账），旧评测不再产生用量。
**Migration**: 新口径见 `assistant-eval-score` 的「判分用量按次入账」；已入账的历史 `assistant_eval` 用量保留不删。
