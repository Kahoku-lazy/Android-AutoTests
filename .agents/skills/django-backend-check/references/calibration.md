# 判罚量规与例外（防同 skill 结果漂移）

> 与 `vue-frontend-check/references/calibration.md` 对位：强制统一 🔴/🟠/🟡 与 ✅ 口径。

## 1. 验证方式必须声明

每份报告开头写：

```text
验证方式: 静态扫描 | 静态+pytest | 静态+curl/手工
```

| 项 | 仅静态时 | 静态+pytest / curl |
|----|----------|---------------------|
| 一.1～一.4 工具层 | 必须实跑命令；未跑不得 ✅ | 同左 |
| 三.x 写库/防火墙 | 静态 rg + 读代码可 ✅/❌ | 同左 |
| 四.x 接口 | 可读 urls/Serializer 标 ⚠️ | 相关 `pytest -m api` 或 curl 后可 ✅ |
| 六.x 测试 | 未跑不得 ✅；最多 ⚠️ | 跑过相关 marker 可 ✅ |

**关单**：用户要「关单/完成」时，一.1～一.4 必须绿；涉及写库/HTTP 时六.2 或等价手工验证必须完成。纯「静态体检」须在结论标明「不可单独作为关单依据」。

## 2. 严重度量规（不得凭感觉升降）

| 严重度 | 必须归入的情形 |
|--------|----------------|
| 🔴 | `manage.py check` 失败（Error）；漏 migration 致模型与库不一致；跨 App ORM 写；跨 App import service/runner/state_machine/consumer；写操作空 except/pass 吞错；响应信封错误（缺 status / 假成功；**已登记 legacy 平铺特例除外**，见 `apps/CLAUDE.md` §1.3）；api 收 request 或对外返回 Model 导致封装破坏；dashboard 写库；主路径接口 500/契约字段名与调用方不一致且必现失败 |
| 🟠 | `ruff check` 失败；公开 api 无类型注解且为新增/改签名；views 明显超 300 行仍堆业务；错误文案含技术词（§5）；WS Consumer 未进 `gateway/routing.py`；Serializer 与 Model 字段不同步但尚未证必现挂；写库在 views 但同 App 未抽 api（收敛违规）；`makemigrations --check` 告警未处理 |
| 🟡 | `ruff format` 未过；`var` 级风格债；文件接近上限未超 1.5 倍；docstring 缺失；测试覆盖不足但主路径有手工验证；`--check-boundaries` 历史债非本次引入（须注明） |

**禁止**：把跨模块写库 / 静默吞错写操作判成 🟡；禁止未跑 §7 命令对一.x / 二.1 下 ✅。

## 3. system check 警告例外

| 警告 | 口径 |
|------|------|
| `staticfiles.W004`（STATICFILES_DIRS 目录不存在） | 应建 `static/`（或改 settings）；未处理 → 🟠；已建 → ✅ |
| `--deploy` 下 DEBUG/SECRET 类 | 本地开发可记 🟡 债；不得用「deploy 有警告」单独判关单失败，除非用户要求生产口径 |
| 其它 Warning | 默认 🟠；确认无运行影响且非本次引入 → 可 🟡 并写明 |

`check` 出现 **Error** → 一律 🔴，一.1 = ❌。

## 4. 文件行数阶梯（与 python-code.md 对齐）

| 文件 | 上限 | 超 1.5× | 超 2× |
|------|:----:|:-------:|:-----:|
| `urls.py` | 200 | 🟠 禁止纯新增 | 🔴 只允许拆分 |
| `views*.py` | 300 | 🟠 | 🔴 |
| `api.py` / `service.py` | 400 | 🟠 | 🔴 |
| executor / adapter | 500 | 🟠 | 🔴 |
| `models*.py` | 不限 | — | — |

未超上限但本次又 +50 行且已近上限 → 🟡 提醒下个 PR 拆分。

## 5. 错误文案技术词黑名单

出现在**对用户返回的 message** 则至少 🟠（四.5）：

`traceback`、`IntegrityError`、`OperationalError`、`localhost`、`127.0.0.1`、原始 SQL、绝对文件路径、`SECRET`、堆栈片段、`status code` 英文框架句。

兜底：「操作失败，请稍后重试」/ 业务可读原因（如「名称已存在」）。

日志里可以保留技术细节；**禁止**把日志原文直接塞进 JSON `message`。

## 6. api.py 契约硬规则

违反任一条 → 至少 🟠；导致跨模块耦合或写路径分裂 → 🔴：

1. 跨模块可调用函数必须出现在 `__all__`
2. 不接收 `request` / `HttpRequest`
3. 不返回 `JsonResponse` / DRF `Response`
4. 不返回 ORM Model / QuerySet（返回 dict / list[dict] / 简单类型）
5. 写操作校验与状态检查在 api 内完成

## 7. 强制扫描命令（清单第二节前必跑）

在仓库根目录，`<scope>` 默认为本次改动涉及的 app 路径（可多路径）：

```bash
python manage.py check
python manage.py makemigrations --check
ruff check apps/ config/ gateway/ shared/ models/
ruff format --check apps/ config/ gateway/ shared/ models/

# 范围扫描（按改动收窄）
rg -n "\.objects\.(create|bulk_create)|\.save\(|\.delete\(|\.update\(" <scope>
rg -n "from apps\.\w+\.(service|state_machine|runners?|consumers?)\b|import apps\.\w+\.(service|state_machine)" apps/
rg -n "except.*:\s*pass|except\s*:\s*$" <scope>
rg -n "JsonResponse\(|\bstatus\b" <scope>
rg -n "def \w+\(.*request" apps/*/api.py

# 涉及跨模块或架构变更时
python tools/gen_arch_stats.py --check-boundaries

# 关单且改了逻辑/接口时
pytest -m "unit or integration" <相关 tests 路径>
# 改了 HTTP 再加：
# pytest -m api <相关路径>
```

未跑 `check` / `ruff check` 不得对一.1 / 一.3 / 二.1 下结论。  
未跑边界扫描不得对「跨模块无违规」下 ✅（可写 ⚠️ 未扫）。

## 8. 输出必须含三块（缺一不可）

1. **缺陷汇总表**（仅失败/风险项）  
2. **逐项扫描记录**（一～七适用项：✅ / ⚠️ / ❌ / N/A + 一句备注）  
3. **结论**（通过口径 + 验证方式 + 阻塞项）

只写缺陷表、不写逐项记录 → **不合规输出**，须补全后再给结论。
