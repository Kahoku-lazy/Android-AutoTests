## 1. 后端：逐元素回填名称

- [x] 1.1 `apps/device_inspector/api.py` 的 `save_snapshot_to_elements` 新增 `element_aliases: list[dict] | None = None`；构造 `pairs = [(原始下标, 元素)]`（`element_ids` 存在时按其筛减），先按 `aliases`（rid 口径）回填、再按**原始下标**用 `element_aliases` 覆盖；验证：`manage.py check` 0 issues、`ruff check` 通过；集成测试断言同名 rid 两元素各自保名
- [x] 1.2 `apps/device_inspector/views.py` 的 `save_elements` 读取并透传 `element_aliases`；验证：`ruff check` 通过，端点路径与响应形状未变

## 2. 前端：按元素下标发送名称

- [x] 2.1 `store.ts` 的 `saveToElements` 用 `nameOverrides`（键=元素 `_idx`）组装 `element_aliases: [{index, name}]`，不再发送 rid 口径的 `aliases`；body 类型同步改为 `element_aliases?: {index; name}[]`；验证：新增前端单测断言请求体 `element_aliases` 为 `[{index:0,name:'甲'},{index:1,name:'乙'}]` 且 `body.aliases` 为 `undefined`（同名 rid 场景）

## 3. 测试

- [x] 3.1 新增 `tests/graybox/integration/test_inspector_save_element_aliases.py`（3 例）：① 同名 rid 两元素分别命名 → 落库后各自保留（`{'[0,0][10,10]': '第一行', '[0,20][10,30]': '第二行'}`）；② 只勾选原始下标 1 的元素 → 名称落到该元素而非筛减后的第 0 位；③ rid 口径 `aliases` 通道仍可用（AI 工具调用方不被破坏）；验证：**3 passed**；前端 `npx vitest run tests/device-inspector` → **4 passed**

## 4. 门禁与归档

- [x] 4.1 `openspec validate fix-inspector-save-alias-per-element --strict`；验证：valid
- [x] 4.2 `python manage.py check`（0 issues）+ `ruff check apps/device_inspector apps/element_locator tests/graybox/integration`（All checks passed，顺手修掉上一单遗留的 I001 import 顺序）+ 我的 5 个文件 `ruff format --check` 全通过；验证：见读数
      （附注：`apps/element_locator/admin.py` 与 `models.py` 有格式债，但**都不是本变更的文件**——`models.py` 是他人在途改动、`admin.py` 未修改，故未格式化，仅登记）
- [x] 4.3 `python -m pytest tests/graybox -q`；验证：**328 passed**（含本单新增 3 例；上一轮为 303，差值含他人在途新增用例）
- [x] 4.4 `npm run lint:styles`（`LINT_EXIT=0`）+ `npx vite build`（退出码 0，1m 45s）+ `npx vitest run tests/device-inspector`（4 passed）；验证：见读数
- [x] 4.5 前端请求体核对以单测为准（`store.spec.ts` 第 4 例断言 payload），后端落库以集成测试为准——两者合起来覆盖 4.5 的验收意图，且**不新增开发库数据**；验证：见 2.1 / 3.1
- [x] 4.6 归档：delta 写回 `device-inspector-page`「元素表格勾选驱动筛减保存」（正文补一句 + 新场景「同名 resource-id 的多个元素各自保留名称」位于第 117 行）；验证：该 requirement 现 8 个场景
