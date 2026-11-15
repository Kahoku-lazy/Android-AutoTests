# 问题类型 → URL 族（Django 6.1）

先判断你在问哪一类，再决定抓哪种页面。抓错族会得到"看起来相关但答不上"的内容。

## 版本前缀

| 用途 | 前缀 |
|---|---|
| 英文正文 | `https://docs.djangoproject.com/en/6.1/` |
| 中文正文（HTML 才有译文） | `https://docs.djangoproject.com/zh-hans/6.1/` |
| reST 原文（永远英文） | `https://docs.djangoproject.com/en/6.1/_sources/<path>.txt` |
| 拒用 | `/dev/`（下一版）、`/en/stable/`、`/en/latest/`、无版本号的 `/en/<path>` |

## 按问题类型选族

| 你在问 | 抓哪里 | 例 |
|---|---|---|
| 某个 setting 是什么/默认值/新版变化 | `ref/settings/` | `ref/settings` → `#std-setting-SILENCED_SYSTEM_CHECKS` |
| 管理命令的参数与语义 | `ref/django-admin/` | `#django-admin-check`、`#cmdoption-check-database` |
| 某个检查号什么意思 | `ref/checks/`（只到**章节**锚点） | `#database`、`#models`、`#mail` |
| 概念与"为什么这样设计" | `topics/` | `topics/db/fetch-modes`、`topics/checks` |
| 照着做一遍的步骤 | `howto/` | `howto/upgrade-version`、`howto/mailers-migration` |
| "自 6.1 起 / 6.1 不再支持" | `releases/6.1/` | `#system-checks`、`#backwards-incompatible-changes-in-6-1` |
| 6.0 侧对照 | `releases/6.0/` + `en/6.0/...` | 只用于对比，结论仍标 6.1 |
| 实现细节、精确行号、文档没说的事 | GitHub tag 源码 | `https://github.com/django/django/blob/6.1.3/<path>#L<n>` |

## 锚点规则（已实测，别猜）

| 族 | 锚点可用？ | 说明 |
|---|---|---|
| settings | ✅ `#std-setting-<NAME>` | 大写原名，如 `#std-setting-DATABASES` |
| 管理命令 | ✅ `#django-admin-<cmd>`、`#cmdoption-<cmd>-<opt>` | 如 `#cmdoption-check-database` |
| 检查号（`models.W036`） | ❌ **没有 per-id 锚点** | 实测 ref/checks 全页仅 99 个 id、含 `#models` 这类章节锚点，无 `w036`；引整页 + 检查号文本，精确指位改引源码或 `_sources` 行号 |
| 发布说明章节 | ✅ `#<section-slug>` | 如 `#system-checks`、`#whats-new-6-1` |
| topics/howto | ✅ `#<section-slug>` | 小节标题的连字符形式 |

精确指位检查号时，用这两种替代：

```bash
# ① 文档 reST 里的行号（可写进报告）
python .agents/skills/django-61-docs/scripts/doc_src.py ref/checks --grep "models.W036"

# ② 源码定义处（检查号由源码发出）
#    django/core/checks/messages.py / django/db/models/constraints.py 等
```

## 常用入口速查

| 页 | 内容 |
|---|---|
| `ref/models/querysets` | QuerySet API、`fetch_mode()`、`first()/last()`、`union()` |
| `ref/models/fields` | 字段类型、`on_delete` 的 DB 级选项（`DB_CASCADE` 等） |
| `ref/models/constraints` | `UniqueConstraint` 的 `condition`/`nulls_distinct` |
| `ref/exceptions` | `FieldFetchBlocked`、`OperationalError`、`IntegrityError` |
| `ref/checks` | 所有检查号（只有章节锚点） |
| `ref/settings` | 所有 setting |
| `ref/django-admin` | 所有管理命令 |
| `topics/db/transactions` | `atomic`、`on_commit` |
| `topics/db/fetch-modes` | 6.1 新增：`FETCH_ONE`/`FETCH_PEERS`/`FETCH_RAISE` |
| `howto/upgrade-version` | 升级流程（先读它，再读目标版 release notes） |
| `internals/deprecation` | 弃用时间表与策略 |

## 源码定位法

```bash
# 本机已装版本里找符号定义（最快）
python -c "import django.db.models as m; print(m.__file__)"

# 上游源码里找行号（只读、不落盘；把 pattern 换成你要找的标识符）
python -c "import urllib.request as u; s=u.urlopen('https://raw.githubusercontent.com/django/django/6.1.3/django/core/checks/registry.py',timeout=30).read().decode(); [print(i,l) for i,l in enumerate(s.splitlines(),1) if 'connections' in l]"
```

得到行号后拼成可复核的引用：
`https://github.com/django/django/blob/6.1.3/django/core/checks/registry.py#L96`

引用行为时给 **tag**（`6.1.3`）而不是 `stable/6.1.x`——后者会随补丁漂移，半年后无法复核。

