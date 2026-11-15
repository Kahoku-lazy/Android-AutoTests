---
name: django-61-docs
description: >-
  Use when answering anything about Django 6.1 — API、settings、管理命令、system check 报错号、
  发布说明、升级/破坏性变更，或「官方文档怎么说」「这个 W036 什么意思」「check 会不会连库」
  「6.1 升级会坏什么」。Pins every claim to docs 6.1.x plus 源码 tag plus 本机实测三源交叉，
  拒绝凭记忆回答，也拒绝只信单个页面（参考页滞后于发布说明已实证）。Project-local skill for
  Android-AutoTests, whose backend/ is a Django project pinned to 6.0.6 with 6.1 as upgrade target.
---

# Django 6.1 文档查询（本仓库）

`backend/` 是一个真实运行的 Django 项目（[requirements.txt](../../../requirements.txt) 当前钉 `Django==6.0.6`，
6.1.x 是候选升级目标）。所以「Django 6.1 怎么规定的」这类问题必须按本技能查：**版本钉死、多源交叉、结论带引用**。

## 何时用

- 查 **6.1 的行为/默认值**：某个 setting 默认是什么、某个管理命令接受什么参数
- **解释报错与告警**：`models.W036`、`fields.E011`、`mysql.W002` 这类检查号到底什么意思
- **评估升级影响**：6.0 → 6.1 的破坏性变更、弃用项、新特性（fetch modes、`DB_CASCADE`、`MAILERS`）
- **核对仓库用法**是不是官方姿势（我们锁过版本、查过 `check` 连库，都是靠这套流程定的）
- 需要写进方案/报告、**必须给出可复核的版本化引用**的时候

## 何时不用

- 只是读本仓库代码 → `engines-docstring-check` 的 `read`
- 装包、跑测试、改代码 → 直接做
- Django 的新闻、社区讨论、issue 八卦 → `web_search`，不是本技能

## 铁律一：先把版本钉死

```bash
grep -n "^Django" requirements.txt        # 仓库当前钉的版本（写回答前先看）
```

- 文档 URL **必须**落在 `/en/6.1/`（中文 `/zh-hans/6.1/`）：`/dev/` 是下一版，不带版本的 `stable` 会跟随最新，都不能当 6.1 的答案
- 6.1.x 补丁级的差异（如某个检查在 6.1.2 被移除）→ 查对应版本的发布说明 + GitHub tag
- 回答里写明「这是 **6.1** 文档 / **6.1.3** 源码的说法」；拿 6.0 作对比时两侧都标出来

## 铁律二：四个证据源，按可信度排

| 级别 | 来源 | 什么时候必须用 |
|---|---|---|
| ① 实测 | 本机 `python -c` / `manage.py` / 最小复现 | 任何「会不会连库 / 会不会报错 / 默认值 / 顺序 / 是否被移除」的问题 |
| ② 源码 | GitHub tag `6.1.3`（或 `stable/6.1.x`） | 文档没写、写得含糊、或与文档冲突 |
| ③ 发布说明 | `releases/6.1/`，必要时对比 `releases/6.0/` | 升级影响、破坏性变更、新特性、弃用 |
| ④ 主题/参考页 | `topics/`、`ref/`、`howto/` | 概念解释、用法示例、API 签名 |

为什么这么排：单句文档最容易误导。`ref/checks` 说「database 检查默认不跑」是对的，可 `check` 实测
照样连库——因为连库的是 `models` 组的字段级后端检查（`_check_backend_specific_checks`），不是 `database` 组。
只有把文档、源码、实测三样对起来，才知道你引的那句话在说哪条路径。而"会不会真的连库"这种事，
只有跑一遍才算数。

## 标准流程（五步）

1. **定版本**：读 `requirements.txt`，明确这次回答针对 6.0.6 还是 6.1.x
2. **分类型**：按 [references/source-map.md](references/source-map.md) 把问题映射到 URL 族
   （setting / 命令参数 / 检查号 / 主题 / 升级 / 实现细节）
3. **读原文**：优先抓 `_sources/**/*.txt`（英文 reST，无导航噪声、可精确 grep）；
   要中文措辞时再抓 `zh-hans/6.1/` 的 HTML 页（注意：`_sources` 永远是英文）
4. **交叉验证**：涉及行为 → 跑最小实测；涉及实现 → 读 tag 源码并给出 `#L<行号>`
5. **落引用**：每条结论配版本化 URL（+ 锚点或行号），并标清证据级别

## 脚本（只用标准库，无第三方依赖）

```bash
# 读 6.1 文档的 reST 原文（绕开 web_fetch 的 30KB 截断）
python .agents/skills/django-61-docs/scripts/doc_src.py ref/checks --grep "database tag" -C 4
python .agents/skills/django-61-docs/scripts/doc_src.py topics/db/fetch-modes --head 60
python .agents/skills/django-61-docs/scripts/doc_src.py ref/settings --grep "SILENCED_SYSTEM_CHECKS"
python .agents/skills/django-61-docs/scripts/doc_src.py --list ref/models            # 目录下有哪些页

# 校验写出去的链接是否都钉在 6.1（退出码 1 表示有违规）
python .agents/skills/django-61-docs/scripts/doc_link_lint.py dev_docs/xxx.md
python .agents/skills/django-61-docs/scripts/doc_link_lint.py --changed              # 只查 git 改动
```

`--version 6.0` 可切到 6.0 文档做对比；`--lang zh-hans` 只影响报错提示语，不改变 `_sources` 是英文这一事实。

## 常见坑（详表见 [references/pitfalls.md](references/pitfalls.md)）

| 现象 | 处理 |
|---|---|
| `web_fetch` 读到一半被截断 | 改用 `doc_src.py --grep/-C`，或直接抓 `_sources` reST 原文 |
| 从检查标签推断"谁会连库" | `database` 组被过滤 ≠ 没人连库；读 `registry.py` 或跑一次最小复现 |
| 文档与实测"矛盾" | 先确认是不是两条路径（`database` 组 vs `models` 组）；确认后再谈谁对 |
| `zh-hans/6.1/_sources/*.txt` 打开是英文 | 正常：源码永不翻译；中文只能读 HTML 页 |
| 「`check` 会不会连库」这类问题 | 必须实测：给一个不可达的 `DB_HOST`/`DB_PORT` 跑一遍 |
| 把 `/dev/` 当 6.1 | 看页面侧栏 `Documentation version: 6.1` 才算数 |
| 只给 HTML 链接不给锚点 | 用 `#models.w036`、`#std-setting-SILENCED_SYSTEM_CHECKS`、`#cmdoption-check-database` 这类锚点，方便复核 |
| 引用源码没给行号 | 用 `https://github.com/django/django/blob/6.1.3/<path>#L<n>` |

## 输出模板（严格）

```text
结论：<一句话>

依据（按证据级别分开写，不混着说）：
- 实测：<命令> → <结果>
- 源码：6.1.3 <path>#L<n> → <关键片段>
- 发布说明：https://docs.djangoproject.com/en/6.1/releases/6.1/ → <原文摘录>
- 文档：https://docs.djangoproject.com/en/6.1/ref/checks/#models.w036 → <原文摘录>

冲突 / 未验证：<文档与实测不一致的点，或本次没条件验证的部分>
```

- **结论先行**：先一句话回答，再展开
- **三源分开**：文档原文 / 源码 / 我的推断，三者不要混着说
- **不夸大**：没查到就说没查到；推断要标「推断」
- **版本化引用**：链接必须是 `/6.1/`；引用具体行号时写清 tag

## 与仓库流程的衔接

- 结论要进方案/报告 → 落 `dev_docs/`（架构类 `ARCH_PRD`，测试/方案类 `DEV_TEST`）
- 结论要变成代码改动 → 走 OpenSpec 四步（explore → propose → apply → archive），本技能不改代码
- 本技能对 `backend/` 的既有结论（例如 `check` 在 6.1 会连库、OpenAPI 基线必须用 mysql 配置生成）
  先看 [references/pitfalls.md](references/pitfalls.md)，别重复踩
