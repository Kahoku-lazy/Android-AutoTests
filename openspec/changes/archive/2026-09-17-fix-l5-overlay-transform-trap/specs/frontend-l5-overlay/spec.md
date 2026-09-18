## ADDED Requirements

### Requirement: Blocking overlays escape transformed ancestors

阻塞型覆盖层（`el-dialog` / `el-drawer`）的遮罩 MUST 覆盖整个视口；系统 SHALL NOT 让覆盖层因祖先元素的 `transform` / `translate` / `rotate` / `scale` 建立包含块而被困在局部容器内。当覆盖层的挂载点位于带 transform 的容器之内时，该覆盖层 MUST Teleport 到 `body`（`el-dialog` 的 `append-to-body`），以同时保住容器的手绘倾斜与遮罩的全视口覆盖。容器自身的倾斜 MUST NOT 通过删除 `transform` 来规避本问题。

#### Scenario: Login error overlay mask covers the viewport

- **WHEN** 登录失败触发服务端错误浮层，而挂载它的 `.meeting-doodle` 带 `transform: rotate(1.2deg)`
- **THEN** `.el-overlay` 的实测矩形等于视口（1440×900 @ 0,0），而不是便签卡外框（约 424×403 @ 822,215）
- **AND** 浮层内容相对视口居中，而非相对便签卡居中

#### Scenario: Mask click closes from anywhere on the page

- **WHEN** 错误浮层打开后，用户点击便签卡范围之外的遮罩区域
- **THEN** 浮层关闭并向父组件 emit `close`
- **AND** 纯展示浮层保持 Element Plus 默认的点遮罩关闭（不写 `close-on-click-modal="false"`）

#### Scenario: Tilted container keeps its hand-drawn look

- **WHEN** 修复后检查登录页便签卡
- **THEN** `.meeting-doodle` 仍声明 `transform: rotate(1.2deg)`，视觉与修复前一致
- **AND** 该 transform 处留有指向覆盖层包含块约束的登记注释
