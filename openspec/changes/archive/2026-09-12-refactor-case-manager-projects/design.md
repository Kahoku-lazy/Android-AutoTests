## Context

见 `proposal.md` 的 Why。现行 `case_manager` 按 `case_type` 拆四套模型、路由、编辑器；目录树挂在类型下，无项目层；`TestDefinition.steps_json` 与 `test_runner` / 编辑锁 WS 耦合。本期在同一 App 内改形，不新建 Django App。

## Goals / Non-Goals

**Goals:**

- 增加 `CaseProject`，目录与用例归属项目，目录不限层级
- 用例收成文档字段；标准信封 REST；前端项目列表 + 工作台
- 迁移清空旧四类数据；拆除四类型 API、预览、编辑锁 WS

**Non-Goals:**

- 不恢复自动执行、单步调试、YAML 导入导出、逐步配对清单
- 不新建用例管理 App、不复用 workflow 文档表
- 不把 `test_runner` 改造成跑文档用例
- 不在本期做项目成员协作、分享、权限矩阵（仅按创建者/当前用户隔离）

## Decisions

1. **原地改 `case_manager`，不平行新模块**  
   表前缀 `cm_`、防火墙与前端模块边界保持不变。备选（新 App、挂到 workflow）会跨职责或重复 CRUD，已否决。

2. **三表：项目 / 目录 / 用例**  
   `TestDefinition` 保留表名但砍可执行字段，避免下游 import 名大面积改符号；语义改为文档用例。备选（新表 `cm_case_docs`）更干净但跨模块改名成本高。

3. **用例 ID `TC-YYYYMMDD-NNNN`**  
   同日序号四位，全局唯一；创建时后端生成，前端只读。备选 UUID 不利于人工沟通。

4. **枚举存 snake/英文码，UI 显示中文**  
   `test_type`: `app|web|api|func`；`business_type`: `appliance|lighting|app`。HTTP JSON snake_case。

5. **树接口一次返回目录+用例节点**  
   `GET /projects/{id}/tree/` 减少往返。拖拽走独立 `POST /move/`，服务端校验禁止拖入自身子孙。

6. **用例可挂项目根（directory 可空）**  
   与「先建目录再建模」不强制；树根同时可有目录节点和用例节点。

7. **标准信封，删除 legacy 平铺与四类型路径**  
   本期允许对 `/api/cases/*` 做破坏性清理。`test_runner` / dashboard / AI Tool 同步改读新定义或停止写结构化步骤。

8. **去掉 case-editing WS**  
   文档用例无协同锁；`gateway/routing.py` 只保留执行进度 WS。须同步 ARCH「2 个生产点」口径为 1。

9. **前端路由**  
   `/cases` 项目列表；`/cases/projects/:projectId` 工作台；可选 `.../cases/:caseId` 深链。侧栏单项入口。

10. **时间格式**  
    展示 `YYYY-MM-DD-HH:mm:ss`（例 `2026-09-09-12:00:24`）；存储仍用 DateTimeField UTC/项目默认时区，序列化层格式化。

## 模块防火墙自检

- 跨 App：`test_runner` / `dashboard` / `ai_assistant` 只读 `case_manager` Model 或走其 `api.py`；禁止 import `views_*` / `consumers` / 内部 service
- 写操作：项目、目录、用例的 INSERT/UPDATE/DELETE 只在 `apps/case_manager` 的 `api.py`（可拆 `api_projects.py` 再由 facade 导出），View 只分发
- 禁止跨 App import service/runner/consumer/state_machine
- 前端只经 `djangoClient` → `/api/cases/...`；仪表盘只读聚合，不写用例表
- 不新增 WS；删除编辑锁通道，不引入 SSE

## Risks / Trade-offs

- [旧数据不可恢复] → 迁移前文档写明清空；本地/测试库可接受，生产须运维确认备份
- [执行引擎暂时无用例可选] → 明确错误文案；执行能力后续单独立项
- [ARCH/AGENTS 仍写四类型与双 WS] → 实现时同步 `ARCH-00`、`apps/case_manager/AGENTS.md`、前端 `case-manager/AGENTS.md`、`API-用例管理.md`
- [无限层级拖拽环] → 移动前做祖先链检测，409 中文错误
- [同日 ID 并发撞号] → 生成序号时按日加事务/唯一约束，冲突则重试

## Migration Plan

1. 部署前备份 `cm_*` 表
2. 迁移：删除四类用例与旧目录行 → 改 schema（加 project、砍字段、删 Web/API/Storage 表）
3. 发版同时上线前端新路由；旧书签跳转 `/cases`
4. 回滚：只回滚代码无法恢复已清空数据，必须靠备份

## Open Questions

无（会改变范围的问题已在方案阶段拍板）。
