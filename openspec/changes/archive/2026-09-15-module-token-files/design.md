## Context

见 `proposal.md` - Why。T0 已就绪（198 颜色原子 / 44 通用组件原子 / 31 排版与基础量原子，`npm run lint:styles` 批 2 通过）。实测边界：`.ai-workbench` 42 条 · `.case-workbench` 2 条 · workflow `--ac-*` 30 条（含 10 处字面量）· `modules/**`+`views/**` 声明 108 条、其中 88 处为字面量色值。

## Goals / Non-Goals

**Goals:** 模块令牌有唯一落点（每模块一份文件）· 模块级值必须引用 T0 · 作用域与视觉零变化 · 门禁可静态验证 T1。
**Non-Goals:** 不改 T0 词表 · 不改消费点引用名 · 不动 `views`（无模块级令牌）· 不做管道溯源（变更 C）· 不清理死文件（变更 C）。

## Decisions

### D1 · 文件布局与加载
`modules/{name}/tokens.css`，由 `main.ts` 与现有 4 份全局样式并列 import。选择理由：声明本身是惰性数据（只声明自定义属性），生效范围由选择器（模块页面根类）决定；集中 import 避免新增非 scoped `<style>` 块（现 6 处已需理由注释）。备选：由模块入口 `<style src>` 引入 → 必须是**非 scoped** 才是全局作用域，会新增 3 个无理由的非 scoped 块，弃用。

### D2 · 作用域保持模块页面根类
迁移只搬文件、不搬选择器：`.ai-workbench` / `.case-workbench` / `.workflow-workbench` 原样保留。依据：EP 2.7 `el-dialog` 默认不 Teleport（`append-to-body` 全仓 0），消费点都在根类之内。

### D3 · T1 的两级粒度
模块级（跨组件消费）→ `modules/{m}/tokens.css`；组件级（单组件消费）→ 组件自身根类载体保留，但值必须 `var(T0)`。本变更对 85 处组件级载体只改值，不搬位置。

### D4 · 值等价而非文本等价
颜色比较走规范化（hex 补全 / rgba 去空格 / 大小写归一），因此 `#fff` 与 `#ffffff` 视为同值。校验输出 `value_mismatch=0`。

## 模块防火墙自检

| 红线 | 本变更 |
|------|--------|
| 跨 App import / 写库 / 前端直连数据库 | 不涉及：改动面全在 `frontend/src/**` 样式声明与 `main.ts` 的样式 import |
| 新增依赖 | 无（未新增 npm 包、未改 vite 配置） |

## Risks / Trade-offs

- [模块令牌文件与组件文件分离，阅读时需跨文件] → 每份文件头部注释写明作用域与口径；门禁按文件校验
- [main.ts 的样式 import 列表增长到 7 条] → 以注释分组（全局样式 / 模块令牌），后续模块按同一模式追加
- [构建级验证缺失] → `vite build` 仍被沙箱拦（spawn EPERM）；以值等价校验 + `lint:styles` + `vue-tsc` 三重核验替代，浏览器核验未做

## Migration Plan

1. 抽 `.ai-workbench` / `.case-workbench` 两块 → 对应模块文件
2. 抽 workflow `--ac-*` → `modules/workflow/tokens.css`（值同步改 `var(--color-*)`）
3. 模块/组件级 85 处字面量 → `var(--color-*)`
4. `main.ts` 追加 3 条 import
5. 校验：值等价 0 mismatch · `lint:styles` 通过 · `vue-tsc` 与基线一致
6. 回滚：改动集中在 5 个文件 + 33 个组件的值替换，`git revert` 单次提交即可

## Open Questions

- `views` 是否需要模块令牌文件：当前其载体均为单组件消费，暂不新建；若后续出现跨组件场景再补
- 安全/加密相关的令牌约束是否纳入门禁（当前不在 T0/T1 口径内，涉及数据安全时按平台规范另开变更）