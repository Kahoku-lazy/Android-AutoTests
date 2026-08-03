# CLAUDE.md

## 行为准则

1. **先读文档，后写代码，不假设。不隐藏困惑。呈现权衡。** 需求不明确时， 先看 PRD 验收条件，列出可能的理解，让用户选择——不要默默挑一种执行

2. **用最少的代码解决问题。不接受过度设计。**不添加需求之外的功能。用户说"加个筛选条件"，不要顺便"优化整个表格组件"

3. **只碰必须碰的。只清理自己造成的混乱。**不要"顺手"改进相邻代码、注释、格式。diff 中每一行都应能追溯到用户的请求

4. **定义成功标准。循环验证直到达成。**将指令转化为可验证的目标：

### 5. 报错先诊断，不动手

**看到错误日志、堆栈、浏览器 console 报错、服务异常时，禁止直接猜原因改代码。** 必须先在文字中完成以下三步：

1. **复述现象**："我看到了什么"
2. **列出可能原因**："可能的根因有 A / B / C"
3. **提出验证计划**："下一步查什么来确认"

等用户确认方向后再动代码。**用户说"修一下"不等于可以跳过诊断。**


## 模块防火墙

> 详细规则 → `.claude/rules/api-conventions.md`

```
✅ 跨 App import Model（只读查询）
✅ 跨 App import api.py（复杂写操作）
❌ 跨 App import service/runner/consumer/state_machine（内部实现）
❌ 跨 App 直接 ORM 写（INSERT/UPDATE/DELETE 必须走 api.py）
❌ 前端直连数据库
❌ 仪表盘做写操作
❌ 错误提示暴露技术术语给用户
```

---

## 项目工具


| 工具                                                  | 用途                 |
| --------------------------------------------------- | ------------------ |
| `python tools/gen_arch_stats.py`                    | 自动统计表/端点/Tool/步骤类型 |
| `python tools/gen_arch_stats.py --check-md`         | 检测文档是否落后代码         |
| `python tools/gen_arch_stats.py --check-boundaries` | 检测跨模块 ORM 写违规      |
| `python run.py start / stop / status`               | 启动/停止/检查平台         |


---


## 关键约定

- API 响应统一 `{ok, data}` 或 `{ok, error}`
- JSON 字段 snake_case，前端变量 camelCase
- 数据库表前缀：`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_`
- 步骤类型唯一真相源：`models/step_types.py::StepType` 枚举
- 设备状态唯一真相源：`apps/device_pool/models.py`（ONLINE/BUSY/OFFLINE）
- API Key 加密存储，前端脱敏展示，日志不输出 Key

