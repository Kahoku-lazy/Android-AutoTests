## ADDED Requirements

### Requirement: 阴影规格扁平且不含模糊投影

前端样式中的阴影（`box-shadow` / `text-shadow`，**含经自定义属性间接声明**的阴影值）MUST 采用扁平硬偏移形式：模糊半径（长度序列的第三个值）MUST 为 `0`。系统 SHALL NOT 使用带模糊半径的投影表达层次或"悬浮感"，也 SHALL NOT 使用外发光（形如 `0 0 <blur>`）作为强调手段。阴影的偏移量与色源 SHOULD 取 `tokens.css` 已登记的 `--app-shadow-*` / `--comp-*-shadow*` 令牌；模块确需自定义色源时，该色源仍 MUST 是已登记的颜色原子或引用它的局部自定义属性。

#### Scenario: No blurred shadow remains in the source tree

- **WHEN** 静态检索 `frontend/src` 下全部 `.vue` / `.css` 的阴影声明（包括自定义属性值内嵌的阴影）并解析其模糊半径
- **THEN** 模糊半径大于 `0` 的命中数为 `0`
- **AND** 本轮收敛 `ai-assistant` 2 处、`device-inspector` 4 处、`workflow` 2 处

#### Scenario: Floating surfaces use flat hard shadow

- **WHEN** 打开设备检查器的截图面板与两个放大预览浮层，以及工作流的 API 节点与元素选择浮层
- **THEN** 这些表面的阴影为零模糊硬偏移（无光晕、无渐变过渡的柔影）
- **AND** 浮层仍与下层纸面可区分（描边或硬偏移影至少其一可见）

#### Scenario: Indirectly declared shadows obey the same rule

- **WHEN** 某组件通过自定义属性（例如 `--avatar-shadow`）间接声明阴影并在消费处使用 `box-shadow: var(--avatar-shadow)`
- **THEN** 该自定义属性的值同样满足零模糊约束
- **AND** 收敛后不保留零消费方的阴影自定义属性