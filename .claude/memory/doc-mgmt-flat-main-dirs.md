---
name: doc-mgmt-flat-main-dirs
description: dev_docs采用主目录平铺+README索引，禁止多层子目录与软链兼容
type: project
---

`dev_docs/` Stage-Gate 文档约定（2026-07-10 更新）：

1. **只建主目录**，文件平铺，用前缀分类；每目录 `README.md` 索引；总入口 `index.html`。
2. **不留软链兼容**：旧路径（`01-技术架构/`、`03-产品原型/`、`04-测试方案/`、`diagrams/`、`子PRD/`）已删除，只认新路径；引用与书签须同步更新。
3. **需求文档唯一位置**：`02-PRD需求/`，固定结构 **1 总 PRD + 7 子 PRD + README**：
   - `实际需求文档.md`
   - `子PRD-{01..07}-{模块}.md`（元素定位/设备/用例/执行/报告/AI/仪表盘）
   - `README.md`
4. **方法论不落本地**：`需求矛盾分析方法`、`优秀设计` 直接写在 `index.html` PRD 阶段内嵌栏目，禁止再建对应 md/子目录。
5. **HTML 全功能规格例外**：允许 `02-PRD需求/html/` 存放**七模块**全功能 HTML 需求（`子PRD-01`～`07-*-全功能需求.html`），Markdown 主文件仍平铺；冲突以现网+HTML 为准。
6. **03-设计与架构**：对齐 PRD——`当前实现架构方案.md` 为总设计真相；全部图册/审查/原型进 `html/`；同主题角色见 `html/对比-同主题文档差异.html`。
7. **05-开发与测试例外**：允许按平台功能模块建子目录（`仪表盘/`…`AI助手/` + `平台级/`），不再用 `开发-{模块}-*` 平铺前缀；详见 `doc-mgmt-devtest-module-triad`。
8. 不管：`.claude/`、`.agents/`、`tests/`、根目录 `AGENTS.md`/`README.md`；`exports/*.yaml`、`logs/*.log`、`data/uploads` 不进文档库。
