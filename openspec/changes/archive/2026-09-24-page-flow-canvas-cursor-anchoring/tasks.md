## 1. 浮层贴边（纯函数 + 三个浮层接入）

- [x] 1.1 新增浮层定位纯函数（工作流模块 `helpers/overlayPosition.ts`）：`containOverlayPosition(anchor, size, viewport, margin=8)` 返回屏内坐标；浮层大于视口时收敛到 margin。验证：`frontend/tests/workflow/p0/overlay-position.spec.ts` 8 用例全绿（含正常位、右/下越界、超大浮层、尺寸为 0 回落常量）
- [x] 1.2 节点右键菜单接入贴边定位（`useContainedOverlay`：先按常量落位、渲染后按实测尺寸再收敛；菜单本体与「选择 Android 页面」列表同一浮层）。验证：`frontend/tests/workflow/p0/node-menu-containment.spec.ts` 以越界锚点挂载组件，断言 `left/top` 使浮层完整落在视口内（含列表模式）
- [x] 1.3 连线右键菜单接入同一套组合式函数。验证：同一文件的「画布连线右键菜单」用例以右下角锚点断言 `left/top` 在屏内，重命名态同样在屏内
- [x] 1.4 画布元素选择器（「+ 添加元素」浮层）接入同一套，并为三个浮层加 CSS 兜底 `max-height: min(<自然高度>, calc(100dvh - 16px))`，内部列表区改为随外层收缩滚动。验证：`npx vue-tsc --noEmit` 零错误 + 浏览器实测（任务 3.3）确认矮窗口下浮层上下边缘都在视口内
- [x] 1.5 确认浮层仍是非模态光标锚定菜单：不出现全屏遮罩节点、菜单不居中。验证：`node-menu-containment.spec.ts` 断言无 `.el-overlay` / 自绘遮罩，且 left 与光标一致、不等于视口居中值
- [x] 1.6 「选择 Android 页面」列表加载完成后再次收敛（列表渲染后浮层由 126px 涨到 420px，只在打开瞬间收敛会把底边顶出视口）。验证：浏览器实测列表盒 `y=572, height=420` → 底边 992 ≤ 1000−8

## 2. 新建页面节点落在鼠标处

- [x] 2.1 画布容器记录鼠标最后停留的客户端坐标（`mousemove`）；新建时经本模块纯函数把屏幕坐标换算为画布坐标（**不做 16px 网格吸附**），再按节点实测尺寸把中心对准该点；鼠标未进过画布时退到画布可视区域中心。验证：`frontend/tests/workflow/p0/canvas-placement.spec.ts` 8 用例（含「1px 屏幕位移必须有非零画布位移」）+ `frontend/tests/workflow/p0/page-node-placement.spec.ts` 5 用例断言 `pos = 中心换算点 − 尺寸的一半`；浏览器实测中心与鼠标**零偏差**
- [x] 2.2 同一位置连续新建做最小错位（按节点中心比较，步长 24×16，最多 8 步），保证不出现完全重合的节点。验证：单测连续两次点击「+ 页面」断言位移 = (24,16)；浏览器实测位移 (40,26) = (24,16)×zoom(1.65)
- [x] 2.3 回归确认落点规则不改动既有行为：节点命名仍为「页面N」、上限仍为 50、既有点坐标不变、自动保存照旧。验证：`cd frontend && npx vitest run tests/workflow/p0` 6 文件 41 用例全绿（含既有 13 条）

## 3. 门禁与实测

- [x] 3.1 前端静态门禁（只跑改动范围）：`npx prettier --check src/modules/workflow tests/workflow/p0/*.spec.ts` 全绿 · `npx eslint src/modules/workflow` 0 error（46 条既有 warning）· `npx vue-tsc --noEmit` 0 错误
- [x] 3.2 浏览器实测·落点：临时流程画布上鼠标停在 (364,896) 后点「+ 页面」，节点中心实测 (364,896)（零偏差）；缩放至 1.98 后在 (594,278) 新建，中心实测 (594,278)。证据：`temps/canvas-cursor-anchoring/01-node-at-cursor.png`、`02-node-at-cursor-zoomed.png` + `assertions.json`
- [x] 3.3 浏览器实测·贴边：连线菜单在锚点 x=1590（越界）时盒为 `x=1424,right=1672`；节点菜单在右下角为 `y=865.6,bottom=992`；「选择 Android 页面」列表为 `y=572,bottom=992` 且搜索框可见；元素选择器在屏内；矮窗口 1000×520 下菜单盒 `704,385.6,288×126.4`（底边 512 ≤ 520−8）；0 控制台报错
- [x] 3.4 收尾：临时验证文档已删除；用户既有文档「H6810设备页面关系流」库内节点数实测前后一致（17/17，本次实测未写入该文档）
