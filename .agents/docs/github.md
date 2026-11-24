## GitHub 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名一起带进去，导致已删除的包复活。
3. **PR 流程**：所有改动走 `feature 分支 → PR → 合并进 Kahoku`，禁止直推主干（`Kahoku` 分支保护强制，管理员同样生效）。外部协作者可 fork 后提 PR，无需授权；首次贡献者的 PR 需维护者在 Actions 页批准运行 CI。
4. **CI 是唯一的质量闸门**：PR 提交后必须确认 `ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 全绿，作为合并前置条件
5. **禁止强推**：`Kahoku` 是唯一主干，禁止 `--force`。已推送的提交要改，用新提交修正，不改写历史。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。不跑全量回归。
```bash
python run.py check                # 本地门禁
git add <具体文件>                  # 逐文件暂存，不用 -A
git commit -m "feat(scope): ..."
git push origin <feature分支>       # 推特性分支，不直推 Kahoku
gh pr create --base Kahoku         # 提 PR；python / frontend 两个 CI job 全绿后方可合并
```