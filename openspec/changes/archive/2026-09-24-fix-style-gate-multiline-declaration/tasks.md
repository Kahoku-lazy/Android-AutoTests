## 1. 修复声明扫描器

- [x] 1.1 `frontend/tests/check-style-gates.mjs` 的 `scanDeclarations`：匹配前把跨行声明折叠为一条逻辑行（断点：`;` / `{` / `}` / 注释收尾 `*/`），行号仍取声明起始行的块内偏移，原有正则与前缀规则不变。验证：`git diff --stat` 只动一个文件（+22 / −6）
- [x] 1.2 计数守恒：修复前后批 2 输出对比——声明 339 → 340（只多 `--font-body`）、颜色原子 98 → 98、复合值登记 3 → 3。验证：两次 `npm run lint:styles` 输出逐项比对
- [x] 1.3 门禁转绿：`cd frontend && npm run lint:styles` 退出码 0，批 1 / 批 1b / 批 2 / 批 3 / 批 4 全部出现并通过（批 3：载体 4031 处 0 违规；批 4：几何尺度全通过）。验证：命令输出 + 退出码 0
- [x] 1.4 判定规则零变更：改动全部落在 `scanDeclarations` 内，未动阈值 / 白名单 / 判定分支。验证：`git diff` 逐行核对；另确认批 4 走的是自己的逐行扫描（不消费 `scanDeclarations`），故不受影响

## 2. 影响面确认

- [x] 2.1 消费点检查：`scanDeclarations` 仅两处消费（批 2 的 T0 判定、批 3 的声明落点），批 3 依赖的块内相对行号语义未变；`lint:styles` 仅 `frontend/package.json` 定义、未接入 `tools/check_gates.py` 与 `.github/workflows/ci-phase1.yml`。验证：全仓 grep 引用点
- [x] 2.2 平台代码未触碰：本单只改门禁脚本，未动 `tokens.css` 与 `frontend/src/**`。验证：`git status --short`——`frontend/src/modules/element-locator/**` 的改动属于同时在飞的 `relayout-locator-workspace` 变更，与本单无关
