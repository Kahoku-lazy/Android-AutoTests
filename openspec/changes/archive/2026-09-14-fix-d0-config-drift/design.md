## Context

- 4 项现象的实测证据见 proposal「Why」表格；其中 #5 的因果链是「`DOCKER_CONTAINER` 无任何设置方 ⇒ 分支不可达 ⇒ `LOGGING` 未定义 ⇒ 应用 INFO 日志无 handler」。
- `config/api_docs.py` 目前是 `/api/docs` 与 `/api/docs.html` 的数据源（`config/urls.py:15-16`），且 `/api/docs` 是**用户裁定保留公开**的端点 → 不能直接删除，只能「修正 + 加机检」。
- `config/env.py` 需被 `run.py`（仓库根脚本，`sys.path[0]` 即仓库根）与 `config/settings.py` 同时复用，且不得引入 Django 依赖（`run.py` 在 Django 之外先加载 `.env`）。

## Goals / Non-Goals

**Goals:**

- D0 内「配置声明」与「实际生效」一致：删掉从未生效的键、让日志配置真的生效、让两份重复的 `.env` 解析合一、让手写 API 文档不再能默默漂移。

**Non-Goals:**

- 不重写 `api_docs.py` 的内容结构，不改 `/api/docs` 的公开策略与 HTML 呈现；
- 不引入 `python-dotenv` 等新依赖（保持零依赖实现）；
- 不动 `apps/` 业务代码、不动 schema 告警（另单）。

## Decisions

**D1 #4 删除 `custom_css`，而不是补一个空 CSS 文件。**
理由：键的唯一作用是引用一个不存在的资源；补空文件会把「无效引用」变成「看似有效但无内容」的更大迷惑。字体覆盖若确有需求，应按主题规范新增真实文件并单独评审。

**D2 #5 `LOGGING` 始终定义，按「本地文件 / 容器 stdout」分档，级别由 `LOG_LEVEL` 控制。**
理由：日志是排障基础设施，不应依赖一个从未被设置的变量；`DOCKER_CONTAINER` 保留为「输出目标」的选择器而非「是否配置」的开关。
备选：只在 `settings` 里 `logging.basicConfig` —— 与 Django 的 `LOGGING` 机制重复，不取。

**D3 #6 保留手写文档 + 双向一致性测试（不立即改由 schema 渲染）。**
理由：`/api/docs` 是公开文档页，其内容比自动 schema 更可读（含中文说明与请求示例）；立即替换会丢失信息且被 schema 告警单阻塞。加测试后「漂移」从静默变为失败，足够阻止再次腐烂。
备选：删除 `api_docs.py` 改渲染 schema —— 依赖 schema 补齐单（155 条告警），且丢中文说明，登记为后续决策。

**D4 #7 `config/env.py` 提供 `load_dotenv()`，语义严格沿用现有实现（不覆盖已存在的 `os.environ` 键）。**
理由：收敛重复实现的同时**不改变**任何加载语义（先到先得：真实环境变量优先于 `.env`），避免把「清理重复」变成「改变行为」。
风险点：引号处理两版不一致，统一时必须选一个——选「先 `strip\`"` 再 `strip\`'\`」的当前 settings 版本，并在用例里覆盖 `KEY="v"` / `KEY='v'` / `KEY=v` 三种写法。

## Risks / Trade-offs

- [#5 让日志生效后，本地控制台输出变多] → 级别默认 `INFO` 且可用 `LOG_LEVEL` 调整；不改变业务日志内容。
- [#6 一致性测试可能与「DRF router 动态生成路径」冲突导致误报] → 测试只比对**静态 `path()` 条目**（与 `gen_arch_stats.py` 同口径），并在用例注释说明 router 展开不计；已知偏差（如 case_manager 的 router 路径）在文档里显式列为「不在本文档收录范围」。
- [`api_docs.py` 修正条目时可能误删仍在用的端点] → 测试是双向的（文档 → 代码、代码 → 文档），由用例兜底。
- [`.env` 解析收敛改变边缘行为] → D4 明确「语义不变 + 三写法用例」。
