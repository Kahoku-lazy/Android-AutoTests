## 1. 补 EP stub 并恢复断言可达

- [x] 1.1 补 `el-dialog` stub：**带类型的 props**（`modelValue/title/width/appendToBody` 均为 Boolean/String 显式类型）、emit `update:modelValue`；`v-if="modelValue"` 渲染 `.el-overlay`（`@click` 关闭）> `.el-dialog`（`@click.stop` + `@keydown.esc` 关闭），内部渲染默认插槽与 `footer` 具名插槽。验证：运行输出不再有 `Failed to resolve component: el-dialog`
- [x] 1.2 补 `el-button` stub（`<button type="button" class="el-button"><slot /></button>`，不额外 `$emit('click')`）。验证：不再有 `Failed to resolve component: el-button` 告警
- [x] 1.3 6 条既有断言**逐字未改**且全部通过（`不渲染内容` / `展示错误文案` / `点「知道了」` / `visible=false ESC 不触发` / `按 ESC` / `点击遮罩`）。验证：该文件 `7 passed`（6 既有 + 1 新增）

## 2. 为 L5 约束补单元级守卫

- [x] 2.1 新增断言「`el-dialog` 收到 `append-to-body`」：stub 把收到的 prop 透出为 `data-append-to-body`，断言其为 `'true'`。
      **反向验证**：把组件里的 `append-to-body` 临时抽掉 → `1 failed | 6 passed`（恰好红 1 条）；恢复后 `7 passed`，证明该守卫真的有效
- [x] 2.2 实现中发现的坑并已就地登记：stub 的 props **必须用带类型的对象写法**。用数组写法 `props: ['appendToBody']` 时，模板里的无值属性 `append-to-body` 会以空字符串 `''` 到达（只有 Boolean 类型才触发 Vue 的空串→true 强转），断言会永远红；已在代码注释中写明原因，防止后人「简化」回去

## 3. 门禁与归档

- [x] 3.1 `npx vitest run --project login/p0 --project login/p1` = **12 files / 65 tests 全通过**（修复前 61 passed / 3 failed；65 = 61 + 3 修复 + 1 新增）
- [x] 3.2 `npm run typecheck` 共 30 例错误 = **与既有基线同数**，其中登录/浮层相关 **0** 例（30 例均在 `tests/dashboard/**` 与 `ProjectTree.vue`）
- [x] 3.3 `openspec validate fix-login-overlay-spec-stubs` 通过后归档（`skip_specs: true`，无 spec 变更；生产代码零改动）
