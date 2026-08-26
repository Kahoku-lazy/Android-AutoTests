---
name: boundary-check
description: |
  模块边界检查 — 扫描跨模块 import、防火墙违规、直接 ORM 写入、文件体积超标。
  架构师每次审查代码时的标准检查工具。
  Keywords: 边界检查, 防火墙, 跨模块写入, 文件体积, boundary check, firewall check, 耦合度
  Trigger: 架构审查时、代码变更涉及跨模块时、PR 提交前质量门禁时。
---

# Boundary Check — 模块边界快速检查

**目的**: 在代码变更后、提交前，快速扫描是否违反了三道防火墙和模块边界规则。

**能力模型**: 扫描(Scan) → 诊断(Diagnose) → 报告(Report)

## 触发条件

| 场景 | 触发方式 |
|------|---------|
| 每次 Edit/Write 操作 | check-boundary 门禁（原 Claude hook，DSH 事件门禁待建） |
| 涉及 `apps/` 下文件的变更 | architect agent 调用此 skill |
| 提交前的质量门禁 | developer agent 的 auto-dev 流程中调用 |
| 架构审查 | `architecture-review` skill 的 Phase 2 调用 |

## 检查维度

### 一、防火墙 #1 — service.py 互不 import

```
规则: 禁止跨 App import service 模块
检查: grep -rn "from apps\." apps/ --include="*.py" | grep -v "models\|api\|urls\|views\|consumers\|migrations"
判定: 任何命中 → 违规
```

### 二、防火墙 #2 — 写操作走 api.py

```
规则: 跨 App 写（save/update/create/delete）必须通过 api.py 函数
检查: 对每个跨 App import Model 的文件，扫描 .save() / .update() / .create() / .delete()
判定: 在非 api.py 中直接 ORM 写入其他 App 的表 → 违规
```

**已知违规（技术债，已记录，不阻塞）**：
- `apps/test_runner/state_machine.py:278-293` — Device.status 直接修改 + DeviceLock.update()
- `agentscope_service/tools/task_tools.py:141,427,438,585` — TestSOP.create(), TestRunRecord.create(), sop.save(), record.save()

### 三、防火墙 #3 — 外部只走 HTTP API

```
规则: 外部服务不能直接 import Django 内部模块
检查: grep -rn "from apps\." agentscope_service/ gateway/ --include="*.py"
说明: AgentScope 同进程调用是设计决策，不属于违规。此处仅记录依赖关系。
```

### 四、防火墙 #4 — 不 import 他模块内部实现

```
规则: 禁止跨 App import views/service/runner 等内部文件
检查: grep -rn "from apps\.[a-z_]*\.\(views\|service\|runner\|callbacks\|state_machine\|executor\) import" .
判定: 任何命中 → 违规
```

**已知违规**：
- `apps/dashboard/views.py:100` — `from apps.test_runner.runner import _active_runs`
- `agentscope_service/tools/runner_tools.py:6` — `from apps.test_runner.runner import TestRunner`
- `agentscope_service/tools/runner_tools.py:7` — `from apps.test_runner.callbacks import TestRunnerCallback`

### 五、文件体积

```
规则: .py ≤ 400 行, .vue ≤ 500 行
检查: find . -name "*.py" -exec wc -l {} \; | awk '$1 > 400'
      find . -name "*.vue" -exec wc -l {} \; | awk '$1 > 500'
判定: 任何命中 → 标记需拆分
```

### 六、模块结构完整性

```
规则: 每个 Django App 必须有 models.py / views.py / api.py / urls.py
检查: for app in apps/*/; do for f in models.py views.py api.py urls.py; do
        [ -f "$app/$f" ] || echo "MISSING: $app$f"; done; done
判定: 缺失任何文件 → 标记需补齐
```

### 七、新增跨 App import 检测

```
规则: 每次变更不应无故新增跨模块依赖
检查: git diff 中新增的 "from apps.{其他app}" 行
判定: 新增跨模块 import 且未在 api.py 中 → 需要架构师 review
```

## 工作流

### 快速扫描（hook 触发，<2 秒）

```bash
# 只检查本次变更的文件
CHANGED_FILES=$(git diff --name-only HEAD)
for f in $CHANGED_FILES; do
  # 检查是否新增跨模块 import
  git diff HEAD -- "$f" | grep "^+from apps\." && echo "⚠️  $f: 新增跨模块 import"
  # 检查是否直接 ORM 写入
  git diff HEAD -- "$f" | grep "^+.*\.save()\|^+.*\.update()\|^+.*\.create()" && echo "⚠️  $f: 新增直接 ORM 写入"
done
```

### 完整扫描（architect 调用，~30 秒）

```bash
# 1. 防火墙检查
echo "=== 防火墙 #1: service 隔离 ==="
grep -rn "from apps\." apps/ --include="*.py" | grep -v "models\|api\|urls\|views\|consumers\|migrations\|__init__"

echo "=== 防火墙 #4: 内部实现隔离 ==="
grep -rn "from apps\.[a-z_]*\.\(views\|service\|runner\|callbacks\|state_machine\|executor\|adapter\) import" apps/ agentscope_service/ --include="*.py"

echo "=== 文件体积 ==="
find apps/ -name "*.py" -exec wc -l {} \; | awk '$1 > 400 {print $2, $1" 行 (超标 "$1-400")"}'
find frontend/src/ -name "*.vue" -exec wc -l {} \; | awk '$1 > 500 {print $2, $1" 行 (超标 "$1-500")"}'

echo "=== 模块结构完整性 ==="
for app in apps/*/; do
  name=$(basename "$app")
  for f in models.py views.py api.py urls.py; do
    [ -f "$app/$f" ] || echo "MISSING: $name/$f"
  done
done

echo "=== 跨 App import 依赖图 ==="
for app in apps/*/; do
  name=$(basename "$app")
  echo "[$name]"
  grep -rn "from apps\." "$app" --include="*.py" | grep -v "apps/$name/" | grep -v migrations | sed 's/.*from apps\.\([a-z_]*\)\..*/\1/' | sort -u | while read dep; do
    [ "$dep" != "$name" ] && echo "  → $dep"
  done
done
```

## 输出格式

```
🔍 边界检查报告 — {timestamp}
─────────────────────────────
防火墙 #1 (service 隔离):  ✅ 通过 / ⚠️ N 处违规
防火墙 #2 (写走 api):     ✅ 通过 / ⚠️ N 处违规（含 M 处已知）
防火墙 #3 (外部走 API):   ✅ 通过 / ⚠️ N 处跨边界调用
防火墙 #4 (内部隔离):     ✅ 通过 / ⚠️ N 处违规
文件体积:                 ✅ 通过 / ⚠️ N 个文件超标
模块结构:                 ✅ 通过 / ⚠️ N 个文件缺失
新增依赖:                 ✅ 无新增 / ⚠️ N 条新增跨模块 import
─────────────────────────────
总评: 🟢 健康 / 🟡 需关注 / 🔴 需修复
```

## 关联文件

| 文件 | 说明 |
|------|------|
| `android-autotests-rules/references/api-conventions.md` | 三道防火墙完整规则 |
| `android-autotests-rules/references/conventions.md` | 文件行数上限 |
| check-boundary 门禁（原 Claude hook，DSH 事件门禁待建） | 每次 Edit/Write 自动触发 |
