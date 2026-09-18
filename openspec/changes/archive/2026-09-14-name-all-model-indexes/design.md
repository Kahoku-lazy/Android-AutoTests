## Context

动机与清单见 `proposal.md` - Why。与 `stabilize-drifted-index-names` 同一根因，区别是那单处理**已经报错**的 3 处，本单把剩下的 5 处一次锁死，避免下一批漂移。

## Goals / Non-Goals

**Goals:**

- 全仓 `models.Index` 都有显式 `name=`，索引名不再随 Django 哈希变化漂移
- 补名过程中 `makemigrations --check` 保持 exit 0（证明零 DDL）

**Non-Goals:**

- 不改索引字段或新增/删除索引（纯命名）
- 不给 `Meta.constraints` 的 `UniqueConstraint` 改名（它们本就有显式 `name=`）
- 不引入自定义命名规范（如统一前缀规则）——沿用 Django 计算名即迁移状态名

## Decisions

### 1. 名字取 Django 当前计算名

- **选择**：直接写 `idx.name`（取证脚本从 Django 注册表读出）
- **理由**：`makemigrations --check` 绿 ⇒ 计算名 = 迁移状态名 ⇒ 写进去不产生任何 DDL；这是唯一能同时「锁定名字」和「零风险」的取值
- **备选**：另取一套更可读的名字 → 会生成 5 个 rename 迁移（真实 DDL），否决

### 2. 用 AST + Django 双源取证，而不是 grep

- **选择**：AST 找 `models.Index(...)` 调用点（判断有无 `name` kwarg），Django 注册表取计算名
- **理由**：grep 无法可靠区分「多行写法里已有 name」与「没有」；AST 是权威且与 ruff 格式化无关

### 3. 取证脚本放 `temps/`，跑完删除

- **选择**：`temps/d0_index_scan.py`（仓库约定：临时件入 `temps/`）
- **理由**：一次性取证工具，不入库；删掉避免留下无消费者的脚本

## 模块防火墙自检

- 跨模块写库：不涉及（只改模型 Meta 声明）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [名字写错 → 产生真实 rename DDL] → 名字由脚本从 Django 注册表读出（非手抄），并以 `makemigrations --check` 归零作判据
- [与并行修改同文件的改动冲突] → 三个文件逐个读取后立即改，改完立刻用 git diff 复核仅索引名行变化

## Migration Plan

1. 跑取证脚本拿到 5 处清单与计算名
2. 三个文件分别补 `name=`
3. `makemigrations --check` 必须仍 exit 0；`manage.py check` / `ruff` / unit 全量回归
4. 删 `temps/d0_index_scan.py`；归档；回滚 = `git checkout` 三个 models.py
