---
name: code-health-check
description: |
  代码健康检查 — 自动化工具扫描 + AI 语义审查双引擎，发现 Python 代码中 ruff 到达不了的深层问题：返回类型不一致、魔法字符串、热路径冗余、静默吞错、字段语义过载、重复逻辑、封装破坏等。
  Keywords: 代码检查, 代码质量, 健康检查, 静态分析, 维护性, 可维护性, code review, 代码审查, 查代码, 检查代码
  Trigger: 用户表达"检查代码/代码质量/健康检查/查代码/代码审查/维护性分析"，或要求对 Python 文件进行深度质量排查时。
---

# Code Health Check — 工具 + AI 双引擎代码健康检查

**目的**: 先用自动化工具扫描能机器发现的问题，再用 AI 语义审查发现工具到达不了的深层设计问题，输出统一报告。

**核心理念**: ruff/mypy 只能覆盖约 20% 的代码质量问题。剩下 80%——返回类型不一致、字段语义过载、魔法字符串、静默吞错——需要结构化提示词引导 AI 逐项检查。

## 双引擎模型

```
引擎 1: 自动化工具 (ruff)
  能发现: 命名违规、XPath/SQL 注入、裸 except、圈复杂度超标
  不能发现: 设计意图、语义矛盾、代码模式重复、缺少错误处理

引擎 2: AI 语义审查 (结构化提示词)
  针对工具到不了的 12 类问题，逐项给 AI 检查清单
  每项检查有: 触发关键词、搜索命令、判断标准、输出格式
```

## 工作流

### Phase 1: 工具扫描

```bash
# 对被检查文件运行 ruff（带预设规则集）
ruff check --select PL,B,SIM,N,B,C90,RUF,ANN --output-format=grouped <target_files>
```

规则说明：

| 规则集 | 检查什么 | 典型命中 |
|--------|---------|---------|
| `PL` | Pylint 等价规则 | 函数内冗余变量、可复用的代码 |
| `B` | flake8-bugbear | 裸 except、可变默认参数 |
| `SIM` | flake8-simplify | 可简化的 if/for |
| `N` | pep8-naming | 命名违规（ALL_CAPS 实例属性等） |
| `C90` | mccabe 复杂度 | 函数圈复杂度 > 10 |
| `RUF` | ruff 自有 | Python 版本兼容性 |
| `ANN` | flake8-annotations | 缺少返回类型注解 |

### Phase 2: AI 语义审查

对每个被检查文件，**逐项**执行以下 12 项检查。每一项给出：
- 是否命中
- 命中的具体代码位置
- 严重度（🔴 功能正确性 / 🟠 可维护性 / 🟡 代码风格）
- 修复建议

#### 检查清单

**1. 返回类型一致性**
```
触发: 一个类中多个方法返回不同类型（None / bool / str / raise）
搜索: grep -n "def " <file> 列出所有方法，人工对比返回值
判断: 同一类中，无异常、查询类方法混用 None/bool/str → 命中
```

**2. 魔法字符串**
```
触发: return 语句直接返回裸字符串（如 'pass'/'fail'/'a'/'b'）
搜索: grep -rn "return\s\+['\"]" <file> | grep -v "JsonResponse\|HttpResponse"
判断: 返回的字符串在 models/constants.py 或 StepType 枚举中无对应定义 → 命中
```

**3. 热路径冗余构造**
```
触发: 高频调用方法（execute/__call__/run）中重建字面量容器
搜索: 搜索 def execute / def __call__ 方法体内的大括号 {} 或 []
判断: dict/list 的内容是固定映射（handler 字典、常量表） → 命中，应提升为类变量
```

**4. 静默吞错**
```
触发: 写操作方法（click/delete/save/kill）没有异常保护
搜索: 列出所有写操作方法 → 逐一检查是否有 try/except
判断: 方法名含 click/delete/save/kill/start/stop 且无 try/except → 命中
```

**5. 字段语义过载**
```
触发: 同一个字段在不同方法中代表不同含义
搜索: grep -rn "s\.index\|step\.index\|\.index\b" <file>
判断: 搜索结果中 .index 被用于 ≥3 种不同语义（如：元素索引、轮询间隔、重试次数） → 命中
```

**6. 重复逻辑**
```
触发: 相同的轮询/循环/条件模式在 ≥3 个方法中出现
搜索: 目视检查方法体中 deadline/while/sleep 模式的重复
判断: 包含相似 while+time+deadline 结构的代码块在 3+ 个方法中出现 → 命中，应提取公共方法
```

**7. 封装破坏**
```
触发: 外部直接访问对象的 `_` 前缀私有属性
搜索: grep -rn "\._[a-z]" <caller_file>  # 在被调用文件中搜
判断: 命中 → 应添加公共 getter/setter 或 @property
```

**8. 字段名与实际用途矛盾**
```
触发: 字段名暗示一种用途，代码中使用为另一种
搜索: 搜索 s.xpath 在非定位场景的使用（如作为包名参数）
判断: 字段名与注释声明的用途不一致 → 命中
```

**9. 枚举与实现不同步**
```
触发: handler 字典/mapping 的条目数 ≠ 枚举定义的条目数
操作: 数 handler 字典的 key 数 → 对比 models/step_types.py 的 StepType 枚举值数
判断: 数量不一致 → 命中
```

**10. 硬编码数值散落**
```
触发: 数字字面量（2/3/0.3/0.5/5/12）散落在方法体中无常量名
搜索: grep -rn "\b[0-9]\+\(\.[0-9]\+\)\?\b" <file> | grep -v "0\b\|1\b\|100\b"
判断: 同一个数值出现在 ≥2 个不同方法中 → 命中
```

**11. 日志规范**
```
触发: print() 或缺少日志的方法
搜索: grep -rn "print(" <file>  # 直接违规
判断: 同时检查写操作、异常路径是否有 log()/logger 调用 → 缺失则命中
```

**12. 异常吞噬**
```
触发: except 块什么都不做或只 pass
搜索: grep -rn "except.*:" -A 2 <file> | grep "pass\|#\|$"
判断: except 后直接 pass 或空行 → 命中
```

### Phase 3: 输出报告

按以下结构输出 HTML 报告到 `tests/functional/code-health/reports/`：

```
1. KPI 摘要卡片
   - 检查文件数 / 工具发现问题数 / AI 发现问题数 / 综合评分

2. 引擎 1: ruff 扫描结果
   表格：文件 / 规则 / 位置 / 问题描述

3. 引擎 2: AI 语义审查结果
   12 项检查的命中详情，每项含代码片段 + 严重度 + 修复建议

4. 12 项检查的覆盖率矩阵
   表格：每项检查对其他模块的可复用性

5. 优先修复清单
   P0/P1/P2 分级
```

## HTML 样式规范

- 配色: 遵循 `html-report` skill 的 design token
- 字体: Nunito + Noto Sans SC
- 卡片布局，问题用左侧色带区分严重度（🔴红/🟠黄/🟡灰）
- 代码块用暗色背景 + 语法高亮

## 适用文件类型

- Python 后端文件（`apps/**/*.py` / `models/**/*.py`）
- Django views / api / service / adapter / executor 等业务逻辑文件
- 不适合: `migrations/` / `__pycache__` / 第三方库代码

## 关联文件

| 文件 | 用途 |
|------|------|
| `ruff.toml` | 自动化扫描规则配置 |
| `html-report` skill | 生成 HTML 报告时加载 design token |
| `android-autotests-rules/references/backend.md` | 后端编码规范 |
| `models/constants.py` | 枚举定义（检查魔法字符串时对照） |
