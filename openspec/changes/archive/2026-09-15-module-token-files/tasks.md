## 1. 模块令牌文件化

- [x] 1.1 从 `shared/styles/tokens.css` 迁出 `.ai-workbench`(42 条) 与 `.case-workbench`(2 条)，生成 `modules/ai-assistant/tokens.css` / `modules/case-manager/tokens.css`；验证：`--ai-*` / `--case-*` 在共享层残留 = 0
- [x] 1.2 从 `shared/styles/workbench-theme.css` 迁出 30 条 `--ac-*` 至 `modules/workflow/tokens.css`，选择器保持 `.workflow-workbench`；验证：workbench-theme 内 `--ac-*` 残留 = 0
- [x] 1.3 `main.ts` 追加 3 条模块令牌 import；验证：`main_imports=3`

## 2. 值引用主 token

- [x] 2.1 模块/组件级 85 处字面量色值 → `var(--color-*)`（33 个文件）；验证：脚本值等价校验 `value_mismatch=0`
- [x] 2.2 模块令牌文件内 10 处 `--ac-*` 字面量 → `var(--color-*)`；验证：三份 T1 文件 `literals=0`

## 3. 门禁与回归

- [x] 3.1 `npm run lint:styles` 通过（批 2：颜色原子唯一 / 非原子无纯色字面量 / 引用完整）；验证：exit 0
- [x] 3.2 裸值复核与类型检查；验证：`hex_bare=0` · `rgba_bare=0` · `TOTAL_ERRORS=34`（全在 tests/）· `APP_CODE_ERRORS=0`（与基线一致）

## 4. 关单

- [x] 4.1 `openspec validate module-token-files --strict` 通过并归档

## 关单记录（2026-09-15）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 值等价（零视觉变化） | `node temps/migrate-t1.mjs` | `value_mismatch=0`（旧值 vs 新值按规范化色比较） |
| T1 字面量 | 三份模块令牌文件 | ai 42 条 / case 2 条 / workflow 30 条，**字面量均为 0** |
| 共享层残留 | 扫描 `shared/styles/tokens.css` | `--ai-*`=0 · `--case-*`=0 |
| 门禁 | `cd frontend && npm run lint:styles` | exit 0（T0 声明 394 条 · 颜色原子 198 · 存量别名 48） |
| 裸值 / 类型 | `temps/verify-colors.ps1` | `hex_bare=0` · `rgba_bare=0` · `TOTAL_ERRORS=34` · `APP_CODE_ERRORS=0` |
| 构建 | `npm run build` | **未执行**：沙箱 `spawn EPERM`；浏览器核验仍未做 |