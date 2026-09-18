## Context

注释里的「24」是历史值，图标持续增加后未同步。触发点是复核「SVG 相关文件在哪里」时实测导出数与注释不符（见 `fix-icon-count-comment` 的 What Changes）。

## Decisions

### D1 · 只改计数值，不改同段其它描述

复核结论：同段「覆盖场景」「`defineComponent` + `h()` 渲染函数」两句与实现一致，故只改数字，避免顺手动其它文字（`frontend/AGENTS.md` 行为规范 3「只碰必须碰的」）。

### D2 · 计数口径

计数方法：全文匹配 `export const (Icon[A-Za-z0-9]+)`，得 45 个唯一导出；与模板中 `makeIcon(` 的调用数一致。不把 `shared/icons/lucide-registry.ts` 的 14 个 lucide 名字计入 —— 那是运行时子集（经 `window.lucide` 渲染），不是本文件的自绘图标。

## Risks / Trade-offs

- 无可观测风险：注释不参与编译、不进入产物；无引用方依赖该文字。

## Migration Plan

1. 改注释数字
2. 复核计数与注释一致
3. 归档（`skip_specs: true`）
