## ADDED Requirements

### Requirement: 样式引用完整性门禁覆盖全部样式载体

引用完整性检查 SHALL 覆盖 `.css` 文件全文与 `.vue` 的 `<style>` 块，MUST NOT 因文件类型或样式块而豁免扫描。运行时注入的自定义属性名（`:style="{ '--x': v }"`、`style="--x: v"`）SHALL 按边界汇集后参与判定，以覆盖注入点与消费点分处同目录不同文件（如组件与它的 `X.style.css`）的情形。

#### Scenario: 样式表中的悬空引用被拦截

- **WHEN** `.css` 文件或 `.vue` 的 `<style>` 块引用了一个全仓无声明、且非运行时注入的令牌
- **THEN** 门禁 SHALL 以非零退出码阻断并报出文件与行号

#### Scenario: 样式表引用未声明的模块令牌被拦截

- **WHEN** 某边界的 `.css` 引用了仅声明于其他边界的模块令牌
- **THEN** 门禁 SHALL 判定为跨边界借用并阻断

#### Scenario: 组件与其同目录样式表之间的注入不被误判

- **WHEN** 某边界内的 `.vue` 通过 `:style` 注入自定义属性名，同边界的 `.css`（如 `X.style.css`）消费该名字
- **THEN** 该引用 SHALL 视为可解析，不产生悬空或跨边界告警

### Requirement: 几何尺度由门禁持续校验且只降不增

阴影模糊半径、圆角字面量与动效时长 SHALL 由门禁持续校验。`box-shadow` 的模糊半径 MUST 为 0；`border-radius` MUST 取自 `--app-radius-*`/`--radius-*`、图形量白名单或已登记的独立造型，等价四值展开（`A B A B`）MUST NOT 保留；`transition`/`animation` 简写中的时长 MUST 取自 `--app-duration-*`（已登记的循环装饰动画除外）。画布侧驼峰 `fontSize` 与已登记的图形量字面量 SHALL 以只降不增的上限保留。

#### Scenario: 模糊阴影被拦截

- **WHEN** 源码中出现模糊半径非 0 的 `box-shadow`
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 未登记圆角字面量被拦截

- **WHEN** 源码中出现既非令牌、又不在登记清单内的 `border-radius` 字面量
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 等价四值圆角被拦截

- **WHEN** `border-radius` 写成 `A B A B` 且与两值写法渲染完全等价
- **THEN** 门禁 SHALL 判定为冗余写法并阻断

#### Scenario: 刻度外动效时长被拦截

- **WHEN** `transition` 或 `animation` 简写中出现非 `var(--app-duration-*)` 的裸时长
- **THEN** 门禁 SHALL 以非零退出码阻断

#### Scenario: 画布字号存量只降不增

- **WHEN** ECharts / VueFlow 配置中的驼峰 `fontSize` 数量超过已登记上限
- **THEN** 门禁 SHALL 阻断
