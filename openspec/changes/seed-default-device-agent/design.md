## Context

- 智能体是数据库行（`ai_agents`），不在源码里；唯一的历史种子是迁移 `0061`，只种了 `Agent-02`（`case_authoring`）。
- 现有环境的设备执行智能体（本机为 `Agent-01号`，`task_kind=device_control`）是早年手工建的运行时数据，仓库里没有任何创建路径。
- `0061` 取「迁移时刻的第一个超级管理员」作为 owner；而 `README` 的标准顺序是 `migrate` → `createsuperuser`，干净库上必然取不到超管。
- 可见性规则集中在 `api.filter_agents_for_user`（列表）与 `permissions.check_agent_visible`（提交/详情），两处都对 `owner_id IS NULL` 判否。
- 任务装配已与 `route_configs` 解耦（`task_list/engine_adapter.py` 只解析设备 serial），模型与工具写死在 `engines.agents`，所以种子里不需要任何密钥。

## Goals / Non-Goals

**Goals:**
- 全新环境迁移完即同时具备设备执行与用例编写两类默认智能体，零手工步骤。
- 种子结果与「先 `migrate` 还是先 `createsuperuser`」完全无关。
- 对新旧库都幂等：已有设备执行智能体的库不新增、不改写。

**Non-Goals:**
- 不改 `Agent-02` 的既有种子与字段。
- 不引入 `is_shared` 之类的新字段（本轮用「无主 = 共享」表达）。
- 不做历史数据的智能体去重或改名。
- 不动前端看板与任务提交页面。

## Decisions

### 种子放在数据迁移里，不放管理命令
迁移随 `migrate` 自动执行，满足「随代码走」；管理命令需要人记住多跑一步，正是这次问题的成因（README 之外的口头约定）。反向迁移只删除本迁移自己创建的那一行，避免误删人工数据。

### 幂等键用 `task_kind`，不用名称
现存机器上的行叫 `Agent-01号`，按名称判定会在这些库上再种一条重复的。改为「库中已存在任意 `task_kind=device_control` 的智能体即跳过」，既覆盖历史手工行，也覆盖人工改名的情况。

### 「无主 = 平台共享」下沉到可见性层
迁移时点不可控，所以不能让语义依赖 owner 一定非空：
- `filter_agents_for_user`：普通用户集合加入 `Q(owner_id__isnull=True)`；
- `check_agent_visible`：`owner_id` 为空直接判可见。
备选方案「`post_migrate` 信号/首次登录补种」被排除：隐式副作用、跨进程时序不稳定、难写单测。

### 迁移里顺带回填历史无主行
存在超管时把 `NULL` owner 回填为首个超管 id，让旧库逐步收敛到显式归属；无超管时保持为空，由上面的规则兜底，迁移不因此失败。回填只动 `owner_id` 一列。

### 种子字段取值
`name=Agent-01号`、`avatar=🤖`、`model_provider=deepseek`、`model_name=deepseek-flash`（与 `0062` 对齐）、`task_kind=device_control`、`route_configs={"device_control": {"name": name, "avatar": avatar}}`——最后一项是卡片显示源，与 `api.create_agent` 的写法保持一致。

## 模块防火墙自检

- 跨 App import：迁移内只经 `apps.get_model` 读 `auth.User`（Django 内建 Model，只读），未 import 其他 App 的 service/runner。
- 写操作：迁移自带 ORM 写 `ai_assistant` 自己的表；业务写路径仍收敛在 `api.py`，本次不新增业务写接口。
- 前端：零改动，不直连数据库。
- 依赖方向：`task_list` → `ai_assistant` 只读关系不变；未新增反向依赖。

## Risks / Trade-offs

- [无主即共享放大了可见范围] → 只影响 `owner_id IS NULL` 的存量行；写权限仍仅超管；若日后要区分「平台共享」与「孤儿数据」，用显式字段替换该规则。
- [迁移写入了数据] → 反向迁移按 `task_kind` 精确删除本迁移创建的那一行，并在删除前跳过已挂任务的智能体。
- [与 `0061` 的 owner 逻辑重复] → 不回改已应用的迁移（历史库不会重放），由新迁移统一处理回填。
