## 1. 配置关停

- [x] 1.1 在 feature 分支删除 `.github/dependabot.yml`（整文件删除，不留空壳；依据 `design.md` D2）；验证：`git status` 只多出这一条删除 + 两份文档改动，`python -m run check` 的 Python 侧阻塞项全绿（前端 `vitest` / `vite-build` / `bundle-budget` 三项在本机沙箱内因 esbuild `spawn EPERM` 无法执行，属环境限制，改由 CI 判定）
- [x] 1.2 复核安全开关未被连带影响：`gh api repos/Kahoku-lazy/Android-AutoTests/automated-security-fixes` 仍返回 `{"enabled": true, "paused": false}`，`gh api repos/Kahoku-lazy/Android-AutoTests/vulnerability-alerts` 仍返回 204

## 2. 文档口径同步

- [x] 2.1 改 `SECURITY.md` 的「第三方依赖漏洞」条目：区分「安全更新仍由 Dependabot security updates 自动开 PR」与「定期版本升级已停用、依赖巡检改为人工按需发起」，并写入恢复方法（从 git 历史取回 `dependabot.yml`）；验证：`git diff` 确认两件事都写到，无残留「Dependabot 会跟踪本仓库依赖更新」的单一表述
- [x] 2.2 在 `CHANGELOG.md` 的 `Unreleased → Changed` 下补一条记录本次策略变更并指向 `openspec/changes/retire-dependabot-version-updates/`；验证：条目格式与同节既有条目一致
- [x] 2.3 全仓搜一遍旧口径：`Dependabot` 的命中项只剩 `SECURITY.md`、`CHANGELOG.md` 与 `openspec/**` 的新表述；验证：无其他文件仍在承诺「自动跟踪依赖更新」

## 3. 存量挂单收尾

- [x] 3.1 关闭当前 10 个打开的定期升级 PR（#78–#87），统一附言「版本升级策略已停用，见 SECURITY.md」，不合并不改动其分支；更早的 11 个同类 PR 实测已处于 closed 状态，无需处理。验证：`gh pr list --state open` 返回 0 条

## 4. 交付

- [ ] 4.1 提 PR 到 `Kahoku`（`gh pr create --base Kahoku`），确认 `python` 与 `frontend` 两个 CI job 全绿（合并由维护者执行）；验证：`gh pr checks <PR号>` 两项均 success

## 5. 合并后验证（本次会话不勾选，留给合并后的维护者）

- [ ] 5.1 合并后确认远端 `.github/dependabot.yml` 已不存在（`gh api repos/Kahoku-lazy/Android-AutoTests/contents/.github/dependabot.yml` 返回 404），且 Security → Dependabot 页无「配置无效」提示
- [ ] 5.2 观察一个扫描周期（下一个周一）：确认未产生新的定期版本升级 PR；若出现安全更新 PR，记为预期行为而非回退信号
