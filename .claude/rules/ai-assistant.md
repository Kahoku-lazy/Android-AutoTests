# AI Assistant Rules — Android-AutoTests

## SOP 四阶段工作流

这是注入到所有 Agent system_prompt 中的核心工作流：

### 阶段 1：需求分析与用例设计
- 目标：理解需求 → 设计用例方案 → 用户确认
- 规则：需求不明确时必须逐项询问，禁止跳过；设计方案必须等用户确认后才进入下一阶段
- 产出：`case_design` JSON

### 阶段 2：元素准备
- 目标：确保用例所需页面元素已存在
- 规则：缺失元素告知用户具体缺少什么，记录 gaps 到 `sop_context`
- 产出：`element_mapping` + `element_gaps`

### 阶段 3：用例创建与调试
- 目标：创建测试用例 → 调试到 PASS
- 规则：步骤中使用阶段 2 获取的 XPath；调试失败 → 分析原因 → 调整 steps → 重新 save + debug；必须全部 PASS 才能进入执行阶段
- 产出：`case_ids`

### 阶段 4：任务执行
- 目标：锁定设备 → 创建任务 → 执行 → 释放
- 规则：`loop_count` 默认为 3（用户未指定时）；执行完毕后必须释放设备
- 产出：`run_id` + `run_results`

## SOP 状态机

```
create_test_sop (phase=1→2)
  → update_test_sop (phase=2→3)
    → update_test_sop (phase=3→4)
      → update_test_sop (phase=4, status='completed')
任意阶段可转为 → update_test_sop (status='cancelled')
```

`sop_context` 字段随阶段推进逐步填充：Phase 1→`requirement` `case_design`，Phase 2→`element_mapping` `element_gaps`，Phase 3→`case_ids` `debug_notes`，Phase 4→`run_id` `run_results`。

## 两层工具体系

| 层级 | 存储 | 用途 |
|------|------|------|
| Plan 工具 (TaskCreate/Get/List/Update) | agent.state.tasks_context（内存） | 阶段内子任务拆解和进度追踪 |
| SOP 工具 (create/update_test_sop) | Django DB `tr_test_sop`（持久化） | 跨阶段状态机，记录产出和推进阶段 |

## 用户确认 (HITL)

部分工具需要用户确认：Agent → `REQUIRE_USER_CONFIRM` 事件 → 前端确认弹窗 → `POST /confirm-result` → AgentScope 收到 `ALLOW/DENY`。

## 对话恢复

SOP 上下文 (`tr_test_sop`) 持久化在数据库，支持跨会话/跨服务恢复。AgentScope 重启后从 Django DB 重建会话。
