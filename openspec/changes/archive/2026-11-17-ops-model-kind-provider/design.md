## Context

现状：`frontend/src/modules/ops-console/model-configs.vue` 的抽屉已有「模型类型」下拉（聊天 / 实时语音 / 语音合成），但「厂商」下拉固定列三家，二者互不约束；模型名称沿用聊天的多行列表；「音色」排在模型名称之前；语音合成隐藏了 API 地址，保存时却仍走地址校验，服务端 `ModelConfigSerializer.base_url` 又是必填字段，导致语音合成实际存不进去。厂商选项、类型选项与列定义都集中在 `constants.ts`，页面只做渲染与提交。

约束：不新增接口、不做数据迁移；页面继续使用现有 `sketch-kit` 表单结构与 `AppTable` 列插槽；后端只放宽语音合成的 `base_url` 校验。

## Goals / Non-Goals

**Goals:**

- 让厂商下拉随模型类型收敛，切换类型时给出该类型的默认厂商并同步密钥变量。
- 打开历史配置时不把不受支持的厂商回显到下拉。
- 实时语音 / 语音合成只维护一个模型名称，聊天保留多行。
- 音色紧跟在模型名称之后，语音合成不再要求 API 地址。
- 在列表的模型名称左侧展示模型类型。

**Non-Goals:**

- 不在服务端增加「类型 × 厂商」校验；接口仍接受任意合法厂商与合法类型的组合。
- 不新增厂商、不调整三类模型的实际调用链、音色清单或 API 协议选项。
- 不改变聊天多行名称的批量创建方式（一个名称一条配置）。

## Decisions

### D1：支持关系放在 `constants.ts`，厂商选项携带支持类型

`OPS_PROVIDER_OPTIONS` 每项增加 `kinds`（该厂商支持的类型集合），并新增纯函数 `providersForKind(kind)` / `defaultProviderForKind(kind)` / `normalizeProvider(kind, provider)`；类型标签与列表列复用同一份 `OPS_MODEL_KIND_OPTIONS`。

备选：在 `model-configs.vue` 里写一份 `Record<kind, provider[]>`。否决——页面与常量表会出现两套真相源，以后加厂商要改两处。

### D2：不受支持的厂商直接不渲染，而不是渲染成禁用项

需求是「显示要准确、不能显示错误」。过滤后的选项列表短（最多三家），用户不需要看到灰掉的 deepseek / govee；Element Plus 也无需额外的 disabled 样式。备选「全量列出 + 禁用不支持的」会让用户误以为以后能选，否决。

### D3：切换类型时只在当前厂商失效时回退默认

类型变化后若当前厂商仍受支持则保留（例如 dashscope 从实时语音切到语音合成、再切回聊天都保留）；仅在失效时落到该类型的默认厂商（聊天 deepseek，实时语音 / 语音合成 dashscope）。备选「每次切类型都强制回默认」会清掉用户刚做的有效选择，否决。

### D4：打开编辑时归一厂商

`openEdit` 用 `normalizeProvider(row.model_kind, row.provider)` 决定回显值。原因：Element Plus 的 select 在绑定值不在选项里时显示空白，等于让用户面对一个「看不见的非法值」；归一后表单永远只呈现合法组合。代价是保存历史脏数据时会写回默认厂商，但这些组合本就是本变更要消灭的状态。

### D5：表格新增 `model_kind` 列并用标签渲染

列定义加在「密钥环境变量」与「模型名称」之间，页面用 `#cell-model_kind` 插槽调用 `modelKindLabel(record.model_kind)`。`modelKindLabel` 对缺失/未知值回落「聊天」，与后端字段默认值 `chat` 一致。备选直接在 `constants` 里放 `formatter` 函数——`AppTable` 不消费该字段，否决。

### D6：后端只放宽 `base_url`，不收紧厂商组合

`ModelConfigSerializer.base_url` 改为 `required=False, allow_blank=True`。字段级「非空」会先于 `validate()` 执行，不改这里，语音合成的空地址永远到不了 `validate()`。`validate()` 仍只对聊天 / 实时语音校验地址；「厂商 ∈ 三家」「类型 ∈ 三类」「厂商与密钥变量成对」不变。

备选：前端为语音合成偷偷填一个默认地址。否决——会落一条用户看不见、也无法编辑的地址，且与「语音合成不需要地址」的产品口径冲突。

### D7：实时语音 / 语音合成用一个计算属性收口单模型

`singleModelName` 计算属性：读取 `nameRows[0].value`，写入首行；没有行时补一行。模板在非聊天分支只渲染这个单输入框，聊天分支保留多行 + 添加 / 删除。`watch(model_kind)` 在切到非聊天时把 `nameRows` 截断为第一行，避免隐藏行被保存。`namesInForm()` 在非聊天时只取首行，作为第二道保险。

备选：保留多行、只在界面上藏掉其余行。否决——隐藏的值仍会被 `namesInForm()` 提交，等于「界面上一个、库里多个」。

### D8：音色移动到模型名称之后

模板把音色字段整体挪到模型名称字段之后，仍用 `v-if="form.model_kind !== 'chat'"` 控制显隐。没有改字段绑定与音色清单，只改顺序。

### D9：语音合成跳过地址校验

`save()` 仅在 `model_kind !== "tts"` 时调用 `validApiUrl`；聊天 / 实时语音保持原校验（实时语音允许 ws / wss）。`loadNames` 仍只对聊天开放。

## 模块防火墙自检

- 跨 App import：无。前端改动在 `frontend/src/modules/ops-console/` 与前端测试内；后端改动只在本 App 的 `serializers.py`。
- 跨 App service/runner/consumer：无。
- INSERT/UPDATE/DELETE：写库仍走 `backend/apps/ai_assistant/api.py`；本次不改写库函数。
- 前端不直连数据库；本页无仪表盘写操作。
- 结论：未引入新的跨模块依赖，不触碰 `engines/`。

## Risks / Trade-offs

- [历史脏组合在编辑保存后被改写为默认厂商] → 该组合本就不受支持；归一逻辑只影响非法组合，合法组合原样保留。
- [服务端仍可被直接调用写入非法厂商组合] → 本变更只放宽地址，不收紧组合；若后续要堵住，单独在 `ModelConfigSerializer` 增加组合校验并补 API 用例。
- [从聊天切到实时语音会丢掉多余名称行] → 这是「只维护一个」的预期行为；切回聊天后可重新添加。
- [`allow_blank=True` 会放宽语音合成之外的请求] → `validate()` 仍对聊天 / 实时语音调用 `_valid_http_url`，空地址照样 400；新增接口用例钉住这条。
- [类型 watcher 改厂商后密钥未同步] → 复用既有 `provider` watcher（厂商变化即写 `api_key_env`），并有组件用例覆盖。
- [Element Plus select 对不在选项中的值显示空白] → `openEdit` 先归一；新建态默认组合本就合法。

## Migration Plan

无数据迁移。`base_url` 放宽为可空不需要改库；已保存的语音合成配置（若有手工写入的）可直接再次编辑保存。回退只需恢复静态厂商列表、多行名称、旧字段顺序与 `allow_blank=True` 一处。
