# Sketched UI Kit — 手稿控件皮肤（分类）

> **定位**：控件级皮肤分类，只管 **按钮** 与 **输入框** 两类控件；不管页面骨架、卡片、表格、弹窗。
> **作用域根类**：`.sketch-kit`。容器加上这个类，容器内的按钮与输入框切到手稿控件皮肤；不加就仍是主线皮肤（`DoodleBtn` 实线硬影 + `el-input` 实线墨边）。
> **落点**：`frontend/src/shared/styles/sketched-kit.css`（`main.ts` 引一次）；令牌见 [../tokens.md](../tokens.md) §1.18。
> **参考**：需求方提供的两张变体图（按钮五态 / 输入四态）；风格来源 StyleKit「Hand-Drawn Doodle」showcase <https://www.stylekit.top/styles/hand-drawn-doodle/showcase>。

## 0. 与主线皮肤的关系（别混用）

| 维度 | 主线皮肤 | Sketched UI Kit |
| --- | --- | --- |
| 按钮描边 | `2.5px solid var(--ink)` + 硬影 | **描边态 `1.5px dashed`，无影**；填充态保持实线 + 硬影 |
| 危险按钮 | 实心红底 + 白字 | **红虚线描边 + 纸底 + 红字** |
| 输入框 | `2px solid var(--ink)` 实线 | **`1.5px dashed` 浅墨边** |
| 适用 | 全站默认 | 手稿 / 纸片语境的表单与工具条（首例：运营后台「新建模型」抽屉） |

**一个界面要么整块用 kit，要么不用**：禁止同一个表单里一半虚线一半实线；禁止把 `.sketch-kit` 挂到页面根（那是换主题，不是用分类，需要另立变更）。

## 1. 按钮（图一 · 五态）

五态映射到 `DoodleBtn` 的现有 tone，**不新增按钮组件**：

| 图上名称 | 用法 | tone | 规格 |
| --- | --- | --- | --- |
| Primary | 次级/中性动作（取消、加载、添加一行） | `paper` | 框 `var(--comp-kit-border)`（`1.5px dashed`）· 底 `--app-bg-card` · 字 `--ink` · 无影 |
| Danger | 破坏性动作（删除行） | `danger` | 框色 `var(--comp-kit-danger-line)` · 字 `var(--comp-kit-danger-ink)` · 底 `--app-bg-card` · 无影 |
| Highlight | 主行动（保存） | `yellow` | 框 `2.5px solid var(--ink)` · 底 `--c-dashboard` · 字 `--ink` · 硬影 `3px 3px 0 0 var(--ink)` |
| Commit（保存/提交） | 表单主行动 | 任意 tone + **`class="doodle-btn--save"`** | **与 Primary 同一套几何**：框 `var(--comp-kit-border)`（虚线）· 无影；区别只在填充 —— 底 = **绿色渐变** `--comp-kit-save-gradient`（顶端深绿 → 底端淡绿） |
| Disabled | 不可用 | 任意 tone + `disabled` | 框 `var(--comp-kit-border-faint)` · 底 `--app-bg-subtle` · 字 `--app-text-secondary` · 无影 |
| Teal | 校验/查看类动作 | `teal` | 框 `2.5px solid var(--ink)` · 底 `--c-case` · 字 `--ink` · 硬影 `3px 3px 0 0 var(--ink)` |

共用几何：`min-height: 34px` · `padding: 0 var(--app-space-md)` · `border-radius: var(--comp-kit-radius)`（`3px`）· 字号 `var(--app-size-sm)` · 字重 `--app-font-weight-heavy`。label 行里的小动作按钮（如「加载模型」）压到 `28px` + 12px 字，避免把 label 行撑高。

> **2026-11-16 需求方指定**：`保存/提交` 用**绿色渐变填充**（深→淡），与 hand-drawn-doodle 上游「flat marker colors only、禁渐变」相反。这是**已批准的偏离**：仅限 `.doodle-btn--save` 一个变体，色相取成功色（`--app-status-success`），两端由原子 `color-mix` 派生，不新增颜色原子；其它按钮仍然只用平涂。

交互：

- 描边态 hover → 底 `--app-highlight`，**不位移、不加影**（虚线框靠底色变化给反馈）。
- 填充态 hover → `translate(-1px,-1px)` + 影 `4px`；active → `translate(2px,2px)` + 影 `1px`。
- focus-visible → `outline: 2px solid var(--c-dashboard); outline-offset: 2px`（键盘可达，不许省）。
- **焦点语言全 kit 一套**：按钮用 `:focus-visible`、输入框用 `:focus-within`，但都是同一个 `2px` outline + `2px` offset；输入框**不再**用扩散环。
- **禁用态文字对比度豁免**（WCAG 对 disabled 控件不要求 4.5:1）；非禁用态的 danger 文字必须用 `--comp-kit-danger-ink`，不许用 `--app-marker-red`（在纸底上只有 ~2.5:1）。

## 2. 输入框（图二 · 四态 + label）

| 态 | 规格 |
| --- | --- |
| 默认 | 框 `var(--comp-kit-border-soft)`（`1.5px dashed` 浅墨）· 底 `--app-bg-input` · 圆角 `var(--comp-kit-radius)` · `box-shadow: none` · `min-height: 36px` · 内边距 `0 var(--app-space-sm)` |
| hover | 框色提到 `var(--comp-kit-line)` |
| focus / focus-within | 框色 `var(--comp-kit-line)` + 与按钮同一套 `2px solid var(--c-dashboard)` outline（offset `2px`）；内层控件显式 `outline: none`，焦点指示只由 kit 提供 |
| disabled | 框 `var(--comp-kit-border-faint)` · 底 `--app-bg-subtle` · 字 `--app-text-secondary` |
| 多行（Long note） | 同默认框 + `padding: var(--app-space-sm)` · `min-height: 96px` · `resize: vertical` |
| placeholder | `--app-text-muted` |

**label（字段标题）**：`font-size: var(--app-size-sm)`（14px，与动作按钮同一档）· 色 `--ink` · **不写字距**。2026-11-16 需求方调整：原来用 12px + `0.08em` 字距的次级灰，读起来像辅助说明，现在与「+ 添加一行」这类按钮文字同字号同色，作为字段标题更立得住。**下限仍是 12px**，不许再往下缩。

控件本体（`el-input` / `el-select` / `el-textarea`）的字母间距必须重置为 `normal`，否则 `letter-spacing` 会从 label 继承进输入内容。

## 3. 用法（平台内 Vue）

```vue
<el-drawer v-model="open" title="新建模型" size="min(460px, 92vw)">
  <!-- 作用域根只挂 .sketch-kit；结构类挂在它**内部**（kit 全是后代选择器） -->
  <div class="sketch-kit">
    <div class="sketch-form">
      <label class="sketch-field">
        <span class="sketch-field__label">厂商</span>
        <el-select v-model="form.provider">…</el-select>
      </label>
      <label class="sketch-field">
        <span class="sketch-field__label">地址</span>
        <el-input v-model="form.base_url" placeholder="可空，空则用厂商默认地址" />
      </label>
      <div class="sketch-form__actions">
        <DoodleBtn tone="paper" @click="open = false">取消</DoodleBtn>
        <DoodleBtn tone="yellow" class="doodle-btn--save" @click="save">保存</DoodleBtn>
      </div>
    </div>
  </div>
</el-drawer>
```

- `.sketch-form` / `.sketch-field` / `.sketch-form__actions` 由 kit 样式表提供（纵向 `--app-space-md` 间距、label 在上、动作区右对齐）。
- **`.sketch-kit` 不能和 `.sketch-form` 挂在同一个元素上**：kit 用 `.sketch-kit .sketch-form` 这种后代选择器，同级两个类不命中，表现为"表单完全没有间距"（2026-11-16 在「新建模型」上实际踩到过）。
- 按钮继续用 `DoodleBtn`，**不要**在 kit 里另造按钮组件；保存/提交加 `class="doodle-btn--save"` 走绿色渐变。

## 4. 线型白名单（这条会改 SKILL.md §线型规则）

kit 是虚线在仓内的**第二个合法来源**，范围写死：

- 允许：`.sketch-kit` 作用域内的按钮描边态、输入框 / 多行框 / 下拉框边框。
- 允许的文件只有 `frontend/src/shared/styles/sketched-kit.css`（另加既有白名单 `AgentRouteCard.vue`）。
- 不允许：卡片、表纸、弹窗/抽屉外框、列表分隔、页面装饰、图表容器；也不允许把 kit 的虚线 CSS 抄进组件。

## 5. 反模式

- ❌ 把 `.sketch-kit` 挂到页面根 "顺手统一"——那是全局换肤，要走变更，不是用分类。
- ❌ 在 kit 里写死颜色/字号/间距字面量；一律走 `--comp-kit-*` 与 `--app-*`。
- ❌ 把 `.sketch-kit` 与 `.sketch-form` 挂在同一个元素上（后代选择器不命中，间距全丢）。
- ❌ 给保存按钮再加一层渐变/阴影；色相已固定为成功色，深浅只由 `--comp-kit-save-from` / `-to` 决定。
- ❌ 用 `border-image` / repeating-gradient 画"假虚线"绕过门禁。
- ❌ 在同一个抽屉里混用主线输入框（实线）与 kit 输入框（虚线）。
- ❌ 给 kit 按钮保留主线的硬影：**描边态必须无影**，否则与图上的手绘虚线不是一套语言。
