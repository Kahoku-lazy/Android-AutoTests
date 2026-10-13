## 1. 修复与测试

- [x] 1.1 验收角色的截图工具包装改为"仅当被包装实现声明了 `user_id` 时才转发"；验证：新增单测分别用"引擎自带签名（无 user_id）"与"平台签名（有 user_id）"两种实现调用包装后的工具，前者不因 `user_id` 报错、后者能拿到归属
- [x] 1.2 全仓 grep 同类写法（包装层无条件转发 `user_id`）；验证：除本处外无其它命中，或已在 design 遗留里登记
- [x] 1.3 回归：`pytest tests/graybox/unit -q -k "verifier or workflow or agent"` 全绿（除既有前端抽取存量红外）；`python -m ruff check engines/ai` 通过
- [x] 1.4 引擎级端到端复跑：验收侧截图调用不再报错，页面类断言能凭截图判定；验证：留存跑测输出与 `logs/agents-*.log` 片段
