## 1. 指针修订

- [x] 1.1 `doodle-craft` 6 处指针改指真实来源；验证：无悬空指针（保留 2 处带「已并入」说明的历史沿革提及）
- [x] 1.2 `vue-frontend-check/references/checklist.md` 模块色对照改为「本文件组件规格验收」；验证：命中 = 0

## 2. 段号与清单

- [x] 2.1 重复的「皮肤维度六 · 布局 Layout」→「皮肤维度八 · 布局 Layout（分栏 / 比例 / 断点）」；验证：序号唯一（一…八）
- [x] 2.2 文件头维度清单补上该段；验证：清单与正文标题一致

## 3. 关单

- [x] 3.1 `openspec validate fix-doc-residue --strict` 通过并归档（`skip_specs: true`）

## 关单记录（2026-09-15）

| 验证项 | 结果 |
|---|---|
| 指针替换 | `doc_patches=10 missing=0`（7 处活指针 + 2 处 tokens.css + 1 处 checklist） |
| 残留 | 活文档内**悬空指针** = 0；保留 2 处带「已并入 checklist」说明的历史沿革提及（`SKILL.md:12` / `references/layout.md:3`） |
| 段号 | 一/二/三/四/五/六/七/八 唯一 |
| 自纠 | 首轮误写「阵影」，同轮修正 `typo_fixed=true` |
| 构建 / 浏览器 | 不涉及（纯文档） |