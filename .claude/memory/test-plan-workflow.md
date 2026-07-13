---
name: test-plan-workflow
description: 编写模块测试方案的标准四阶段流程
metadata: 
  node_type: memory
  type: project
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

编写模块测试方案的标准四阶段流程。

**为什么重要**：第一次编写 case-manager 测试方案时走了弯路——跳过了 Skill 加载、手动写了方案而浪费了 Plan agent 的结果。后续必须按此流程执行。

**流程**：

```
收到「编写 XX 模块测试方案」需求
  │
  ├─ Phase 1: 代码探索（Explore agent ×1-3 并行）
  │   ├── 前端组件/API/路由完整架构
  │   ├── 后端 models/views/api.py/urls 完整端点
  │   └── 测试基础设施（现有测试模式/框架/脚本）
  │
  ├─ Phase 2: PRD 同步（prd-writer Skill）
  │   └── 审查子PRD → 发现代码与文档差异 → 标注到测试方案
  │
  ├─ Phase 3: 测试规范加载（functional-testing Skill）
  │   └── test-case-design.md → 五维度模型 + 编号规则 + 覆盖率要求
  │
  └─ Phase 4: 输出到 dev_docs/05-开发与测试/{模块}/测试方案-*.md
      ├── 覆盖现有文件（如已存在）
      └── 同步更新 平台级/平台测试方案.md 用例数
```

**关键铁律**：
- 🔴 Phase 2 和 Phase 3 的 Skill 不可跳过——它们提供规范和 PRD 上下文
- 🔴 测试方案必须放在对应模块子目录（如 `05-开发与测试/用例管理/测试方案-04-case-manager.md`）；平台级进 `平台级/`
- 🔴 编号规则：文档方案用模块前缀（如 `CM-`、`DP-`），自动化脚本用 `CASE-` 前缀
- 🟠 Explore agent 最多 3 个并行，覆盖前端/后端/测试三方向
- 🟠 输出后必须同步更新 `平台测试方案.md` 的用例数

**关联**：[[prd-first-workflow]] [[animal-island-ui-api-traps]]
