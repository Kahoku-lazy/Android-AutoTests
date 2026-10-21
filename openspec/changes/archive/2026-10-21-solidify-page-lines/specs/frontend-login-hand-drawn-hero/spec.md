## MODIFIED Requirements

### Requirement: 登录页线型由登录页作用域令牌决定

登录页（`/login`）的描边线型 SHALL 由 `.login-page` 作用域内的具名令牌 `--login-line` 决定，其值 SHALL 为 `dashed`。登录页 MUST NOT 依赖任何共享组件令牌（`--comp-*`）或其它模块的令牌来决定自身线型。

该要求是对"登录页是唯一保留虚线的页面"这一既有决定的所有权归属：虚线 MUST 是登录页自己登记的选择，使其余页面把虚线改为实线时，登录页 MUST NOT 随之改变、也 MUST NOT 需要改动共享令牌来维持。

#### Scenario: 登录页虚线来自自有令牌

- **WHEN** 打开 `/login`，检查 Meeting doodle 容器与「注册」次按钮的计算 `border-style`
- **THEN** 二者均为 `dashed`
- **AND** 其线型令牌声明在 `.login-page` 作用域内，而非来自共享层或侧栏

#### Scenario: 共享线型变化不波及登录页

- **WHEN** 把侧栏作用域令牌 `--sidebar-line` 从 `solid` 临时改为 `dashed`
- **THEN** 登录页的 Meeting doodle 与「注册」次按钮仍渲染为虚线
- **AND** 登录页样式无需任何改动

#### Scenario: 令牌化不改变可见外观

- **WHEN** 对比本变更前后 `/login` 的渲染结果（1440×900 与 480×900 两个视口）
- **THEN** 描边宽度、线型、描边色与阴影的计算值一致
- **AND** 唯一几何差异来自两行校验提示各自恢复 8px 上移：Meeting doodle 高度减少 16px、其内容随垂直居中重新分布，描边宽度仍为 2px（浏览器对 2.5px 的取整结果）
