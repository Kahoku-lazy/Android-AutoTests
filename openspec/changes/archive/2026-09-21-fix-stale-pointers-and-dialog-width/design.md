## Context

- 宽度失真的证据（真机）：`.el-cascader` 根节点 `attrs = ["class", "tabindex"]`（**无 `data-v-*`**），故 `.save-folder[data-v-9e59799a] { width: 100% }` 永不匹配；`getComputedStyle(.save-folder).width = 218px`，而 `.save-page-select` = 394px（= `.el-form-item__content` 宽）。
- 指针失真：`frontend/AGENTS.md` 的「### 1. 硬性规范」当前只有 1–7 条，第 7 条正是字号规则；不存在 §1.5 / §1.14 子条（旧版编号残留）。
- 上一单 `remove-inspector-false-signals` 把宽度问题作为「伴随发现」登记并**未修**（理由：可见变化需产品确认）。本单兑现该结论。

## Goals / Non-Goals

**Goals:**

- 「目录路径」控件宽度与同弹窗其它字段一致（兑现作者已写下的 `width: 100%` 意图）
- 两处指向不存在条款的引用被修正或移除

**Non-Goals:**

- 不新增 `frontend/AGENTS.md` 条款
- 不做全仓指针对普查
- 不改弹窗/控件交互

## Decisions

**D1 用 `.save-folder-field :deep(.el-cascader)` 兑现全宽意图，而不是保留 218px**
依据：作者已经写了 `.save-folder { width: 100% }`——全宽是**既有意图**，只是写法在 scoped 下打不中（子组件根节点无作用域属性）；同一弹窗的「选择页面」下拉本就是全宽，两个字段宽度不一致是缺陷而非设计。包裹层是普通元素、带作用域属性，`:deep()` 从它穿透到子组件内部是这个场景的标准写法。
备选：保持 218px 并删掉那条无效声明 → 否决（等于放弃作者已表达的意图，且同弹窗字段宽度继续不一致）。
**D2 删掉模板上的 `class="save-folder"`**
理由：唯一消费它的 CSS 规则被替换后，该 class 会变成无人消费的标记类（`frontend-l2-page-region`「No dead marker class」）。
**D3 `tokens.css` 指针改为 §1.7，而不是把 §1.14 原样保留**
理由：字号规则确实存在于第 7 条，指针应当指得到；这是注释内的文档修正，不改任何令牌值。
**D4 l4 spec 的 §1.5 括号引用**直接移除**，不换成别的引用**
理由：该规范句本身自足（「校验失败文案与 `ElMessage` 提示 MUST 由调用方处理」），AGENTS.md 里没有任何对应条款可指；换成指向本 spec 自己是循环引用。spec 正文一句未改，只是删掉悬空引用。

## 模块防火墙自检

- 跨 App import：零新增；后端零改动
- 前端 HTTP 出口 / 端点：不变
- 共享层：只改 `tokens.css` 的**注释**（值不变，样式门禁照跑）
- 迁移：零

## Risks / Trade-offs

- [控件变宽改变弹窗观感] → 这是本单唯一可见变化，且方向与同弹窗其它字段一致；真机测量前后宽度并留档
- [`:deep()` 在包裹层上不生效] → 真机核对 `getComputedStyle(.el-cascader).width` = 394px；若失效则回退为「保留 218px 并删掉无效声明」
- [删 `save-folder` class 影响 e2e 选择器] → 全仓检索 `save-folder`：仅本组件模板与样式命中，无选择器依赖

## Migration Plan

1. 改 `SaveToElementsDialog.vue`（模板 + CSS）→ 真机测量控件宽度
2. 改 `tokens.css` 注释指针
3. 写回 `frontend-l4-data-surface` 的 §1.5 引用移除
4. 门禁：`lint:styles` + `vite build` + `vitest tests/device-inspector` + `openspec validate --strict`
5. 回滚：`git revert`

## Open Questions

（无）
