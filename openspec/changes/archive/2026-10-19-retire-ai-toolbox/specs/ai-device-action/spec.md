## REMOVED Requirements

### Requirement: 智能体可发现设备已安装的 App 包名

**Reason**: 该平台侧只读工具只存在于 `apps/ai_assistant/tools.py`，调用入口为工具箱调试页与内部工具网关；两者随本变更删除后工具不再存在，SOP 引擎也未装配该工具。
**Migration**: 包名仍可在设备管理/检查器侧查看；智能体不再拥有该工具。

### Requirement: 平台侧设备工具在本变更中保持不变

**Reason**: 平台侧设备动作工具已随 `apps/ai_assistant/tools.py` 删除，不再有「平台侧工具」这一面。
**Migration**: 设备动作只保留引擎侧（`engines/agents/tools/tool_device.py`）一套，其行为与返回契约不变。
