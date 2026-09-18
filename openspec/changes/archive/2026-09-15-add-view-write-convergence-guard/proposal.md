## Why

**③-2/③-3 的实测结论：其余 ViewSet 早已收敛，无事可做；但「D3 写库只经 api.py」这条契约没有永久门禁。**

上一单（{B}converge-element-locator-drf-writes{B}）的续做清单写着
「其余 App 的 ViewSet 隐式写（{B}case_manager{B} 4 · {B}evaluator{B} 3 · {B}ai_assistant/views_drf{B} 1）」。
本次按「不推测逻辑，不假设问题」逐文件实测，证明**该清单是错的** —— 它是按「哪些 ViewSet 没覆写 {B}perform_*{B}」推出来的，
而没有验证这些 ViewSet 是否真的写库：

| 文件 | ViewSet 基类 | 写方法 | 结论 |
|---|---|---|---|
| {B}element_locator/views_projects_drf.py{B} | {B}viewsets.ViewSet{B} ×2 | 显式调 {B}el_api.create/update/delete_directory{B}；项目写方法直接 {B}raise MethodNotAllowed{B} | 已收敛 |
| {B}case_manager/views_drf.py{B} | {B}viewsets.ViewSet{B} ×4 | 显式调 {B}case_api.create/update/delete_*{B} | 已收敛 |
| {B}workflow/views_api.py{B} | {B}ModelViewSet{B} ×2 | 6 个 {B}perform_*{B} 全调 {B}wf_api.*{B} | 已收敛 |
| {B}ai_assistant/views_drf.py{B} | {B}GenericViewSet{B} | 无 mixin，自定义 {B}@action{B} 调 {B}api.*{B} | 已收敛 |
| {B}element_locator/views_drf.py{B} | {B}ModelViewSet{B} ×6 | 8 个 {B}perform_*{B}（② 已改造） | 已收敛 |
| {B}evaluator/views_api.py{B} | {B}ModelViewSet{B} ×3 | ③-1 已收敛 | 已收敛 |

实测（全仓 {B}apps/**/views*.py{B}，AST 精确到调用）：
- 直写模式 {B}.objects.(create|bulk_create|get_or_create|update_or_create|update|delete|add|remove|set|clear){B}
  / {B}.save({B} / {B}.delete({B} → **0 命中**
- 正对照：同一 AST 检测器对 {B}apps/evaluator/api.py{B} 命中 14 处（正则口径）→ 检测器有效
- {B}viewsets.*{B} 定义共 20 个，**全部**落在 {B}views*.py{B} 文件内（无游离在其它模块名的 ViewSet）

**缺口**：{B}tools/gen_arch_stats.py --check-boundaries{B} 只覆盖**防火墙 #2（跨模块 ORM 写）**，
不覆盖「View 写本 App 自己的模型」。{B}calibration.md{B} §7 把这条列为**手工** {B}rg{B} 扫描 ——
手工扫描不会在 CI/关单时自动拦人，下一次 {B}serializer.save(){B} / {B}instance.delete(){B} 仍会悄悄溜进来（
③-1 修掉的那个 {B}instance.delete(){B} 就是这么攒出来的）。

## What Changes

- 新增 {B}tests/arch/test_view_write_convergence.py{B}：把 §7 的手工扫描固化为 {B}arch{B} 层守卫
  - 用 {B}ast{B} 而非正则：只匹配**调用**，不误命中注释与字符串
  - 逐模块参数化断言 {B}apps/*/views*.py{B} 无直写；**含一条正对照测试**，保证守卫本身能失败
  - 模块 docstring 显式声明**未覆盖**「经实例关系管理器写 M2M」（{B}bank.questions.add(...){B}）——语法上与集合操作不可区分
- 不改任何生产代码（实测已是 0 违规，无代码可改）

- **BREAKING**：无
- 按 schema 约定设 {B}skip_specs: true{B}（不改行为，只加门禁）

## 关联文档

- 契约：{B}apps/AGENTS.md{B} §1.2「View / Consumer / Tool 直接 ORM 写」禁止项 · {B}D3 写库只经 api.py{B}
- 口径：{B}.agents/skills/django-backend-check/references/calibration.md{B} §7（手工扫描命令）
- 前置变更：{B}converge-evaluator-drf-writes{B}（③-1）· {B}converge-element-locator-drf-writes{B}（②）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 测试：新增 {B}tests/arch/test_view_write_convergence.py{B}（约 90 行）
- 不改生产代码、不改契约文档
- 验证：新测试 · {B}pytest tests/arch -q{B} · {B}ruff{B} · {B}manage.py check{B}
- 不在本单范围：{B}consumers*.py{B} / Tool 层的同类守卫（本单只覆盖 view 层）·
  经关系管理器写 M2M 的检测（AST 不可判别）
