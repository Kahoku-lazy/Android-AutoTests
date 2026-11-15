# 已踩实的坑（每条都有证据，不是传说）

本文件只收录**本仓库真实验证过**的结论：抓到过冲突、跑出过反例、或花过时间才弄明白。
新的坑请按同样格式追加（现象 → 证据 → 处理）。

## 1. `check` 为什么会连库——连库的不是 `database` 标签

[ref/checks](https://docs.djangoproject.com/en/6.1/ref/checks/) 说「database 检查默认不跑」，这句话**没说错**；
而我们实测 `check` 确实连了库。两句都对，因为**连库的是另一条路径**。这种"看起来矛盾"的地方最容易误判，
所以把两条路径拆开写：

| 环节 | 6.1.3 实际行为 |
|---|---|
| `core/checks/registry.py` L90-94 | 未指定 `--database` 时，**`Tags.database` 那组检查被过滤掉**——文档描述的就是这一条 |
| 同文件 L96-97 | 但 `databases` 被补成 `list(connections)` |
| 同文件 L99-100 | 其余检查（**含 `Tags.models`**）拿到全部别名 |
| `db/models/fields/__init__.py#L518-525` | `_check_backend_specific_checks` 只在 `databases is None` 时早退；否则逐个 alias 调 `validation.check_field` → `field.db_type()` → MySQL 后端要读服务器版本 → **建连接** |
| `db/models/base.py`（6.0.6） | `Model.check()`: `databases = kwargs.get("databases") or []` → 循环 0 次，不连库 |

实测对照（本机，同一份仓库代码）：

| 组合 | 结果 |
|---|---|
| 6.1.3 + 不可达 mysql（`DB_PORT=13306`） | `OperationalError (2002)`，exit 1 |
| 6.1.3 + `DB_ENGINE=sqlite` | `System check identified no issues`，exit 0 |
| 6.0.6 + 不可达 mysql | `no issues`，exit 0（今天 CI 仍绿的原因） |
| 6.0.6 + `check --database default` | `OperationalError (2002)`——补上别名就炸，机制同源 |

**教训**：不要从检查标签名推断谁会连库。`database` 组被过滤 ≠ 没有别的组连库；这类问题一律
「读 `registry.py` + 跑一次最小复现」定论，别只引一句文档就下结论。

**同一机制的连带效应**：因为 6.1 才把数据库别名喂给模型检查，`models.W036` 这类"依赖连接特性"的告警
在 6.0.6 上**不会出现**（实测：mysql 可达、6.0.6 跑 `check` = `no issues`；6.1.3 同环境 = 一条 W036）：

| 版本 | 位置 | 行为 |
|---|---|---|
| 6.0.6 | `django/db/models/base.py` `Model.check()` | `databases = kwargs.get("databases") or []` → `_check_constraints(databases)` 循环 0 次，约束检查空转 |
| 6.1.3 | `django/core/checks/registry.py` | `if databases is None: databases = list(connections)` → 每个别名各跑一遍 |

所以"升级后冒出来的警告"要分清是**新问题**还是**旧事实首次可见**——本例是后者：那条条件唯一约束
在 MySQL 上从来没被创建过（`migrate` 时 `_unique_supported()` 返回 False → `_create_unique_sql()` 返回
`None` → `add_constraint()` 的 `if sql:` 静默跳过）。

**这类"条件唯一约束 + MySQL"的两种修法**（形状候选，未在本仓库验证过；落地前必须真库 `makemigrations` + 实测）：

1. `GeneratedField` 辅助列 + 复合唯一：`active_key` 在 `status="active"` 时为 1、否则 `NULL`，
   再 `UniqueConstraint(fields=["device", "active_key"])`。MySQL 唯一索引允许多个 `NULL`，
   等价"仅 active 行互斥"，且 sqlite/MySQL 行为一致——测试里才有意义。
2. 表达式唯一索引：`UniqueConstraint(Case(When(status="active", then=F("device")), default=None), name=...)`。
   依赖 `supports_expression_indexes`（MySQL 8.0.13+，6.1 的 `mysql/features.py` 会该位为 True），
   代价是 Python 侧 `validate()` 变空转。

两条"不要做"：直接删 `condition` 改成纯 `(device)` 唯一（锁记录不删，第二条锁必冲突）；
用 `Meta.required_db_features = {"supports_partial_indexes"}`（MySQL 会干脆不建这张表）。

## 2. 6.1 移除了 `django.utils.cache.cc_delim_re`

DRF 3.17.2 及更早仍 `from django.utils.cache import cc_delim_re`，在 6.1 上**导入即炸**：

```text
ImportError: cannot import name 'cc_delim_re' from 'django.utils.cache'
```

- 修复在 **DRF 3.18.0**（核对过 tag：3.17.2 仍 import，3.18.0 已删）
- 陷阱：仓库里写的是 `djangorestframework>=3.15`，新装机会自动拿到 3.18.x，**问题被掩盖**；只有停在旧版本的本机环境会失败
- 处理：升 6.1 时把 DRF 显式钉到 `>=3.18`，别依赖隐式解析

## 3. 6.1 抬高了数据库门槛

| 后端 | 6.1 要求 |
|---|---|
| MySQL | **≥ 8.4**（8.0 与 8.1–8.3 均放弃） |
| MariaDB | ≥ 10.11 |
| PostgreSQL | ≥ 15（14 已放弃） |
| SQLite | ≥ 3.37.0 |
| Python | 3.12–3.15 |

升级前先 `mysql --version`；本机 8.4.4 合格，测试/生产库要单独确认。

## 4. `_sources/*.txt` 永远是英文

实测：`https://docs.djangoproject.com/zh-hans/6.1/_sources/ref/checks.txt` 与英文版**字节数相同、无 CJK**；
同路径的 HTML 页有中文。Sphinx 的 `_sources` 存的是构建源，不存译文。

**处理**：精确检索/引原文用 `_sources`；要中文措辞就读 `zh-hans/6.1/<path>/` 的 HTML，并接受它可能比英文滞后。

## 5. `ref/checks` 没有 per-check 锚点

实测该页仅 99 个 `id`，全部是章节级（`#models`、`#database`、`#mail`…），**不存在 `#models.w036`**。
写 `#models.w036` 会跳到页首，等于没定位。

**处理**：引 `ref/checks/#models` + 检查号文本；需要精确指位就用 `doc_src.py --grep` 给 reST 行号，或引源码行号。

## 6. 「用错 backend 就得出错误结论」——OpenAPI 基线

不是 Django 文档问题，但同属证据链陷阱：用 `DB_ENGINE=sqlite` 重新生成 `openspec/openapi.yaml`，
会出现 6 增 4 删的假漂移（`sort_order` 的 `maximum/minimum` 从 32 位变 64 位、多出 `format: int64`）。
根因是 sqlite 的 `integer_field_range` 返回 64 位，mysql 返回 32 位。

**处理**：生成/比对契约基线一律用 mysql 配置（与仓库基线同源）；换 backend 就重新基线，别混。

## 7. Windows 下的退出码噪音

`python manage.py check` 在只产生 **W 级警告**时退出码是 0；但 PowerShell 会把 stderr 包装成
`NativeCommandError` 并显示 `[exit code: 1]`，容易误判成失败。

**处理**：判断成败看 `$LASTEXITCODE`，或把 stderr 合并后看结尾那行
`System check identified …`；不要只看崩溃标记。

## 8. 6.1 的弃用项别当"已移除"

`select_related()` 空参、`EMAIL_*` 系列 setting、`get_connection()` 等在 6.1 是**弃用**（有 warning），
不是错误。升级后 grep 到 warning 不要顺手改成"新写法"就完事——先确认目标写法在 6.0 上是否也存在，
否则一个提交把两个版本的兼容性一起破坏了。
