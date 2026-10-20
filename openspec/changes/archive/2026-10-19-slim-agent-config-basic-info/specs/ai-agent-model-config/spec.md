## REMOVED Requirements

### Requirement: 配置页统一管理三类模型

**Reason**: 配置页已收缩为只保留基本信息，不再提供模型配置区块。
**Migration**: 模型配置保留在 `route_configs` 数据中，改由后台/数据初始化维护；配置页不再读写。

### Requirement: 强模型开关控制路由

**Reason**: 该需求描述的是已下线的对话路由管线，配置页也不再提供强模型开关。
**Migration**: 无；平台不再有对话路由。

### Requirement: 强模型名留空回退视觉模型

**Reason**: 强模型与视觉模型配置已不在配置页，回退规则随对话管线一并退役。
**Migration**: 无。

### Requirement: 卡片页收敛为对话配置测试

**Reason**: 卡片当前只保留「校验 / 配置」，不再有对话与测试入口；该需求描述的三个操作已不存在。
**Migration**: 卡片入口以 `ai-assistant/route-card-identity` 为准（校验 + 配置）。

### Requirement: 模型清单标明多模态能力

**Reason**: 配置页不再提供模型清单。
**Migration**: 无。

### Requirement: 需要图片的角色绑定纯文本模型时给出提醒

**Reason**: 配置页不再展示角色模型配置，界面提示无从产生；引擎侧也没有对应的装配告警实现。
**Migration**: 执行/验收角色的多模态标记仍由引擎角色配置声明（`vision=True`）。
