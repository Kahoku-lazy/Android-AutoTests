## Context

见 {B}proposal.md{B}「Why」。要点：③ 的实测结论是**其余 ViewSet 已全部收敛（0 违规）**，
所以本单不产生任何生产代码改动；它把 {B}calibration.md{B} §7 的**手工** ORM 写扫描
固化为 {B}tests/arch{B} 层的可执行守卫，防止 D3 契约再次被绕过。

## Goals / Non-Goals

**Goals:**

- {B}apps/*/views*.py{B} 出现直写 ORM 调用时，{B}pytest tests/arch{B} 立刻失败并指出文件:行:调用名
- 守卫自身**可被证明能失败**（正对照测试）

**Non-Goals:**

- 不改任何生产代码（实测 0 违规）
- 不覆盖 {B}consumers*.py{B} / Tool 层（另单）
- 不覆盖经实例关系管理器写 M2M（语法不可判别）

## Decisions

### 1. 用 {B}ast{B} 而非正则

- **选择**：{B}ast.parse{B} 后只判定 {B}ast.Call{B} 的接收链。
- **理由**：正则会命中注释与字符串 —— 例如 {B}apps/device_inspector/views.py:4{B} 的注释
  「写操作全部下沉 api.py / service.py，本文件不直接 ORM。」就含 {B}ORM{B} 字样；
  将来有人写 {B}# 不要用 Model.objects.create(){B} 的注释也会误报。{B}ast{B} 天然免疫。
- **备选**：直接{清理/镜像} §7 的 {B}rg{B} 正则 —— 否决，误报会侵蚀守卫的可信度。

### 2. 两条判据，按「是否有非 ORM 同义方法」区分

- **选择**：
  1. 接收链末位是 {B}save{B} / {B}delete{B} → **无条件**判违规
  2. 接收链末位 ∈ {B}{create, bulk_create, get_or_create, update_or_create, update, add, remove, set, clear}{B}
     且链上出现 {B}objects{B} → 判违规
- **理由**：{B}save{B} / {B}delete{B} 在内建类型与常用库里没有同义方法，
  裸名接收者（{B}instance.delete(){B}、{B}serializer.save(){B}）几乎必然是 ORM ——
  这正是 ③-1 修掉的写法，必须无条件拦。
  而 {B}update{B} / {B}add{B} / {B}set{B} / {B}clear{B} 是 {B}dict{B} / {B}set{B} 的合法方法
  （{B}request.data.update(...){B}），故必须要求链上有 {B}objects{B} 才判违规。

### 3. 必须有正对照测试

- **选择**：{B}test_detector_flags_known_violations{B} 对一段内嵌片段跑同一检测器，
  断言 {B}instance.delete(){B} / {B}serializer.save(){B} / {B}X.objects.create(){B} /
  {B}X.objects.filter().delete(){B} 都被命中。
- **理由**：一条**永远不会失败**的门禁不如没有 —— 它给出虚假的安全感。
  这与 ① 的教训同源：只在「删除」侧断言而不在「仍 410」侧断言，就漏掉了那个 500。

## Risks / Trade-offs

- [误报阻塞无关改动] → 判据 2 已要求链上有 {B}objects{B}；判据 1 的 {B}save{B}/{B}delete{B} 无内建同义方法。
  若未来出现确实合理的裸 {B}.delete(){B}，应在测试中显式加白名单并写明理由，而不是放宽整体判据。
- [漏报] → 经关系管理器的 M2M 写（{B}bank.questions.add(...){B}）不覆盖；已在模块 docstring 与 tasks 中显式声明，
  该场景仍靠 {B}calibration.md{B} §7 的人工扫描兜底。
- [守卫范围漂移] → 用 {B}apps/*/views*.py{B} 通配发现模块（当前 20 个 ViewSet 全部落在此模式内），
  并额外断言「至少发现 1 个模块」，避免通配失效后守卫静默变空。

## Migration Plan

1. 新增 {B}tests/arch/test_view_write_convergence.py{B}
2. 跑 {B}pytest tests/arch{B} 确认全绿；临时插入一处 {B}instance.delete(){B} 确认守卫会失败（正对照已内置为自动测试）
3. 验证 {B}ruff check{B} · {B}ruff format --check{B} · {B}manage.py check{B}
4. 归档；回滚 = 删测试文件（{B}openspec/{B} 不入库，不靠 git 回滚）
