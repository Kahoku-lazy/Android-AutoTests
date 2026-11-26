# 全仓去注释复盘（2026-11-24）

> **触发**：把全仓产品代码（backend / engines / tests / utils / frontend + 根脚本）的注释与 docstring 一次删干净。
> **产物**：分支 `chore/strip-code-comments`、提交 `ab494da8`、PR #63（805 文件，+927 / −16778）。
> **用途**：记录这次任务的耗时构成、走过的弯路与可复用做法，供后续「大范围机械改造」参考。
> **口径**：时间为工具执行耗时（约 50 分 48 秒），下表按会话内时间戳回推，**均为估算**，不是埋点数据。

## 1. 结论

约一半时间花在任务本身与 Windows 环境的硬成本上；另一半是两次可以避免的绕路：**逐文件起进程做格式化**与**把首个提交建在过期基线上**。

## 2. 时间账（估算）

| 阶段 | 耗时 | 性质 |
| --- | --- | --- |
| 环境 / 权限排障，等会话切「完全权限」（含 3 轮确认提问） | ~15 min | 环境 + 人工等待 |
| 第一轮剥离 + 格式化（含一个跑 18 分钟后被终止的任务） | ~20 min | 一半必要、一半绕路 |
| 修 `node_modules`（`npm ci` 失败两次、停 vite 进程、重装） | ~8 min | 环境 |
| 首轮门禁 + OpenAPI 基线重生成 + 提交 + 提 PR | ~6 min | 必要 |
| rebase 撞 170 个冲突 → 放弃 → 重置 → 第二轮全流程 | ~15 min | 判断失误的代价 |
| AST 语义校验脚本（跑两次，逐文件 `git show`） | ~5 min | 必要但实现笨 |
| 其他（250+ 次工具调用，每次 shell 冷启动约 2s） | ~8 min | 硬性开销 |

## 3. 三次真正的浪费

### 3.1 逐文件起 `ruff` 子进程做格式化（约 18 分钟，被终止）

- **现象**：`ruff format` 直接写文件报 `EPERM`（会话前半段 shell 跑在 Windows 低完整性令牌下），于是改成「每个文件起一次 ruff、stdout 回写」。
- **代价**：550 个文件 × 每次约 2s 进程启动 ≈ 18 分钟，发现不对时已跑掉 12 分钟。
- **正确做法**：只对 `ruff format --check` 报出来的文件（本次是 11 个）逐个走 stdin，不要全量。

### 3.2 首个提交建在过期基线（约 15 分钟白干）

- **现象**：从 `Kahoku` 切分支时它是 `3f9565bd`；做完后主干已推进到 `e0e1a0fb`（#62 合入依赖清理）。rebase 时撞出 170 个冲突，只能放弃、重置、把剥离 + 格式化 + 规范改动 + 门禁全部重跑。
- **正确做法**：动手前 `git fetch` 确认基线；或先 rebase 到最新主干再开始改。

### 3.3 用 `git show` 逐文件做 AST 校验

- **现象**：478 个改动文件、每个文件起一次 `git show` 子进程，单次 3–5 分钟。
- **正确做法**：`git cat-file --batch` 一次喂进去，能压到十几秒。

## 4. 环境性硬成本（换人做也省不掉）

1. **低完整性令牌**：`backend/apps`、`.git/refs/heads/*`、`openspec/changes/archive` 下新建目录一律拒写，`git reset` / `commit` / 切分支全部失败，还留下一次「切分支切到一半」的中间态，需要先恢复现场。
2. **杀毒 / 文件锁**：`ruff`、`prettier`、`python` 写入随机报 `EPERM`，同一批文件要重试 2–4 轮才落地（`ruff format` 重试了 5 次）。
3. **dev server 占用 `esbuild.exe`**：`npm ci` 删不掉它，必须先停掉 `vite --host` 进程才能装依赖。
4. **门禁本身耗时**：`python run.py check` 每次 3–4 分钟（vitest ~30s + vite build ~20s + django / openapi / vue-tsc），本次跑了 3 次。
5. **本地两条门禁假失败**：`vitest` / `vite-build` 经 Python 子进程调用时，node 写 `node_modules/.vite-temp`、`frontend/dist` 报 `EPERM`；直接 `npm test` / `npm run build` 与 CI（Ubuntu）均通过。判断「是不是自己改坏了」时以直跑与 CI 为准。

## 5. 下次怎么做（清单）

- [ ] 动手前 `git fetch` + `git log --oneline HEAD..origin/Kahoku`，确认基线；PR 前再 rebase 一次。
- [ ] 这类一次改 800 个文件的任务，**先确认会话是「完全权限」**再开工。
- [ ] 格式化只处理 `--check` 报出来的文件，不全量起子进程。
- [ ] 批量读 git 历史用 `git cat-file --batch`，不要每文件一次。
- [ ] 机械改造的正确性用「逐文件 AST 对比」兜底，不要靠人眼过 800 个 diff。
- [ ] 先跑一次门禁摸底，再改；改完只重跑受影响的门禁，最后再全量。

## 6. 本次机械改造的实现要点（脚本未入库）

临时脚本都放在 `temps/`（按仓库规则不入库），复用时按下面要点重写即可：

1. **Python**：`ast` 定位 docstring（`Module` / `ClassDef` / `FunctionDef` 的 `body[0]` 是字符串常量），`tokenize` 定位 `#` 注释；先删注释再删 docstring；整行删除，函数体只剩 docstring 时替换为 `pass`。
2. **保留白名单**：`# noqa`、`# type: ignore`、`# pragma`、`# fmt:`、shebang、编码声明；`silent-except` 门禁要求的痕迹统一写 `# silent-except`。
3. **语义校验**：把 HEAD 版本 AST「去掉 docstring」后与改后 AST 做 `ast.dump` 全量对比，不一致就跳过该文件并报人工处理。
4. **前端**：`@babel/parser` 的 `comments` 取精确区间（正确处理正则 / 模板字符串），`.vue` 用 `@vue/compiler-sfc` 拿 block 偏移分别处理 script / style / template。
5. **格式化**：Python 走 `ruff format`，前端走 `prettier --write`；删注释后会残留空行，用「去文件头空行 + 去 class/def 头后空行」的规范化补齐，再交给 formatter 收尾。

## 7. 关联

- 规范：`.agents/rules/python-docstring-style.md`、`.agents/rules/engines-code-style.md` §2
- 门禁：`utils/check_gates.py`（`silent-except` 识别 `# silent-except` 标记；`python-module-docstring` 已下线）
- 提交：`git show ab494da8 --stat`
