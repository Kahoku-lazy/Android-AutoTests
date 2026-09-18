## 1. 修复

- [x] 1.1 在 `tools/gen_arch_stats.py` 导入区之后加 stdout/stderr UTF-8 收敛（`hasattr` 守卫 + `errors="replace"`），并写清「为何不能靠调用方设 PYTHONIOENCODING」。验证：`python -m ruff check tools/gen_arch_stats.py` → **All checks passed!**

## 2. 验证

- [x] 2.1 重定向捕获下运行 `--check-boundaries`，输出落盘 `temps/bc_after.txt`。验证：**退出码 0**，文本含「✅ 模块边界检查通过 — 零违规」（修复前：exit 1 + `UnicodeEncodeError` traceback）
  - 注：PowerShell `>` 是「先解码再以 UTF-16LE 重写」，只能证明**退出码与文本内容**，**不能**作为「管道原始字节是 UTF-8」的证据；字节级证据见 2.6。
- [x] 2.2 直接运行（无重定向）。验证：**退出码 0**，输出「✅ …零违规」，无 `UnicodeEncodeError`
- [x] 2.3 复刻插件真实调用路径：`temps/plugin_gate.cjs` 按 `dsh-plugins/arch-gate/src/index.ts:147-154` 原样调用 `execFile("python", ["tools/gen_arch_stats.py", "--check-boundaries"], {cwd, timeout, maxBuffer, windowsHide})`，取管道 stdout/stderr 拼接后断言 `output.includes("零违规")`。验证：**ok=true、passMarker hit=true、无 Traceback** → 插件走 `return undefined`（不写提示）
- [x] 2.4 其余入口不受影响：`--check-md`（exit 0）与默认输出。验证：两者 **exit 0**，输出结构不变（`--check-md` 提示 ARCH_STATS 区域未初始化，属既有事实，与本修复无关）
- [x] 2.5 `openspec validate fix-arch-gate-encoding --strict`。验证：Valid
- [x] 2.6 原始字节捕获（不经 PowerShell 文本管线）：`Start-Process python -ArgumentList ... -RedirectStandardOutput temps/bc_raw.txt -Wait`。验证：`child_exit=0`、`out_bytes=118`、`err_bytes=0`、首 3 字节 `240,159,147`（`U+1F4DD` 的 UTF-8 序列，**非** BOM `255,254`）；`python temps/assert_marker.py` → `utf8_decode_ok=True`、`passMarker_hit=True`、`has_traceback=False`
- [x] 2.7 反事实验证（因果闭合）：`temps/nofix_gate.cjs` 用同一份源码删掉修复块、以同样的管道调用执行。验证：去修复版 **exit_code=1**、`UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f4dd'`、marker 缺失（复现插件误报）；带修复版 exit 0 + marker 命中
- [x] 2.8 根因直证：同一管道下读 `sys.stdout.encoding` = `"gbk"`；管道内 `print("📝…")` 直接抛 `UnicodeEncodeError`，而脚本 `tools/gen_arch_stats.py:1129` 正是打印 `📝 详细日志` 的一行
