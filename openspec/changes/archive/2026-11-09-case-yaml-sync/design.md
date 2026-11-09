## Context

现状见 [proposal.md](./proposal.md) - Why。三条既有约束决定了实现形状：

1. 用例库的步骤表 `cm_case_steps` 只有 `action` / `assertion` 两列，用例表格与步骤抽屉据此渲染。
2. 执行链只吃「一份 YAML 文件」：任务提交把上传件存成 `kind=config` 的附件，`task_runner` 调 `materialize_config_file` 落成临时文件后交给 `engines.agents.workflow.platform_run.run_platform_sop`。
3. 引擎侧的 YAML 解析在 `engines/agents/workflow/case_file.py`，`anchor` / `log` 的合法性与长度规则已经写在那里（`ANCHOR_KEYS`、`ANCHOR_VALUE_MAX`、`KEYWORDS_MAX`、`_KEYWORD_PATTERN`）。

H6810 目录实测：7 份 YAML、56 条用例、167 步；只有 `H6810_structured_cases.yaml` 带 `anchor`（47 步）与 `log`（8 步），`H6810_ui_only_cases.yaml` 带 `anchor`（45 步）；标题跨文件大量重复（「H6810 定时功能测试」在 4 份文件里各有一份）。

## Goals / Non-Goals

**Goals**

- 本地目录与用例库之间的同步可重复执行，结果可核对（新建/更新/删除/跳过分别计数）。
- 平台用例执行与本地 YAML 执行拿到的引擎输入等价（同样带 `anchor` / `log`）。
- 不新增第二条执行路径：引擎、提示词、SOP 编排零改动。

**Non-Goals**

- 不做双向实时同步（平台侧改动不回写本地 YAML）。
- 不做后端扫描任意本机目录的接口（目录同步只经命令行）。
- 不把 `anchor` / `log` 做成「可编辑的独立字段」——本期只在步骤抽屉里只读展示，编辑仍以 YAML 导入覆盖为准。
- 不改变已有用例行与历史任务。

## Decisions

### D1 执行提示存成步骤行的两个 JSON 列，而不是拼进动作文本

`cm_case_steps` 增 `anchor`（JSON，默认 `{}`）与 `log`（JSON，默认 `{}`）。

- 备选 A：拼进 `action` / `assertion` 文本——会污染表格与预览，且 2000 字校验、去重、比对都要跟着改，回滚困难。
- 备选 B：另建 `cm_case_step_hints` 表——多一次 join，收益只有「空值不占列」，而 JSON 列本身已能表达空。
- 选 A/B 的反面（JSON 列）：读写路径与现有步骤序列完全同构，`_replace_steps` 只需多带两个字段。

### D2 目录同步：一份 YAML 一张表，按标题幂等 upsert

- 表名取文件在目录内的相对路径（`01/h6810-short-card` → `01 / h6810-short-card`），保留变体与来源；跨文件同名标题被表隔开。
- 行匹配键为标题：存在则覆盖（字段 + 步骤整段替换），不存在则新建。**不按 `source_case_id`**，因为 H6810 只有 `01/case.yaml` 有编号。
- 默认不删除「YAML 中已消失」的行（人工补录的行不应被同步洗掉），`--prune` 显式开启。
- 之所以放在命令行：后端不应提供「读本机任意路径」的接口，这是权限与可审计问题。

### D3 平台用例执行 = 生成 YAML 附件，复用既有 SOP 入口

任务提交增加 `case_source` 与 `case_ids`；后端用 `case_manager` 的导出函数生成 YAML 文本，按现有 `PreparedUpload(kind="config")` 落附件（`stored_path=""`，`materialize_config_file` 会走「正文写临时文件」分支）。

- 备选：给 `run_platform_sop` 增加「直接吃用例对象」的入参——要在引擎里新开分支、改签名与测试，收益只是省一次 YAML 序列化。
- 备选：前端把平台用例下载成 YAML 再自己上传——多一步人工操作，且「平台用例」与「本地 YAML」在界面上没有区别。

### D4 提交用 `case_ids` JSON 数组字符串，而不是重复表单键

multipart 下重复键在 DRF `ListField` 的解析行为依赖解析器细节，容易踩坑；`case_ids='["TC-...","TC-..."]'` 在序列化层一次解析、错误信息可控。`case_source` 缺省为 `yaml`，保证老前端/脚本不受影响。

### D5 执行提示校验复用引擎规则，后端不复制常量

在 `case_file.py` 增加公开入口 `parse_step_hints(anchor, log)`，返回可入库的纯字典与失败原因；后端 `api_definitions` 与 `api_yaml` 都只调它。避免 `ANCHOR_KEYS`、`KEYWORDS_MAX` 这类规则在 backend 出现第二份。

### D6 网页导入与目录同步共用同一个落库函数

`api_yaml.import_yaml_text(...)` 是唯一写入口；管理命令负责「遍历目录」，接口负责「校验归属 + 读上传件」，两者都调它。

### D7 前端平台用例选择器：项目 → 文件 → 用例三级，数据源复用既有只读接口

项目用 `GET /cases/projects/`，文件用例用 `GET /cases/files/{id}/`（已返回每行标题与步骤数）。不新增「用例搜索」接口，本期选择规模是「一张表十几条」。

## Risks / Trade-offs

- [执行提示在人工编辑步骤时被清空] → 前端 `toSteps()` 透传 `anchor` / `log`，后端 `_normalize_steps` 也保留；单测锁住「编辑动作文本后执行提示仍在」。
- [同步覆盖人工修改] → 覆盖语义写进结论（新建/更新分别计数）；默认不删行，误覆盖可用 `--prune` 前后的差异核对。
- [同名标题跨文件造成选择器里看起来重复] → 选择器以「文件」为单位展示，标题重复被文件隔开；导出与执行都按 `case_ids`，不存在歧义。
- [YAML 往返后格式不同（缩进、引号、键顺序）] → 只保证语义等价（标题、步骤、anchor、log 内容一致），不承诺字节级一致；单测按 `yaml.safe_load` 结构比对。
- [大文件导入拖慢请求] → 沿用 20MB 上限与逐表写入；H6810 最大一份 22KB / 13 条，不构成风险。

## Migration Plan

1. 新增迁移（`cm_case_steps` 两列 JSON，默认 `{}`），对旧行无回填、无阻塞。
2. 代码上线后旧前端仍按 `case_source` 缺省走本地 YAML，行为不变；新前端切成两份来源。
3. 执行 `python manage.py import_case_yaml --dir D:\Govee\data\H6810 --project H6810 用例库` 完成首次同步；重复执行即幂等校正。
4. 回滚：删除新增列与前端入口即可，已导入的用例行是普通用例行，不影响执行链。

## Open Questions

- 无（本期范围与交互已在讨论中确定）。
