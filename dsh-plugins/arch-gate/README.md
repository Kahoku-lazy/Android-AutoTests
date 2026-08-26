# dsh-plugin-arch-gate

DSH 原生 hooks 插件：把原 Claude 的 check-boundary 写后边界检查职责移植为 **DSH 原生自动边界检查**。

## 功能

- 挂载 `tools/post-execute`（DSH 官方 hooks 管线，PostToolUse 同语义）
- 写入工具（`write`/`edit`）目标路径匹配 `apps/**/*.py` 时触发
- 执行 `python tools/gen_arch_stats.py --check-boundaries`
- **零违规 → 静默通过**；有违规/超时 → 输出注入 `additionalContexts`，模型下一步立即看到提醒（默认不阻塞写入；`mode: block` 可严格拦截）
- 同一 agent 默认 30s 节流，防连续写文件刷屏；每个用户回合重置

## 配置（schemastery，可在 cordis patch 层覆盖）

| 键 | 默认 | 说明 |
|---|---|---|
| `enabled` | `true` | 总开关 |
| `workspaceRoot` | `.` | 检查命令工作目录（相对进程 cwd 解析） |
| `toolNames` | `["write","edit"]` | 关注的写入工具 |
| `pathGlobs` | `["apps/**/*.py"]` | 触发路径 glob |
| `command` / `args` | `python` / `tools/gen_arch_stats.py --check-boundaries` | 检查命令 |
| `timeoutMs` | `30000` | 检查超时 |
| `throttleMs` | `30000` | 节流间隔 |
| `passMarker` | `零违规` | 输出含此标记视为通过 |
| `mode` | `inject` | `inject`=提醒注入；`block`=写入转失败 |
| `maxOutputChars` | `4000` | 注入输出截断长度 |

## 技术形态

- **TypeScript 源码**（`src/index.ts`）→ 构建为 ESM（`dist/index.js`），对齐官方插件生态惯例
- **零运行时外部依赖**：不 import `@deepseek-ai/*`（运行时包不在工作区，从工作区挂载时 bare specifier 解析不可靠），仅用 Node 内建模块；配置无 schemastery schema，默认值在 `apply()` 内合并
- 构建零网络：复用 `frontend/node_modules` 里的 tsc；Node 类型用本地最小桩（`src/node-stubs.d.ts`，工作区无 `@types/node`）

### 构建

```bash
cd dsh-plugins/arch-gate && npm run build   # 或 node ../../frontend/node_modules/typescript/bin/tsc -p tsconfig.json
```

改完 `src/*.ts` 后需重新构建（`dist/` 是挂载入口）。

## 安装（推荐：工作区挂载，零写入 $DSH_HOME）

利用 DSH 启动器的 `--patch` 覆盖层，插件代码完全留在本仓库；**所有插件共用一个聚合 patch 文件**（`dsh-plugins/patch.yml`，新增插件往里加一条即可）：

```bash
dsh web --patch dsh-plugins/patch.yml
```

验证：

```bash
dsh --profile web --patch dsh-plugins/patch.yml --dump-config
# 插件清单中应出现 arch-gate
```

> 若 patch 的 `name` 相对路径解析失败，改聚合 patch.yml 中对应条目为绝对 file URL。

备选（若 `--patch` 条目格式与当前版本不符）：`dsh plugin --profile web add file:../dsh-plugins/arch-gate`（profile 内建符号链接，代码仍在工作区，需一次性写 $DSH_HOME）。

## 设计依据

- 事件与决策形态对齐官方插件 `@deepseek-ai/dsh-repeat-tool-reminder`（`tools/post-execute` waterfall + `additionalContexts` 注入 + `agent/pre-step` 重置）
- 管线顺序：`tools/pre-execute`（拦截/审批）→ 守卫 → `tools/execute` → `tools/post-execute`（本插件）→ `finalizeContent` → `tools/result`

## 后续扩展路线（同目录新增插件）

- `doc-drift`：写 `dev_docs/**` 后跑 `gen_arch_stats.py --check-md`
- `auto-format`：写 `apps/**/*.py` 后跑 `ruff format`（先 dry-run 再提醒）
- `session-health`：`agent/session-start` 时跑 `python run.py status`
