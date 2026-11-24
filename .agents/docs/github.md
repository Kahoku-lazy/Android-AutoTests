## GitHub 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名一起带进去，导致已删除的包复活。
3. **PR 流程**：所有改动走 `feature 分支 → PR → 合并进 Kahoku`，禁止直推主干（`Kahoku` 分支保护强制，管理员同样生效）。外部协作者可 fork 后提 PR，无需授权；首次贡献者的 PR 需维护者在 Actions 页批准运行 CI。
4. **CI 是唯一的质量闸门**：PR 提交后必须确认 `ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 全绿，作为合并前置条件
5. **禁止强推**：`Kahoku` 是唯一主干，禁止 `--force`。已推送的提交要改，用新提交修正，不改写历史。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。不跑全量回归。
7. **网络默认直连**：不把代理写进 `~/.gitconfig`；只有直连失败或网络差时才按文末「网络与代理」临时启用。
```bash
python run.py check                # 本地门禁
git add <具体文件>                  # 逐文件暂存，不用 -A
git commit -m "feat(scope): ..."
git push origin <feature分支>       # 推特性分支，不直推 Kahoku
gh pr create --base Kahoku         # 提 PR；python / frontend 两个 CI job 全绿后方可合并
```

## 网络与代理

默认**直连** GitHub。`~/.gitconfig` 里不要常驻 `http.proxy` / `https.proxy`：代理软件没开时，这两个键会让所有 `push` / `fetch` 直接失败（报 `Failed to connect to 127.0.0.1:<端口>`），而且看起来像仓库问题。

只有出现下面情况才临时启用代理，且**只对本次命令生效**：

- 直连超时、`Failed to connect to github.com`、`Recv failure`；
- `git clone` / `git push` 多次中断。

```bash
# 先确认本机代理在监听（端口以实际软件为准，例如 Clash 的 7897）
netstat -ano | findstr :7897

# 临时给单条命令加代理，不写回任何配置文件
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin <branch>

# gh 临时走代理（可选）
$env:HTTPS_PROXY = "http://127.0.0.1:7897"; gh pr create --base Kahoku
```

用完清掉临时环境变量：`Remove-Item Env:HTTPS_PROXY`。

**不要**用 `git config --global http.proxy ...` 一次性写死——需要常驻时也应只开软件、不改配置。若发现全局配置已被写死，用下面命令恢复直连：

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```