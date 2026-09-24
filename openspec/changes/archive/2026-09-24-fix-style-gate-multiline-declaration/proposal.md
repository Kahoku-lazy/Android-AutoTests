## Why

`cd frontend && npm run lint:styles` 在干净工作树上**本来就是红的**：报 2 处 `G4 引用了未声明的令牌 --font-body → 静默回退风险`。而 `--font-body` 明明声明在 `tokens.css` 第 165 行。

根因在门禁脚本的声明扫描器：它**按物理行**匹配 `--name: value`，而 `--font-body` 的值（字体族栈）是跨行书写的——

```css
--font-body:
  "Cascadia Mono", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", monospace, sans-serif;
```

于是 `--font-body` 从未进入 `declared` 集合，它的两个消费点（`--app-font` / `--app-font-display`）被判成"引用了未声明的令牌"。更糟的是：批 2 判定失败会**提前退出**，批 3（载体边界）与批 4（几何尺度）根本没机会跑——门禁名义上五批，实际长期只跑前三批。

## What Changes

- `frontend/tests/check-style-gates.mjs` 的 `scanDeclarations`：匹配前先把**跨行声明折叠成一条逻辑行**，并把注释收尾（`*/`）也当作断开点。
- 行号语义不变：仍返回声明**起始**行的块内行号，批 3 的 `b.startLine + d.line - 1` 映射不受影响。
- **不改任何判定规则、阈值、白名单**：G1–G14、批 1 字号下限、存量清单口径全部原样。
- **不改 `tokens.css`**：把声明压成单行本来也能绕过这个问题，但该行 104 字符超过 prettier 的 `printWidth: 100`，会被 prettier 打回多行——修扫描器才是正解。
- **非目标**：不把 `lint:styles` 接进 `python run.py check` 或 CI（那是另一个决策，本单不扩面）；不动批 3 / 批 4 的读法。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）—— 只修门禁实现的解析缺陷，不改任何验收标准。

## Impact

- 代码：`frontend/tests/check-style-gates.mjs`（+22 / −6，仅 `scanDeclarations` 一个函数）。
- 行为：声明计数 339 → 340（只多出 `--font-body` 一条，无漏登记）；颜色原子 98、复合值登记 3 均不变；`npm run lint:styles` 退出码由 1 → 0。
- 连带：批 3 / 批 4 首次真正跑完（4031 处载体 0 违规、几何尺度全通过）。
- 平台运行时代码：零改动；令牌值：零改动。
- 在飞的 `relayout-locator-workspace` 变更把 `npm run lint:styles` 写进了验证步骤，本单解除它的假红。
