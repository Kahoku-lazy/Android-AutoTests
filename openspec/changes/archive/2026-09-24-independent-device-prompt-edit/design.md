## Context

现状（代码事实，动机见 proposal.md）：

- 设备提示词区整块内联在 `ToolboxPanel.vue` 里：模板用单个 `editing` 布尔同时切换三份的编辑框，面板页头放整块的「编辑 / 取消 / 保存」，三个角色下拉头各自重复一份「保存」「查看历史记录」。
- `useDevicePrompts` 只有一份三键 `draft` 与一个 `editing` 布尔；`save()` 与 `autoSaveIfDirty()` 都按「三份一起」提交。
- 后端 `POST /api/ai/device-prompts/update/` 是整组语义：三键必须齐备且去空白后非空，写库后按整组三份留一份存档（auto 滚动三份 / permanent 唯一）。该契约本单不动。
- 体积门禁：`ToolboxPanel.vue` 现 499 行，`python run.py check` 的 `vue-file-size`（<500 行）是拦截项——任何净增行都会立刻变红，因此本单必须先把区块整块移出。
- `PROMPT_ROLES` 目前在 `ToolboxPanel.vue` 与 `DevicePromptHistoryDrawer.vue` 各写一份，本单会引入第三处使用。
- 按钮外观约束：`frontend-doodle-button` 的硬边皮肤作用域是「已登记承载页清单」（设备管理页 / 设备检查器 / 元素定位文件详情页），AI 工具页属未登记页，其按键外观 MUST 与变更前一致。

## Goals / Non-Goals

**Goals:**

- 三份提示词各自独立的编辑入口、编辑态与草稿；保存一份时不把另一份的未保存草稿写进库。
- 一份的「查看历史记录」入口唯一；进入某份编辑只展开该份。
- 把设备提示词区块整块移出 `ToolboxPanel.vue`，使该文件回落到体积门禁内且不再借道增长。

**Non-Goals:**

- 不改后端、不改接口载荷与存档结构（不做按份 PATCH、不做按份存档）。
- 不把「取消」改成真正丢弃改动（沿用既有「退出编辑自动保存」语义）。
- 不改这一区域的任何视觉与配色（未登记页按键外观必须不变）。

## Decisions

**D1 编辑态按角色表达，草稿仍是一份三键对象。**
`editing: boolean` 改为 `editingRoles: Record<Role, boolean>`，配 `isEditing(role)` / `startEdit(role)` / `cancelEdit(role)` / `save(role)`；`draft` 保持 `{planner, executor, verifier}` 单对象——三键天然按字段隔离，每份输入框只绑自己的键，多份并存时不会互相覆盖。
备选：每角色一个独立 composable 实例 → 否决：会三次拉取同一份接口、三份互不相干的历史状态，成本大于收益。

**D2 保存按「已保存值为基底 + 覆盖被保存的份」合并提交。**
`save(role)` 构造 `{...已保存三件, [role]: draft[role]}` 再走既有 permanent 确认与接口。这是接口整组语义下实现「只改一份」的唯一正确姿势：基底取已保存值，保证不携带其它编辑中份的草稿。
备选：后端新增按份更新 → 否决：会牵动存档结构、接口契约与既有 spec，收益仅为少提交两个字段。

**D3 自动保存按触发点收敛写入范围，一次写库。**
`autoSaveIfDirty(roles?)` 先算脏份集合（可选按份过滤），为空则不写库；非空则以已保存值为基底合并这些份，提交一次 `archive=auto`。切换来源 / 离开页面传入全部脏份，点「取消」只传入该份——否则取消一份会顺手把另一份仍在编辑中的草稿写进库，与「独立」相矛盾。
备选：逐个脏份各写一次 → 否决：自动档滚动池只有三份，一次退出编辑产生多份无关存档会把历史冲掉，且与「一次编辑动作 = 一份存档」的语义不符。

**D4 「取消」语义保持「退出编辑 + 有改动自动落库」，且只作用于该份。**
`cancelEdit(role)` 只处理该 role：脏则按 D3 以 `[role]` 过滤写库一次并留一份自动档，然后重置该 role 草稿为库中值、退出该 role 编辑态；其余份的草稿与编辑态一律不动。
备选：改成真正丢弃 → 否决：与既有 spec「退出编辑自动保存」直接冲突并改变已上线行为，超出本单范围。

**D5 拆出 `DevicePromptPanel.vue`，由它自己持有 `useDevicePrompts`。**
面板按来源渲染：`<DevicePromptPanel v-if="activeSource === 'prompt'" :can-manage="props.canManage" />`，提示词来源的标题行与动作行（含唯一的「查看历史记录」）也由该组件渲染，父级 `.tb-cat-head` 对提示词来源不再渲染。切换来源、离开页面都由该组件卸载触发 `onBeforeUnmount` 自动保存，父级原有的 `watch(activeSource)` + `onBeforeUnmount` 两处自动保存随之删除。
副作用：提示词拉取时机从「进页面即拉」变成「切到该来源才拉」（少一次请求，界面进来源时用既有 loading）。
备选：拆出的组件做纯展示、状态与编排留在父级 → 否决：为靠近门禁线的父文件保留全部编排与十余项 props，违背本次拆分目的，也与模块内「组件直接调用 composable」的既有写法不一致。

**D6 样式随组件迁移，通用壳样式小范围镜像，视觉零变化。**
`.tb-prompt-*` 全部规则迁入新的 `DevicePromptPanel.style.css`；该组件用到的少量壳样式（`.tb-cat-head` / `.tb-cat-title` / `.tb-cat-sub` / `.tb-cat-actions` / `.tb-btn` / `.tb-btn-primary` 及其 hover 与 `prefers-reduced-motion` 覆写）以同名选择器镜像一份，数值全部引用既有令牌，并在注释里标明镜像来源。
备选一：抽成全局共享样式表 → 否决：作用域外溢，会改变历史抽屉等既有元素外观，与「未登记页外观不变」相冲突；备选二：子组件直接 `<style src="./ToolboxPanel.style.css" scoped>` → 否决：整张 842 行样式表复制进 bundle，且把无关规则绑到该组件上。

**D7 `PROMPT_ROLES` 收敛为单一真相源。**
提到 `constants.ts` 并导出 `Role` 联合类型，面板、新组件与历史抽屉统一引用。
备选：各自再写一份 → 否决：本单会把它变成三处重复，改标签要改三处。

**D8 进入编辑只展开该份。**
`startEdit(role)` 只把该 role 并入 `expanded` 列表，不再强制展开全部三份；折叠面板的展开集仍由用户自己控制。

## 模块防火墙自检

- 本变更**纯前端**，只落在 `frontend/src/modules/ai-assistant/**`：无后端改动、无跨 App import、无新增跨模块依赖、无新依赖。
- 前端 HTTP 仍只经模块既有 `api/toolbox.ts` 走既有 `/api/ai/device-prompts*` 端点，不新增出口、不改路径与载荷字段。
- 无写库路径、无 ORM、无 ws/sse 通道变化、无 `agent_scope` 变更。
- 未触碰共享件与全局主题（`DoodleBtn` / `tokens.css` / `style.css` 等一律无改动）。

## Risks / Trade-offs

- [组件拆分后提示词改为进入来源时才拉取] → 只影响一次请求时机；进入来源沿用既有 loading 态，数据正确性不变。
- [切换来源的自动保存依赖组件卸载] → 与现状同为 fire-and-forget 写库；D3 的「仅编辑中且有改动才写」保证不会因卸载产生空写。
- [镜像样式可能与父级后续改动漂移] → 镜像处写明来源注释；数值只用令牌，不引入新色值，保证两侧仍同值。
- [父级测试 mock 了旧 composable 面（`editing` / `startEdit` / `save`）] → 拆出后父级不再引用该 composable，删除该 mock 段；按角色编辑的覆盖改由新组件用例承担。
- [同改多份后只保存其中一份，另一份草稿仍在编辑态] → 这是本单期望的独立行为；保存成功 MUST NOT 重置其它份的草稿与编辑态。

## 迁移与回滚

纯前端、无数据迁移、无接口变化：合并即生效，回滚只需还原相关前端文件，无后端与存档联动。
