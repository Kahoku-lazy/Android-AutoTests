## 1. 入口重写

- [x] 1.1 `SKILL.md` 重写为入口式版式：frontmatter（name / description 保留并轻修）+ 一段话定位 + 默认设计口径（强制 5 条）+ 先选场景表 + 一段话说清风格 + 设计令牌（分组 / 何时用 / 指针）+ 组件目录（类目表 + 选型判据表）+ 硬规则（编号，违反即 bug）+ 提交前自检。验证：`SKILL.md` = 129 行（≤150），旧版仍在入口的字段（8 模块色、侧栏图标映射、验证命令、自检项）逐项可追溯——侧栏图标映射下沉到 `components/layout.md`，其余留在入口
- [x] 1.2 硬规则按「工具能判定 / 只能人工判定」分述，工具可判定的注明门禁编号（`npm run lint:styles` G1–G5）。验证：G1–G5 与规则逐条对应（规则 1→G1/G2、2→G5、4→G4、5→G4、6→G3），无遗漏无杜撰

## 2. 场景参考

- [x] 2.1 新增 `references/vue-project.md`：平台内 Vue 场景的落地路径（四层不越界的落点表、L0–L5 判层、改 EP 全局覆盖 vs 模块 `:deep()`、取数与三态、验证与门禁命令、与 `frontend/AGENTS.md` / `vue-frontend-check` 的分工、验收契约清单）。验证：文件内命令与路径真实存在
- [x] 2.2 新增 `references/standalone-html.md`：单文件 HTML 场景（`:root` 令牌子集模板、页面骨架、按钮/卡片/表格/表单/三态/弹窗配方、交付前自检）+ 两条实测踩坑（未声明 `var()` 致 SVG 描边消失；滚动落在 `.main__body` 而非 window）。验证：配方取自本次实际产出的预览页，浏览器渲染正常

## 3. 组件规格拆分

- [x] 3.1 拆出 `references/components/general.md`（EP Button 与 `wb-btn` 变体、DoodleBtn、ConfirmButton、Tag）
- [x] 3.2 拆出 `references/components/layout.md`（WorkbenchHeader、WorkbenchCrumbs、AppSidebar + Lucide 图标映射、`.doc-section`、AppTabs / FilterTabs）
- [x] 3.3 拆出 `references/components/cards.md`（AppCard、裸 el-card 覆盖、SketchCard、KpiCard、DoodleNote）
- [x] 3.4 拆出 `references/components/form-controls.md`（Form/Input、Select、Cascader、el-radio-button 分段控件、el-switch、Tabs 指向）
- [x] 3.5 拆出 `references/components/data-display.md`（Table EP 皮肤、AppTable 表纸、usePagination 分页）
- [x] 3.6 拆出 `references/components/overlays.md`（Dialog / Drawer、ElMessageBox 确认框口径）
- [x] 3.7 拆出 `references/components/feedback.md`（SkeletonCard、ErrorState、EmptyState、el-message、el-alert、原地异步）
- [x] 3.8 拆出 `references/components/decorative.md`（PaperDoodles、微旋转机制、图钉/胶带、阴影与圆角边界）
- [x] 3.9 删除旧的 `references/components.md`。验证：旧文件 23 个组件标记（脚本比对 32 项关键词）100% 命中，六个小节全部归位（一→general/cards/…、二→八类目、三→SKILL.md 选型判据、四→tokens.md §1.9、五/六→known-gaps.md）

## 4. 旧参考归位

- [x] 4.1 `references/layout.md` → `references/page-layout.md`（git 识别为重命名），头部加"令牌值以 tokens.css 为准 + 相邻参考"指针，§4.3 微旋转机制下沉到 `components/decorative.md` 只留页面侧要求，其余内容保留
- [x] 4.2 `references/tokens.md` 头部补检索表定位与相邻参考；原 `components.md` §四「动效与降级」并入 §1.9（已降级 / 未降级两张清单）；新增 §1.17「Element Plus 变量映射（41 条）」
- [x] 4.3 新增 `references/known-gaps.md`：收纳原 `components.md` §五「已知缺口登记」（5 条）与 §六「已退役 / 不存在」（8 条）
- [x] 4.4 顺带校正门禁编号：重组时发现 `tokens.md` §1.15 的 G1–G5 表与代码不符（代码里 G4 = 引用完整性、G3 = 模块家族令牌前缀、阴影/圆角/动效 = G12/G13/G14，字号下限属"批 1"且无 G5）。按「以代码为准」把该表改齐，`SKILL.md` 硬规则里的门禁引用同步为真实编号。验证：逐条对照 `frontend/tests/check-style-gates.mjs` 的标签注释

## 5. README 与校验

- [x] 5.1 新增 `README.md`：技能是什么、谁读它、目录结构树、怎么用、维护规则（改令牌先改 `tokens.css` 再同步；新增类目先登记；仓内其它技能只按技能名引用）
- [x] 5.2 链接校验：脚本遍历技能内全部 `.md`，64 条相对链接 0 悬空
- [x] 5.3 残留校验：技能内不再出现 `references/components.md` / `references/layout.md` 旧路径（0 处）；全仓对该技能的引用仍为技能名引用，无深链
- [x] 5.4 行为零变更：本次未触碰 `frontend/`（工作区里 `frontend/src` 下已有的改动属于上一个变更 `render-planner-input-as-json-block`，与本单无关）
