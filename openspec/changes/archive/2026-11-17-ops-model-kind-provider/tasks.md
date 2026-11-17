## 1. 常量与类型（唯一真相源）

- [x] 1.1 `types.ts` 新增 `OpsModelKind`（`chat` / `tts` / `realtime`），`OpsModelConfig` 与 `OpsModelConfigInput` 的 `model_kind` 改用该类型；验证：`npx vue-tsc --noEmit` 0 错误。**验证结果**：通过。
- [x] 1.2 `constants.ts` 给 `OPS_PROVIDER_OPTIONS` 每项补 `kinds`，新增 `providersForKind` / `defaultProviderForKind` / `normalizeProvider` / `keyForProvider` / `modelKindLabel`，并把「模型类型」列插到「密钥环境变量」与「模型名称」之间；验证：`npx vue-tsc --noEmit` 0 错误，映射断言由 3.1 覆盖。**验证结果**：通过。

## 2. 页面行为

- [x] 2.1 `model-configs.vue`：厂商下拉改用 `providersForKind(form.model_kind)`；新增 `watch(form.model_kind)`，当前厂商不受支持时切到 `defaultProviderForKind`；验证：3.2 组件用例断言实时语音 / 语音合成的厂商选项只剩 dashscope。**验证结果**：通过（组件用例 3 项）。
- [x] 2.2 `model-configs.vue`：`openCreate` 默认组合保持聊天 + deepseek；`openEdit` 用 `normalizeProvider` 归一历史厂商并按归一后的厂商重算密钥变量；验证：3.1 的归一断言 + `npx vue-tsc --noEmit`。**验证结果**：通过。
- [x] 2.3 `model-configs.vue`：表格增加 `#cell-model_kind` 插槽，用 `modelKindLabel(record.model_kind)` 渲染；验证：3.1 断言列序与标签映射。**验证结果**：通过。

## 3. 测试

- [x] 3.1 新增 `frontend/tests/ops-console/p0/model-configs.spec.ts`：覆盖 chat / realtime / tts 的厂商集合、默认厂商、`normalizeProvider`、`modelKindLabel`（含缺失值），以及表格列序在模型名称前；验证：`npx vitest run tests/ops-console` 全绿。**验证结果**：`3 passed / 22 tests`，其中本文件 9 项。
- [x] 3.2 同一文件补组件级用例：打开新建抽屉 → 模型类型从聊天切到实时语音 → 厂商变 dashscope、密钥变量变 `DASHSCOPE_API_KEY`；再切实时语音 / 语音合成 → 只显示 dashscope 且已选值保留；验证：`npx vitest run tests/ops-console` 全绿。**验证结果**：通过（挂载真实 SFC + 桩化 el-* 与 api）。

## 4. 门禁与收尾

- [x] 4.1 前端门禁：`npx vue-tsc --noEmit`、`npx eslint src/modules/ops-console/model-configs.vue src/modules/ops-console/constants.ts src/modules/ops-console/types.ts tests/ops-console/p0/model-configs.spec.ts`、`npm run lint:styles`。**验证结果**：`vue-tsc` 与 `eslint` 0 错误；`lint:styles` 批 2 通过，批 3 仍为既有的 21 处 `task-list` 跨边界借用（与 `sketched-ui-kit` 记录的基线一致，本次未新增）。
- [x] 4.2 `openspec validate ops-model-kind-provider --strict` 通过，并把各任务的实际验证结果回写到本文件。**验证结果**：`Change 'ops-model-kind-provider' is valid`。

## 5. 单模型 / 音色位置 / 语音合成免地址（2026-11-16 第二轮）

- [x] 5.1 同步 `proposal.md` / `specs/ops-model-config/spec.md` / `design.md`：补单模型、音色位置、语音合成免地址三条需求与 D6–D9 决策；验证：`openspec validate ops-model-kind-provider --strict`。**验证结果**：valid。
- [x] 5.2 `model-configs.vue`：新增 `singleModelName` 计算属性；模板非聊天分支只渲染一个名称输入（无「+ 添加一行」/「删除」），聊天分支保持多行；`watch(model_kind)` 切到非聊天时把 `nameRows` 截断为首行；`namesInForm()` 非聊天只取首行；验证：5.6 组件用例。**验证结果**：通过。
- [x] 5.3 `model-configs.vue`：把「音色」字段整体移到「模型名称」字段之后；验证：5.6 的字段顺序断言。**验证结果**：通过（`音色` 紧接 `模型名称`）。
- [x] 5.4 `model-configs.vue`：`save()` 在 `model_kind === "tts"` 时跳过 API 地址校验；验证：5.6 中语音合成不填地址仍调用创建接口。**验证结果**：通过。
- [x] 5.5 `backend/apps/ai_assistant/serializers.py`：`base_url` 改为 `required=False, allow_blank=True`，`validate()` 仍只对聊天 / 实时语音校验地址；新增 `tests/ai_assistant/api/test_model_configs.py` 覆盖「语音合成空地址 201」「聊天空地址 400」「语音合成再次编辑保存 200」；验证：`python -m pytest tests/ai_assistant/api/test_model_configs.py -q`。**验证结果**：3 passed；`tests/ai_assistant/api` 全量 24 passed。
- [x] 5.6 扩展 `frontend/tests/ops-console/p0/model-configs.spec.ts`：实时语音 / 语音合成只一个名称输入且无添加 / 删除；聊天三行切实时语音后只剩一行；切回聊天可再添加；音色紧随模型名称；语音合成保存只提交一个名称且 `base_url` 为空；验证：`npx vitest run tests/ops-console`。**验证结果**：3 个文件 / 26 项全绿（本文件 13 项）。
- [x] 5.7 回归门禁：`npx vue-tsc --noEmit`、`npx eslint`（改动文件）、`npm run build`、`openspec validate ops-model-kind-provider --strict`；验证：全部通过并回写结果。**验证结果**：`vue-tsc` / `eslint` 0 错误；`npm run build` 成功；`ruff check` / `ruff format --check` 通过；`manage.py check` 0 issues；`openspec validate` valid。
