## 1. 基线

- [x] 1.1 记录基线：在 `frontend/` 跑 `npm run typecheck` 与 `npm run test`，确认改动前即为绿；并确认 `frontend/tests/knowledge-search` 目录不存在（本单不需要同步既有用例）。验证：typecheck 退出码 0；test 92 文件 / 581 用例全绿；目录不存在。

## 2. 弹窗组件

- [x] 2.1 新建 `frontend/src/modules/knowledge-search/components/RetrievalSettingsDialog.vue`：`el-dialog`（宽 520px、`append-to-body`、`:close-on-click-modal="false"`、`destroy-on-close`）+ `el-form label-width="96px" label-position="left"`；字段与保存逻辑沿用卡片版（向量模型 / 默认返回条数 / 相似度阈值 / 切块大小 / 切块重叠），底部「取消 / 保存」。验证：`npm run typecheck` 通过；浏览器实测五个 label 与四个数值输入齐全。
- [x] 2.2 加载时机改为 `watch(visible)`：打开时清空 `settings` / `loadError` 并重读配置与 embedding 模型列表，加载中走 `SkeletonCard`、失败走 `ErrorState`（可重试），失败只在弹窗内显示可读原因。验证：代码中无 `onMounted` 加载；浏览器实测「保存 0.5 → 取消 → 重开」回填 0.5。
- [x] 2.3 删除 `RetrievalSettingsCard.vue`，并确认全仓无残留 import；新增文案常量 `KS_RETRIEVAL_*` 到 `constants.ts`。验证：`grep RetrievalSettingsCard frontend/src` 零命中；`npm run typecheck` 通过。

## 3. 入口接线

- [x] 3.1 `ModulePanel.vue` 去掉页面流里的检索配置卡片，在「知识模块」卡头部「新增」左侧加「配置」按钮（仅 `canManage` 可见），点击置 `settingsOpen` 为真。验证：页面 DOM 中「检索配置」标题计数 0（未开弹窗时），头部动作实测为 `["配置","新增"]`。
- [x] 3.2 弹窗以 `v-model` 绑定 `settingsOpen` 并仅在 `canManage` 时挂载；不改模块列表的选中态、`emit` 名单与「新增 / 编辑」链路。验证：`defineEmits` 与改动前一致；普通用户视图实测无「配置」「新增」且保留只读权限提示。

## 4. 门禁与验收

- [x] 4.1 前端门禁六条全过：`npm run typecheck`、`npm run lint`、`npm run lint:styles`、`npm run lint:lines`、`npm run build`、`npm run test`。验证：六条命令退出码均为 0；eslint 仅余仓库既有告警，本模块 0 error。
- [x] 4.2 `openspec validate knowledge-retrieval-settings-dialog --strict` 通过。验证：输出 `is valid`。
- [x] 4.3 浏览器验收（1440px 与 1024px）：本机 MySQL 离线，故用已在跑的 dev server（:5173）+ Playwright 路由打桩（mock `auth/me`、`modules`、`settings`、`model-configs`）验证四项场景——页面无检索配置卡片、头部「配置」「新增」并列、点「配置」出弹窗且回填当前值、只改阈值提示「检索配置已保存」/改切块提示需重建索引、点遮罩不关闭而 ESC 与取消可关闭、普通用户看不到两按钮。验证：截图 `temps/ks-01-page.png`、`temps/ks-02-dialog.png`、`temps/ks-03-saved.png`、`temps/ks-04-1024-superuser.png`、`temps/ks-05-non-superuser.png`。
