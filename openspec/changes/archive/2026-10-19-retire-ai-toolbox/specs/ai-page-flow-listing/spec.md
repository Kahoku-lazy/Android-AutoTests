## REMOVED Requirements

### Requirement: 页面流文档列表为全量并含目录层级

**Reason**: `list_page_flows` / `get_page_flow` 只存在于平台侧工具注册表，其调用入口为工具箱调试页与内部工具网关；两者删除后工具不再存在，SOP 执行链也不装配该工具。
**Migration**: 页面流内容改由页面流页（`/workflow`）人工查看；智能体不再拥有该工具。
