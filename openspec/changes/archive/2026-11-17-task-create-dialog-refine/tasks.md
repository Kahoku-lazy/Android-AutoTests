## 1. 弹窗布局

- [x] 1.1 弹窗宽度 640 → 900，标题栏沿用 el-dialog；表单项改 label-position=top。验证：CDP 截图确认。**验证结果**：通过。
- [x] 1.2 双栏：.task-create-grid 左 360px / 右自适应；右侧列承载 PlatformCasePicker 或执行方式提示，窄屏 <980px 回退单栏。验证：build 17.7s。**验证结果**：通过。
- [x] 1.3 设备字段移出 v-else 分支，两种来源都可见；本地 YAML 的配置/指定用例保留在左列。验证：	ests/task-list 162 passed。**验证结果**：通过。

## 2. 门禁

- [x] 2.1 ue-tsc / uild:check / itest tests/task-list / lint:lines / lint:styles。验证：全绿。**验证结果**：tsc 0；build 17.7s；162 passed；批 2 通过；虚线 0 处。
