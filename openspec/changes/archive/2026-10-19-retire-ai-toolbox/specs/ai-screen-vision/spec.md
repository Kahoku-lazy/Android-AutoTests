## REMOVED Requirements

### Requirement: 智能体可读取当前页面文本坐标

**Reason**: OCR 工具只存在于平台侧工具注册表（`apps/ai_assistant/tools.py`），其调用入口只有工具箱调试页与内部工具网关；两者随本变更删除后该工具不再存在，SOP 引擎也未装配 OCR。
**Migration**: 无替代能力；如需页面文本，改用设备检查器的页面分析能力（面向人工）。

### Requirement: OCR 工具复用设备可用性约束

**Reason**: OCR 工具已删除，约束无对象。
**Migration**: 无。

### Requirement: OCR 工具在 AI 工具箱中按视觉识别分组

**Reason**: AI 工具箱已下线。
**Migration**: 无。
