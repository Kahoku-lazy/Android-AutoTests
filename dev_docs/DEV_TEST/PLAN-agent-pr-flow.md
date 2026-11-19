# PLAN：Agent 改代码走 PR，主干禁止直推

> 状态：**待需求方批准**（属 AGENTS.md「改规则必须先请示」的变更申请）
> 性质：方案 + 变更申请，不含任何代码/文档改动
> 依据：AGENTS.md 第 4 条硬约束（改「准入清单 / 禁止事项」须先提交变更申请）

---

## 0. 一句话结论

**能做到，而且成本很低**——因为管道已经铺好（CI 已监听 `pull_request`、PR 模板已存在、仓库是 PUBLIC 且当前账号是 ADMIN、`gh` 已登录）。真正要做的只有三件事：

1. 在 GitHub 上给 `Kahoku` 加**服务端硬锁**（这是唯一能真正拦住 Agent 直推的东西，文档只是软约束）；
2. 改 `AGENTS.md` 第 33–46 节，把「没有 PR 流程」改成「强制 PR 流程」；
3. **先把当前约 200 项未提交改动落地**，再切换——否则第一刀就会把无关改动卷进 PR。

**关键矛盾（必须先定）**：仓库目前只有一个协作者（`Kahoku-lazy`），而 GitHub 不允许自己批准自己的 PR。所以 `required_approving_review_count` **必须设 0**（"必须开 PR，但不需他人批准"），否则每一张 PR 都会永久卡死。这不是偷懒，是这个仓库唯一可行的取值——CI 才是这道闸门的实际把关者。

---

## 1. 现状盘点（本次实测，不是推断）

| 项目 | 实测结果 | 对方案的影响 |
| --- | --- | --- |
| 远端 | `github.com/Kahoku-lazy/Android-AutoTests` | GitHub 托管，可用 rulesets |
| 默认分支 | `Kahoku`（`origin/HEAD` 也指向它） | 保护目标明确 |
| 仓库可见性 | `PUBLIC` | Free 版即可用 rulesets（私有仓库 Free 不支持） |
| 当前账号权限 | `viewerPermission: ADMIN` | 能自己配保护，不用求人 |
| `gh` CLI | v2.103.3，已登录 `Kahoku-lazy`，token scopes `repo/workflow/gist/read:org` | Agent 可直接 `gh pr create` / `gh pr checks` |
| **现有分支保护** | **已存在但残缺**：`allow_force_pushes=false`、`allow_deletions=false`、`required_conversation_resolution=true`、`enforce_admins=false`；**没有** `required_pull_request_reviews`，**没有** `required_status_checks` | 直推现在**完全通得过**。这是"为什么现在能直推"的直接原因 |
| rulesets | `[]`（一个都没有） | 从零建，不会与旧规则打架 |
| CI 触发 | `push: [Kahoku]` **和** `pull_request: [Kahoku]` 都在 | PR 上会跑检查，**不用改 CI** |
| CI job | `python`、`frontend`（job id 即检查名） | 必选检查的 context 就是这两个字符串 |
| PR 模板 | `.github/pull_request_template.md` 已存在 | 但和当前门禁口径不一致（见 §6.4） |
| 提交自动化 | 全仓库 Python 无 `git push` 调用 | 没有脚本要改，直推完全来自 Agent 手工执行 |
| `allow_auto_merge` | `false` | 需决定是否开（Agent 异步等 CI 时有用） |
| `delete_branch_on_merge` | `false` | 建议开，否则分支越积越多 |
| **工作区** | **约 200 项未提交改动 + 60+ 未跟踪文件**，`Kahoku` 领先远端 1 个提交 | **硬阻塞**，见 §5 P1 |

---

## 2. 方案总览：三层防线

```
第 1 层  GitHub ruleset（硬锁，拦得住 Agent 和人类）
          └─ 直推 Kahoku → 直接被拒（remote rejected）
第 2 层  CI 必选检查（PR 上 python / frontend 全绿才能 merge）
          └─ merge 按钮变灰
第 3 层  AGENTS.md 条文（告诉 Agent 该怎么做、不许绕过）
          └─ 决定了 Agent 的默认动作与失败回退
```

**只有第 1 层是真锁**。第 3 层写进 AGENTS.md 是让 Agent 不去撞墙、并按标准动作开 PR；但如果只改文档不改保护，Agent 一次"图省事"就绕过去了。反过来，只锁服务端不改文档，Agent 会在第一次 `git push` 被拒后陷入重试或 `--force`。**两层都要，且第 1 层是决定性的。**

---

## 3. 第 1 层：GitHub 保护的具体配置

用 **Ruleset**（不用经典 branch protection），理由：可写成仓库内 JSON 文件（infra as code，可 review、可回滚）、支持试验模式 `evaluate`、有 insights 留痕。

建议落库文件 `.github/rulesets/kahoku.json`：

```jsonc
{
  "name": "protect-kahoku",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/Kahoku"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },          // 禁止删除主干
    { "type": "non_fast_forward" },  // 禁止强推 / 改写历史
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,      // 单人仓库的必然取值，见 §3.1
        "dismiss_stale_approvals": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true   // 有未解决评论不许合
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,  // 见 §3.2
        "required_status_checks": [
          { "context": "python" },
          { "context": "frontend" }
        ]
      }
    }
  ],
  "bypass_actors": []   // 无豁免，见 §3.3
}
```

落地命令（**由你在批准后执行，或授权我执行**）：

```bash
gh api -X POST repos/Kahoku-lazy/Android-AutoTests/rulesets \
  --input .github/rulesets/kahoku.json

# 顺带两项仓库设置
gh api -X PATCH repos/Kahoku-lazy/Android-AutoTests \
  -f delete_branch_on_merge=true -F allow_auto_merge=false
```

### 3.1 为什么审批数必须是 0

- GitHub 的产品限制：**作者不能批准自己的 PR**。
- 本仓库现在只有 1 个协作者（`Kahoku-lazy`）。若设 `required_approving_review_count: 1`，Agent 开的 PR 永远拿不到 approval → **每张 PR 永久卡死**，只能靠 admin 绕过合并——等于把"必须开 PR"变成纯粹的手续负担。
- 设 0 的含义是：**"必须先开 PR，但不要求他人签字"**。这正是"Agent 改代码走 PR + 主干不能直推"这个需求的原意。
- 如果将来加了第二个协作者，把这个值改成 1 即可，规则文件改一行。

> ⚠️ 若你坚持"必须有人看过才能合"，那就得**先加一个协作者/第二个账号**（哪怕只用来点 Approve），否则流程一定卡死。这是本方案唯一的硬性前置条件。

### 3.2 为什么 `strict` 设 false

`strict_required_status_checks_policy: true` 要求 PR 分支先同步到主干最新才能合。单人 + Agent 串行工作时这只会制造反复 rebase 的空转；CI 每次 push 都会在 PR 分支上重跑，与主干是否最新无关。**建议 false**；若你更看重要求"合前必先对齐主干"，改 true，代价是每次多一步 `gh pr update-branch`。

### 3.3 为什么 `bypass_actors` 留空

- 留空 = **对管理员也生效**，这才是真锁。你当前是 ADMIN，一旦留空，你自己也不能直推。
- 若给 `RepositoryRole:5`（admin）开 `always` 豁免，Agent 一旦拿到你的 token 就能直推，锁形同虚设。
- 紧急情况的正规出路不是永久豁免，而是把 ruleset 临时切到 `evaluate`（只记录不拦），事后在 Ruleset insights 里有留痕——这个过程本身有摩擦，正是它该有的样子。

> 需要你决策：**接受"自己也推不上去"吗？**（我建议接受）

---

## 4. 第 2 层：CI（几乎不用改）

- 已满足：`ci-phase1.yml` 的 `on.pull_request.branches: [Kahoku]` 会为 PR 跑 `python` + `frontend`。
- 唯一隐患：必选检查的 context 是 **job id 字符串**（`python`、`frontend`）。以后谁把 job id 改了名，PR 会**永久 pending**（报错信息还很难懂）。
- 建议在 `ci-phase1.yml` 顶部注释加一行约定，并在 AGENTS.md 写明：**"改 `jobs.python` / `jobs.frontend` 的 id 必须同步改 `.github/rulesets/kahoku.json`"**。本次不重命名 job（改名会让 context 变动、需要一次性重配）。
- 不用改门禁内容：`utils/check_gates.py` 的红线判定与 PR 流程无关。

---

## 5. 第 3 层：AGENTS.md 改法（草案，待批准后才写）

替换现有第 33–46 节（`## GitHub 版本控制与提交`），**其余章节一字不动**：

```markdown
## GitHub 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支。`Kahoku` 受 ruleset 保护，**只能经 PR 合入**；
   任何人（含管理员、含 Agent）不得直推，不得 `--force`。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 feat/fix/refactor/docs/test/chore/style/security。
   一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名带进去，导致已删除的包复活。
3. **强制 PR 流程（Agent 与人类一律适用）**：
   开分支 → 逐文件提交 → push 分支 → `gh pr create --base Kahoku`
   → 等 `python` 与 `frontend` 两个检查全绿 → squash 合并 → 删分支。
4. **CI 是唯一的质量闸门**：PR 上 `python` 与 `frontend` 必须全绿；两者是 `Kahoku` 的必选检查。
   改 `ci-phase1.yml` 里 `python` / `frontend` 的 job id，必须同步改 `.github/rulesets/kahoku.json`。
5. **禁止绕过**：禁止 `gh pr merge --admin`、禁止直推 `Kahoku`、禁止调 API 改 ruleset 或改保护状态。
   被拒绝时**不要重试、不要 `--force`**，按第 3 条走 PR。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。
7. **分支命名**：`<type>/<短描述>`，如 `feat/agent-role-kind`、`fix/login-lockout`；合并后即删。
8. **PR 描述**：按 `.github/pull_request_template.md` 填；必须写清「改了什么 / 为什么 / 怎么验证」。

```bash
python run.py check
git switch -c feat/xxx Kahoku
git add <具体文件>                  # 逐文件，不用 -A
git commit -m "feat(scope): ..."
git push -u origin feat/xxx
gh pr create --base Kahoku --fill
gh pr checks --watch               # 等 python / frontend 全绿
gh pr merge --squash --delete-branch
```
```

**同步要改的其它文档（影响面全量）**：

| 文件 | 行 | 现状 | 处理 |
| --- | --- | --- | --- |
| `AGENTS.md` | 33–46 | 「没有 PR 流程，直接推」 | 换成本节草案 |
| `README.md` | 256 | 「只在推送 `Kahoku` 和指向 `Kahoku` 的 pull request 时跑」 | 改为「PR 必过；主干由 ruleset 保护」 |
| `dev_docs/DEV_TEST/REVIEW-CI验证点与代码进度对照.md` | 150 | 「`pull_request` 触发仍在（仓库已无 PR 流程）」 | 更新为「PR 流程已启用」 |
| `.github/pull_request_template.md` | 19–20 | 自检写 `python manage.py check` / `npx vite build` | 对齐到 `python run.py check`（见 §6.4） |
| `.github/rulesets/kahoku.json` | 新增 | — | 保护规则即代码 |

`temps/_wip_backup/AGENTS.md.*.md` 是历史备份，**不动**。

---

## 6. 风险登记（每项都有对策）

| # | 风险 | 触发条件 | 对策 |
| --- | --- | --- | --- |
| R1 | **脏工作区把无关改动卷进 PR** | 现在就有 ~200 项未提交 + 60 未跟踪；直接切分支开 PR，`git add` 一抖就把别人/别的模块的活带进去 | **先落地当前改动再切流程**（§7 P1）；Agent 侧强制逐文件 `git add`（已有红线） |
| R2 | Agent 被拒后陷入重试/强推 | 第一次 `git push origin Kahoku` 被 ruleset 拒绝 | AGENTS.md 第 5 条明写「被拒不要重试、不要 force」；错误信息里能看出是保护规则 |
| R3 | Agent 用 `--admin` 绕过 merge | 有 admin 权限 | 第 5 条禁止 + `bypass_actors: []`（admin 绕过 merge 仍受 ruleset 约束：`--admin` 只能跳过 review，不能跳过 required checks） |
| R4 | 必选检查永久 pending | 改了 job id / workflow 语法错导致 job 不产出 | §4 约定 + AGENTS.md 第 4 条写死联动 |
| R5 | 单人无法自批导致 PR 卡死 | 审批数被误设 ≥1 | 规则文件写死 0，并在文件里注释原因 |
| R6 | PR 越堆越多无人合 | 流程变复杂后 Agent 开完 PR 就撒手 | 第 3 条把「合并」写进同一条流程：开 PR 的 Agent 负责追到合并 |
| R7 | 分支名冲突 / 同名残留 | `delete_branch_on_merge=false` | 开 `delete_branch_on_merge=true` + 命名带短描述 |

---

## 7. 实施顺序（批准后执行）

| 阶段 | 动作 | 产出/验收 | 谁做 |
| --- | --- | --- | --- |
| **P0** | 本方案获批（含 §8 的 5 个决策项） | 你回复"批准 + 决策取值" | 你 |
| **P1** | **清理工作区**：把当前 ~200 项改动按**现有**流程落地到 `Kahoku`（或先 stash 出一份可追溯的基线） | `git status` 干净，`Kahoku` 与远端一致 | 我（需你确认这批改动的提交切分） |
| **P2** | 走 OpenSpec：`/opsx:propose agent-pr-flow` → apply | change 目录 + AGENTS.md/README/模板/规则文件 改动 | 我 |
| **P3** | 应用 ruleset（`gh api` 两条命令） | `gh api .../rulesets` 能查到 `protect-kahoku`，`enforcement: active` | 你，或授权我 |
| **P4** | **双向验证**（缺一不可） | ① `git push origin Kahoku` 必须被拒；② 开一张真 PR，`python`+`frontend` 全绿后能 squash 合并、分支被删 | 我 |
| **P5** | 归档 change（`/opsx:archive`），PR 模板口径对齐 | openspec 主 spec 更新 | 我 |

> P1 与 P2 的顺序不可换：**必须在干净树上切流程**，否则 P4 的验证 PR 会带着一堆无关文件。

---

## 8. 变更申请（AGENTS.md 要求写清的四件事）

### 改什么
1. `AGENTS.md` 第 33–46 节：`第 3 条「没有 PR 流程」` → `强制 PR 流程`；新增「禁止绕过」「分支命名」「PR 描述」三条；`git push origin Kahoku` 示例改为 PR 五步。
2. `AGENTS.md` 第 4 条：增加「必选检查与 job id 联动」约定。
3. `AGENTS.md` 第 5 条：`禁止强推` 扩展为「任何分支禁止强推」。
4. 新增 `.github/rulesets/kahoku.json`（保护规则即代码）。
5. 同步 `README.md:256`、`REVIEW-CI验证点与代码进度对照.md:150`、`pull_request_template.md:19-20`。

### 为什么必须改
- 现有第 3 条明确写「没有 PR 流程」，与需求直接冲突；不改文档就改保护，会造成"文档说能推、服务端推不上去"的自相矛盾，Agent 必然反复撞墙。
- 现有保护**残缺**（实测：无 required reviews、无 required checks、`enforce_admins=false`），主干直推现在畅通，仅靠文档约束不住 Agent。
- 第 5 条只写了 `Kahoku` 禁强推，PR 分支上强推会悄悄改写待审内容，所以必须扩到全分支。

### 影响面
- **流程**：每次改动多 4 步（开分支 / 开 PR / 等 CI / 合并删分支）；CI 从 1 次 push 触发变为 PR + 合并各一次（`concurrency` 已有 `cancel-in-progress`，不会堆积）。
- **人工**：你从"看推送"变成"看 PR 列表"，需要定期清空。
- **历史**：合并方式改 squash 后，`Kahoku` 上每次是一个提交（历史更干净，但单 PR 内部的零碎提交不再进主干历史）。
- **不受影响**：门禁内容（`utils/check_gates.py`）、OpenSpec 流程、提交规范、依赖边界、钱与配额口径。
- **不可逆性**：无。GitHub 侧随时可停用；文档侧是普通提交。

### 怎么回退
| 层 | 回退动作 | 耗时 |
| --- | --- | --- |
| GitHub 硬锁 | `gh api -X PATCH .../rulesets/<id> -f enforcement=disabled`（或 DELETE） | 1 分钟，不用改代码 |
| 文档 | `git revert <commit>` 一个新提交（禁止 force 改写） | 1 分钟 |
| 中间态 | 把 `enforcement` 设 `evaluate`：只记录不拦，用来观察规则会不会误伤 | 即时 |

---

## 9. 需要你决策（5 项，缺一项不能开工）

1. **是否批准本变更申请**（改 AGENTS.md 第 33–46 节 + 新增 ruleset 文件）。
2. **审批人策略**：接受 `required_approving_review_count = 0`（单人仓库唯一可行、CI 当闸门）？
   —— 若你要"必须有人看过"，则需先加第二个协作者，否则流程必卡死。
3. **是否接受管理员也不可绕过**（`bypass_actors: []`，你自己也直推不了）。
4. **合并方式**：建议统一 **squash** + `delete_branch_on_merge=true`；备选 merge commit（保留分支内提交历史）。
5. **当前约 200 项未提交改动怎么处理**：先按现有流程整批落地（P1）再切流程，还是先 `stash` 出一份基线、切完流程后再以 PR 形式补交？
   —— 我倾向**前者**：这批改动已经跨了很多模块，塞进 PR 会让第一张 PR 无法 review。
