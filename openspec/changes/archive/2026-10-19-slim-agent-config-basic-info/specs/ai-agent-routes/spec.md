## REMOVED Requirements

### Requirement: 智能体支持多线路模型配置

**Reason**: 配置页只保留基本信息，不再提供线路模型配置入口；线路内的模型数据改由后台/数据初始化维护。
**Migration**: `route_configs` 数据结构与执行链装配保持不变；配置页只写线路的 name/avatar。
