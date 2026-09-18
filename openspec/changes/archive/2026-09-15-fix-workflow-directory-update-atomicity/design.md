## Context

动机见 `proposal.md` - Why。现场由「非原子双写」订正为「契约未兑现 + 参数被静默丢弃 + 越权写」：`WorkflowDirectorySerializer.parent_id` 只读，使 `perform_update` 的移动分支不可达，而 `name`/`sort_order` 仍由 `serializer.save()` 直写库。

修法有两个关键点：① 让 `parent_id` 按文档契约**可写**（否则「移到根 / 换父」永远无法生效）；② 把 `sort_order` 纳入 api 能力面（否则视图没有合法途径只经 api 完成更新）。

## Goals / Non-Goals

**Goals:**

- 兑现 `API-工作流.md` §3.4 的 `parent_id` 契约（int/null，null = 移到根），且与 legacy 路径行为一致
- 一次更新只有一条写路径（`wf_api.update_directory`）
- 校验失败时**零写库**（不再有部分更新）
- 补齐 api 对 `sort_order` 的支持，让视图不必绕过白名单

**Non-Goals:**

- 不改 legacy 平铺路径（`views.directory_detail` / `directory_move`）—— 它们本就直调 api、单写路径，本单只动 router 路径
- 不改 `update_directory` 的错误文案与返回结构（前端 `formatApiError` 依赖 `message`）
- 不改 `WorkflowDirectory` 模型或迁移（唯一约束已存在，api 侧已有 `IntegrityError` → `同级目录名冲突`）

## Decisions

### 1. 扩展 api 能力，而不是在视图里加事务

- **选择**：`update_directory` 增 `sort_order`，视图只调它
- **理由**：加 `transaction.atomic` 只解决原子性，写库仍然越过 api 白名单（D3 契约违规）；补 api 能力同时修好两层根因

### 2. 让 `parent_id` 可写（`IntegerField`，不用 `PrimaryKeyRelatedField`）

- **选择**：`serializers.IntegerField(allow_null=True, required=False)`
- **理由**：文档 §3.4 把 `parent_id` 定义为 int/null 的**裸 ID**，存在性/跨原型/成环判定属业务规则，归 `api.py`（`update_directory` / `move_directory`）。若改用 `PrimaryKeyRelatedField`，`validated_data` 会拿到关联对象、并把存在性校验前移到 DRF，产生与 api 重复且文案技术化的错误

### 3. 保留「显式 null = 移到根」

- **选择**：视图把 `parent_id: null` 翻译成 `""` 传给 api（api 内 `parent_id == ""` 即置 `d.parent = None`）
- **理由**：文档 §3.4 明写「传 `null` 移到根」；`libraryStore.ts` 的 `parent_id: number | null` 也说明 null 是合法取值。直接丢弃 null 等于继续静默违约

### 4. 回归测试覆盖「失败不留痕」与「成功全字段落库」

- **选择**：三条用例，用真实 HTTP 路径（`Client().patch` + JWT 头）而非直接调视图
- **理由**：该缺陷的表现层是响应码与库内数据不一致，只有走 HTTP 才能同时断言两者；且顺带覆盖中间件 + DRF 鉴权链路

## 模块防火墙自检

- 跨 App import：不涉及（改动限于 workflow 内）
- 写库收敛：✅ 修复后视图不再直接写库；写仍只在 `apps/workflow/api.py`（含 `api_digest.py`）
- 引擎/通道边界：不涉及

## Risks / Trade-offs

- [契约接通后新增可达错误] → `不能跨原型移动目录` 由不可达变为可达，同步补进 `API-工作流.md` §3.4 错误码表
- [DRF 校验与 api 校验重复] → 序列化器管字段类型，api 管业务规则（跨原型/同级重名），职责不变
- [PUT（partial=False）语义] → `name` 仍由序列化器判必填，`parent_id` 缺省即不动父级，与文档一致

## Migration Plan

1. 扩 `update_directory(dir_id, name, parent_id, sort_order)`
2. `serializers.WorkflowDirectorySerializer.parent_id` 改为可写 `IntegerField`
3. 重写 `perform_update` 为单一 api 调用
4. 新增回归测试并跑；`makemigrations --check` 必须仍绿
5. 归档；回滚 = `git checkout` 三个源文件 + 删测试
