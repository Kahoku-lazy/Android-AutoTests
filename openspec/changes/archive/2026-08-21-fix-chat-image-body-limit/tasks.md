## 1. 配置修复

- [x] 1.1 `config/settings.py` 新增 `DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024`——验证 `manage.py check` 通过、shell 读取 settings 值 = 16MB

## 2. 验证与归档

- [x] 2.1 算术与链路确认：5MB 图片 base64（≈6.7MB）< 16MB；边界实测 7MB 假图片请求返回 400「图片过大（最大 5242880 字节）」，不再抛 RequestDataTooBig
- [x] 2.2 `openspec archive fix-chat-image-body-limit` 归档本 change
