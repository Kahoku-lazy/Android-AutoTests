## Context

动机见 proposal.md - Why。方案所需的现状约束：

- 关键词表 `sl_log_keywords` 已落库（上一单已归档）：一行 = 关键词 × 功能点 × 范围，唯一键 `(keyword, feature_id, scope)`；`api.py` 已有 `upsert_keyword`（update_or_create 语义）/ `delete_keyword` / `list_keyword_rows` / `keyword_mapping_for_sku`。
- 端口 CRUD 先例已落地（add-serial-log-custom-ports，16/17）：`LogPortListAPIView.post`（超管校验 → service → 201）、`LogPortDetailAPIView.patch/delete`（ValueError → ValidationError 400）；前端 `PortFormDialog.vue` + `useCustomPorts.ts` + `helpers/port-form.ts` 是弹窗 / 编排 / 校验的现成范式。
- 目录契约现状：`GET /keywords/` 返回分组条目 `{keyword, features:[{id, module, feature, scope}]}`，**无行主键**——编辑/删除需要定位键。
- 并行变更协调：add-serial-log-custom-ports 的 delta 修改「串口日志拥有端口监听开关状态 / 接口路径与契约 / 两张表字号呈现 / 页内权限与只读边界」；本单**不触碰这四条**，关键词端点以 ADDED 新需求承接，零交叉。
- 平台 DB 为 MySQL（开发库已含关键词表）；本单**无模型变更、无迁移**。

## Goals / Non-Goals

**Goals:**

- 超管可在页面新建 / 编辑 / 删除关键词条目，写路径收敛 `api.py`，错误可读。
- 非超管体验与现状完全一致（四数据列、零写控件）。
- 复用端口 CRUD 的接口 / 弹窗 / 编排范式，不发明第二套。

**Non-Goals:**

- 不做批量导入 / 导出、不做关键词拖拽排序（sort_order 维护仍走 api）。
- 不动表结构、迁移、engines、采集链路、端口 CRUD。
- 不修改「串口日志接口路径与契约」需求（避免与并行单 delta 交叉；其端口端点口径由该单归档同步）。

## Decisions

**D1 端点与错误口径沿用端口 CRUD 先例。**
`POST /api/serial-log/keywords/`（201）、`PATCH/DELETE /api/serial-log/keywords/<int:row_id>/`（200）；超管校验用 `shared.users.is_superuser`，非超管 `PermissionDenied`（403）；业务错误（重复 / 撞车 / 不存在 / 非法 scope）由 api 抛 `ValueError`，View 转 `ValidationError`（400 可读）。备选「404 表示不存在」被否：端口先例统一 400 可读结论，保持模块内一致。View 只分发，直调 `api.py`（关键词无监听编排，不需要 service 层）。

**D2 目录契约加 `row_id`，其余不变。**
`keywords.collect_keywords()` 的 features 条目加 `row_id`（`LogKeyword.pk`）；前端行结构带 `rowId`，编辑/删除按它定位。分组形状、计数、origin、updated_at 不变。备选「前端按 keyword+feature_id+scope 三元组定位」被否：三元组在 URL 里要转义且易错，主键最稳。

**D3 api 增 create/update，upsert 保留给维护。**
- `create_keyword(keyword, *, module, feature, scope="*", feature_id=None)`：先查唯一键，已存在抛 `ValueError`（可读重复提示）；不存在则走与 upsert 相同的续编/追加逻辑。不复用 upsert 的静默更新语义——新建必须拒绝重复。
- `update_keyword(row_id, *, keyword=None, module=None, feature=None, scope=None, feature_id=None, sort_order=None)`：部分更新；条目不存在抛 ValueError；改动后的唯一键若撞另一行抛 ValueError；scope 走既有白名单校验。至少一个字段，否则 ValueError。
- `delete_keyword` 已有，直接用。

**D4 表单字段与校验（helpers/keyword-form.ts 纯函数）。**
keyword 必填（trim 后非空，≤200）；module 必填（≤100）；feature 必填（≤200）；scope 为 `*` 或 SKU 白名单 `^[A-Za-z0-9_-]+$`（≤100）；feature_id 可选正整数（缺省后端续编，编辑时展示当前值可改）。校验文案进 constants，弹窗与编排各校验一次（沿用 port-form 范式）。

**D5 范围输入：el-select filterable allow-create。**
选项 = 通用 + 全量行已有 SKU 范围（`scopeOptions` 现成）；允许输入新 SKU（如 H6601 未登记过时），后端白名单兜底。备选「纯文本输入」被否：已有范围应可选可避错；备选「联动端口 SKU 列表」被否：关键词范围可先于端口登记存在，不耦合端口数据。

**D6 操作列与新建按钮仅超管可见。**
页面入口把 `useAuthUser().isSuperuser` 以 `can-manage` 传给 `LogKeywordPanel`（与 WifiPortPanel 同法）。超管：COLUMNS 追加操作列（编辑 / 删除，`.sketch-kit` 描边态）+ 页头「新建关键词」按钮；非超管：恰四数据列、页头仅刷新。删除走 `ElMessageBox.confirm` 二次确认（警告文案：删除后该关键词不再参与目录与取词，日志文件不受影响）。

**D7 弹窗模块私有 KeywordFormDialog.vue。**
el-dialog + sketch-kit 表单，新建/编辑复用（编辑时预填行值）；组件只渲染，编排进 `useKeywordCrud.ts`（开合 / 校验兜底 / CRUD 请求 / ElMessage 提示 / 成功后 reload 目录），完全镜像 useCustomPorts 结构。样式只写本组件私有类与 tokens。

**D8 成功后刷新目录，配色口径不变。**
CRUD 成功 → `load()` 重取目录；模块配色仍按全量行首次出现顺序分配（既有逻辑），新建模块可能引入新色相，属预期。

**D9 engines 与采集零改动。**
取词并集口径不变；删除关键词只影响目录与后续取词，不触日志文件。

## 模块防火墙自检

- **跨 App import**：无新增；关键词写入全部收敛 `serial_log/api.py`，View 只分发。
- **前端不直连数据库**：只经 `/api/serial-log/keywords/` 三个写端点 + 既有读端点。
- **engines 边界**：零改动，零 django/apps 依赖新增。
- **与并行单零交叉**：不修改其 delta 涉及的四条需求；共享文件（views/urls/api.ts/constants/panel）的改动按功能分区追加，合入前 review diff。

## 红线变更申请（硬约束：经需求方确认后才动 AGENTS 文件）

**改什么：**
1. `frontend/src/modules/serial-log/AGENTS.md` 红线「关键词表**只读**：不提供新增 / 编辑 / 删除 / 上传 / 保存入口；关键词真相源为数据库 `sl_log_keywords`，改表经后端 `serial_log/api.py`（一期无页面写入口）」→ 改为「关键词表**非超管只读**：普通用户无新增 / 编辑 / 删除入口；超级管理员可经页面新建 / 编辑 / 删除（表单弹窗 + 行内操作），写入经后端 `serial_log/api.py`；真相源为数据库 `sl_log_keywords`」。
2. `backend/apps/serial_log/AGENTS.md` 接口表追加三行（POST / PATCH / DELETE keywords，仅超管）；职责段「关键词对照表持久化与只读组装」改为「持久化、组装与超管维护」；写库边界条款已覆盖 api 唯一写点，不改。

**为什么必须改：** 页面写入口是本单核心行为，原「只读 / 无页面写入口」条款与新规约直接矛盾；不改则后续 AI 按旧红线拒绝合法改动。

**影响面：** 仅这两份 AGENTS 的上述条款；三份规格 delta 随归档同步；不影响端口双轨制、采集链路与其它模块红线。

**怎么回退：** 条款为文本替换，回退即恢复原文；代码回退即撤三端点与前端入口，表与数据不受影响（无迁移）。

## Risks / Trade-offs

- [与 add-serial-log-custom-ports 共享 views/urls/api.ts/constants/panel] → 需求面零交叉已核对；代码按功能分区追加，实施前核对其落地状态，合入前逐行 review diff。
- [超管误删关键词影响验收取词] → 删除二次确认 + 警告文案；目录刷新即时可见；历史日志文件不受影响。
- [allow-create 输入非法 SKU] → 前端白名单校验 + 后端 api 校验双层兜底，400 可读。
- [编辑改唯一键造成撞车] → api 守卫先查后改，400 可读，两行均不动。
- [操作列引入后非超管列数口径漂移] → 规格场景钉死「非超管恰四数据列」，面板测试断言。

## Migration Plan

无数据库迁移。部署 = 合入代码（后端三端点 + 前端入口），AGENTS 条款变更须先获需求方确认。回滚 = 回退代码；表结构与数据不变，读口径回到上一单状态。

## Open Questions

（无阻塞性未决项。）
