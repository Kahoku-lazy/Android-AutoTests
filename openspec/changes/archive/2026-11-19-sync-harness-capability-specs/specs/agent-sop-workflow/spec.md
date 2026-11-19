## REMOVED Requirements

### Requirement: Verifier steps carry the per-SKU log keyword catalog

**Reason**: 验收关键词不再由引擎按型号文件注入。`engines/agents/config/data/log_keywords/` 已随旧包删除，SOP 抽象不读取型号目录。
**Migration**: 需要日志关键词时，由调用方写进该步的验收说明或提示词正文。关键词的权威清单在平台 `sl_log_keywords`，不在引擎文件。
