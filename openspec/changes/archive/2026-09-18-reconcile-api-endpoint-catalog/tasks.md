## 1. 目录对账

- [x] 1.1 用括号配对解析（支持跨行）列出全部条目与失效项，据此执行对账：
      `/api/ai/auth/*` ×5 改名到 `/api/auth/*`；1 条重复项（`/api/ai/health/`）与 55 条无对应物的条目删除；
      删空的分组/目录一并移除。
  **验证**：`python temps/parse_catalog_entries.py` 输出「失效（resolve 不到）: 0」且条目数为 131。
- [x] 1.2 复核改动范围。
  **验证**：`git diff --stat -- tools/seed_api_endpoints.py` 只有删除与 5 处 URL 字符串变更；
      `python -m ruff check tools/seed_api_endpoints.py` 无输出。

## 2. 守护升级

- [x] 2.1 `tests/graybox/unit/test_api_path_callers.py`：端点资产目录纳入 resolve 断言
      （移除 `RESOLVABLE` 例外），目录规模下限按实测调整，docstring 去掉"只断言写法"的说明。
  **验证**：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 全绿（7 passed）。
- [x] 2.2 注入假路径证明守护会失败：临时把目录中某条目的 URL 改成一个不存在的路径，确认守护失败并列出该条目，随后还原。
  **验证**：注入期间 `test_every_caller_path_resolves_to_a_view` 失败且错误信息含该路径；
      还原后 `git diff` 不含该临时改动。

## 3. 文档同步

- [x] 3.1 更新 `tests/AGENTS.md` §契约对拍测试：去掉"端点资产目录只断言尾斜杠"的说明，
      改为"四个面全部参与 resolve 断言"。
  **验证**：该节内容与守护实现一致（无"只断言写法"字样）。

## 4. 门禁

- [x] 4.1 单元与架构测试全绿。
  **验证**：`python -m pytest tests/graybox/unit tests/arch -q`（基线 330 passed）。
- [x] 4.2 静态检查通过。
  **验证**：`python -m ruff check tools/seed_api_endpoints.py tests/graybox/unit/test_api_path_callers.py`
      与 `python -m ruff format --check` 对两者均无输出。
- [x] 4.3 架构红线零违规。
  **验证**：`python tools/gen_arch_stats.py --check-boundaries`（基线零违规）。
