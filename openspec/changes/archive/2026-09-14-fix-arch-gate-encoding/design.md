## Context

- 崩溃点：`:1129` `print(f"📝 详细日志: {log_path}")` 与 `:1131-1132` 逐行 `print(line)`（`out` 中含 ✅/🔴）。
- 触发条件：stdout 非 UTF-8（Windows 中文默认 GBK）；**交互控制台与重定向都会触发**（实测均已复现）。
- `_setup_boundary_logger` 第 986 行已带 `encoding="utf-8"` → 日志侧无编码问题。

## Goals / Non-Goals

**Goals:**

- 让该脚本的退出码只反映「是否发现违规」，不再因输出编码而以 1 结束。

**Non-Goals:**

- 不改扫描规则、白名单、输出文案与退出码语义。
- 不改 `arch-gate` 插件配置。
- 不引入新的环境变量依赖（不要求调用方设 `PYTHONIOENCODING`）。

## Decisions

**D1 在脚本内收敛 stdout/stderr 编码，而不是要求调用方设 `PYTHONIOENCODING`。**
备选：(a) 由 CI/插件设 `PYTHONIOENCODING=utf-8` —— 只修一条调用链，手动执行与其它消费者仍崩，且全仓实测无任何该声明；(b) 删掉全部 emoji —— 需改多处并丢失既有输出约定。
理由：单点修复覆盖所有输出路径；`errors="replace"` 对未来不可编码字符兜底，使其退化为可见的替换字符而非崩溃。

**D2 `hasattr(stream, "reconfigure")` 守卫。**
理由：输出被捕获时 stdout 可能是非 `TextIOWrapper` 对象（pytest 捕获等），无 `reconfigure` 时应静默跳过，避免修复本身引入新崩溃。

**D3 不动 `_setup_boundary_logger`。**
理由：已 UTF-8（`:986`），日志侧无需改动。

## 模块防火墙自检

纯工具脚本改动，不涉及应用分层：

- **跨 App import**：无（脚本只 import 标准库）。
- **写库 / api.py**：不涉及。
- **前端不直连数据库**：不涉及。
- **结论**：无新依赖。

## Risks / Trade-offs

- [强制 UTF-8 后，代码页非 UTF-8 的老终端里 emoji 可能显示为替换字符] → 这是 `errors="replace"` 的既定取舍，优于「崩溃 + 退出码 1」；门禁消费者（Node `execFile` 默认按 UTF-8 解码）不受影响。
- [pytest 捕获下 stdout 无 `reconfigure`] → D2 守卫跳过，不影响测试输出。
- [只修了这一个脚本] → 同目录其它工具若有同类 emoji 打印仍可能崩，但都不在门禁路径上；本次按「只碰必须碰的」不扩散。
