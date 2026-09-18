## 1. 对拍守护

- [x] 1.1 新增 `tests/graybox/unit/test_auth_validation_parity.py`：提取前端 `useLoginForm.ts` 的
      `errs.<字段> = '文案'` 与后端 `serializers.py` 的 `ValidationError("文案")`，断言两侧差异**恰好等于**
      已声明且带理由的例外集合；再提取两侧的长度判断 `(比较符, 数值)` 集合，断言集合相等。
  **验证**：`python -m pytest tests/graybox/unit/test_auth_validation_parity.py -v` 全绿
  （两侧当前一致，不应有失败）。
- [x] 1.2 证明守护确实会失败：临时把 `useLoginForm.ts` 的一条文案改一个字（例如「请输入用户名」→「请输入用户名！」），
      确认守护失败并同时列出两侧差异，随后**还原**。
  **验证**：改动期间 `python -m pytest tests/graybox/unit/test_auth_validation_parity.py -q` 失败且错误信息含该条差异；
      还原后 `git diff -- frontend/src/shared/composables/useLoginForm.ts` 为空。

## 2. 文档同步

- [x] 2.1 更新 `tests/AGENTS.md` §契约对拍测试：断言条数由两条改为三条，补上
      `auth-form-validation`（表单校验文案与阈值两侧一致），并把新模块名加入文件列表。
  **验证**：该节列出的文件名与能力路径与实现一致（文件存在、能力路径存在于 `openspec/specs/`）。

## 3. 门禁

- [x] 3.1 单元与架构测试全绿。
  **验证**：`python -m pytest tests/graybox/unit tests/arch -q`（基线 321 passed，+本变更的新用例）。
- [x] 3.2 新增测试文件静态检查通过。
  **验证**：`python -m ruff check tests/graybox/unit/test_auth_validation_parity.py` 与
      `python -m ruff format --check` 对该文件均无输出。
- [x] 3.3 架构红线零违规。
  **验证**：`python tools/gen_arch_stats.py --check-boundaries`（基线零违规）。
