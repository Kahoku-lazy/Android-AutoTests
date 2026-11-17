# 设计：控制条两件改成输入件皮肤

## Context

`DevicePoolView.style.css:83-104` 的「统一按键皮肤」块把 `.el-button`、`.error-state__btn`、`.el-select__wrapper`、`.el-input__wrapper` 四类选择器绑在同一套几何里：

```css
border: 2px solid var(--ink);
border-radius: 2px;
box-shadow: 2px 2px 0 0 var(--ink);
font-weight: var(--app-font-weight-bold);
```

这正是「下拉和搜索框看着像按键」的根因。全局输入框皮肤在 `style.css:180-196`（白底、`--app-radius-sm`、无影、hover/focus 转柠黄），但被模块的 `!important` 按键皮肤压住了。

## Goals / Non-Goals

**Goals**：两件在视觉上明确是「可填/可选」的输入件；135° 渐变填充、浓度 45% → 20%；hover/focus 反馈与主题输入框一致；「上一页 / 下一页」等按键保持不变。

**Non-Goals**：不改筛选、搜索、分页逻辑；不改 `.filter-select` / `.device-search` 的宽度与 DOM 结构；不把渐变推广到全站输入框；不新增颜色原子。

## Decisions

### D1 把两个输入件从按键皮肤块里摘出来，单独成块

按键皮肤块只留 `.el-button` / `.error-state__btn`；`.el-select__wrapper`、`.el-input__wrapper` 另起一段输入件皮肤。这样「一个零件一套皮肤」在文件层面就分得开，后面再改按键也不会再次波及输入件。

### D2 渐变令牌落在 `tokens.css` 的 `--comp-*` 组，值全部 `color-mix` 派生

```css
--comp-device-field-fill: linear-gradient(
  135deg,
  color-mix(in srgb, var(--c-device) 45%, transparent),
  color-mix(in srgb, var(--c-device) 20%, transparent)
);
```

- 与 `--comp-kit-save-gradient` 同一写法：**不新增颜色原子**，两端都从既有模块色派生，门禁（字面量色值只许出现在 tokens.css 的原子层）继续成立。
- 终点用 `transparent` 而不是 `--app-bg-card`：控制条直接坐在纸面上，混到透明即等于「浓度」，将来换底色也不会留一块死色。
- 令牌放共享 `tokens.css` 而不是模块 `tokens.css`：它只派生自全局模块色，没有模块私有颜色需要登记，多加一个只在 `index.vue` 里 `import` 一次的文件不划算。

### D3 输入件皮肤四条覆盖，其余交回主题

| 维度 | 本页输入件 | 依据 |
| --- | --- | --- |
| 边框 | `2px solid var(--ink)` | 与主题输入框一致（`style.css:184`） |
| 圆角 | `var(--app-radius-sm)`（`4px 8px`） | 输入框刻度，不再是按键的 `2px` |
| 填充 | `var(--comp-device-field-fill)` | 本变更新增 |
| 阴影 / 字重 | `box-shadow: none` / `var(--app-font-weight-regular)` | 撤掉按键的两处身份特征 |

hover / focus 不自己发明：显式把边框提到 `--c-dashboard`、focus 复刻主题的 `0 0 0 3px color-mix(--c-dashboard 20%)` 环——因为模块的 `!important` 会压掉全局的 `:hover` / `:focus-within`，必须在同处补回来。

### D4 渐变属于「已批准的偏离」，回写技能参考

doodle-craft 的默认口径是平涂、禁渐变。本次按需求方指定偏离，范围**只限这两个控件**；按 SKILL.md「偏离的唯一入口」要求，落地后把令牌与口径写回 `references/tokens.md`（§1.16 渐变）与 `references/components/form-controls.md`（§1 输入框）。

## Risks / Trade-offs

- [渐变的 45% 浓度压在纸底上，placeholder 对比度可能掉] → 渐变只铺背景、文字仍取 `--app-text-primary`；placeholder 保持主题既有色，实测对比度不降级。
- [两个控件色相比其他模块的输入框更重] → 只在设备页这一处；模块色 `--c-device` 本来就是设备页的识别色，用来标记「这是本页的输入件」是它的既定职责。
- [下拉展开后的选项列表仍走 EP 出厂白底] → 与主题其余下拉一致，本次不动弹层。

## Migration Plan

纯样式 + 一条令牌。回退 = 把两个选择器挪回按键皮肤块、删掉 `--comp-device-field-fill` 与两处技能参考条目。

## Open Questions

无（色相与渐变方向已由需求方在预览图中确认：薄荷绿、135°、45% → 20%）。
