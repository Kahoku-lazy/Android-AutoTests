## REMOVED Requirements

### Requirement: 线路连通探测区分密钥可达与模型可用

**Reason**: 校验功能整体下线，系统不再对线路角色发起探测请求。
**Migration**: 无替代探测；模型可用性由任务执行结果直接暴露。

### Requirement: 线路卡片只呈现三种业务状态

**Reason**: 卡片连通徽标随校验功能删除，三态与过程态不再存在。
**Migration**: 卡片身份区改为「名称 / 职责」两行（见 `ai-assistant/route-card-identity`）。
