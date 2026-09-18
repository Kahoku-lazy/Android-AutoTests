## Why

`python tools/gen_arch_stats.py --check-boundaries` 在**输出被管道或重定向捕获**时**恒以退出码 1 结束**：脚本用 emoji 打印（`gen_arch_stats.py:1129` 的 📝、`:1118/:1122` 的 ✅），而 Windows 中文环境下 stdout 默认编码是 **GBK**，于是抛 `UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f4dd'`。

已实测三种情形：默认控制台 → **exit 1**；`> file 2>&1` → **exit 1**（文件里是 traceback）；`PYTHONIOENCODING=utf-8` → exit 0 且输出「零违规」。而这条命令正是 `dsh-plugins/arch-gate` 的门禁（`execFile` 管道捕获 + `passMarker: "零违规"`），所以**零违规也会被判失败**——门禁退出码不再反映「是否违规」。

## What Changes

- 在 `tools/gen_arch_stats.py` 的导入区之后增加一处 stdout/stderr 编码收敛：`reconfigure(encoding="utf-8", errors="replace")`，并用 `hasattr` 守卫（被 pytest/自定义对象捕获时静默跳过）。
- **不动**任何扫描规则、违规判定、退出码语义与输出文案；只改输出编码。
- **BREAKING**：无。
- 不动的部分：`_setup_boundary_logger`（`:986` 已 `encoding="utf-8"`，日志侧本就无问题——早先看到的乱码是 PowerShell `Get-Content` 以 GBK 解读 UTF-8 文件所致）；`arch-gate` 插件的 `passMarker` 也无需改。

## 关联文档

- 检测依据：本会话 D0 层检测「P1 · 门禁假失败」
- `dsh-plugins/arch-gate/src/index.ts:75-78`（调用点 + `passMarker: "零违规"` + `maxOutputChars: 4000`）
- `apps/AGENTS.md` §3 关单清单（`gen_arch_stats.py --check-boundaries`）
- `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §A.6「工具校验结论」
- 说明：`dev_docs/文档编号对照表.md` 不存在

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；工具链编码修复，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **修改**：`tools/gen_arch_stats.py`（+6 行，导入区之后）
- **效果**：`--check-boundaries` / `--check-md` / 默认输出在**被捕获**环境下由「exit 1 + traceback」变为「exit 0 + 正常 UTF-8 输出」；`arch-gate` 门禁恢复可信
- **不影响**：扫描规则、违规判定、`tools/boundary-whitelist.json`、`logs/boundary-check.log` 的内容与格式
- **测试范围**：`python -m ruff check tools/gen_arch_stats.py` + 三种输出环境实测 + 门禁命令复跑
