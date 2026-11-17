工具：OpenCodeReview（ocr），阿里开源的 AI 代码审查 CLI，Apache-2.0 协议
安装命令：`npm install -g @alibaba-group/open-code-review`（你的环境已满足全部前置条件，随时可装）
装后两步：`ocr config provide`r 配置模型和 API Key → 在 Git 仓库里 ocr review，或用 ocr scan 扫描任意目录
`custom provide` 自定义模型
文档：open-codereview.ai/docs

技能安装：npx skills add alibaba/open-code-review


```bash
cd 你的项目目录

ocr review                        # 审查工作区所有变更（暂存+未暂存+未跟踪）
ocr review --from main --to 分支名  # 审查两个分支分叉后的变更
ocr review --commit abc123        # 审查单个提交
ocr review --preview              # 只预览会审查哪些文件，不真正调用模型

ocr scan                          # 全量扫描整个目录（不需要 Git 历史）
ocr scan --path src/某个目录       # 只扫描指定目录/文件

ocr review --format json --output result.json   # 结果输出为 JSON
```


没问题，那我先讲清楚它是干嘛的，你再决定用不用 😄

## 一句话说明

**OpenCodeReview 是个"AI 代码审查员"**：你把代码改动丢给它，它像一个资深工程师一样逐行审查，告诉你哪里有 bug、哪里有隐患，精确到**文件名 + 行号**。

## 它具体能发现什么

比如开发改了这么一段代码：

```python
def get_user(users, id):
    for u in users:
        if u.id == id:
            return u.name
```

它可能会给出这样的审查意见：

> 📍 `user_service.py:42` 【高】未找到用户时函数隐式返回 `None`，调用方直接 `.upper()` 会抛异常，建议显式抛出 `UserNotFoundError` 或返回默认值。

典型能抓到的问题：
- **逻辑缺陷**：边界条件漏了、空指针、数组越界、死循环
- **安全隐患**：SQL 注入、硬编码密钥、路径穿越
- **资源问题**：连接/文件没关闭、内存泄漏
- **并发问题**：竞态条件、锁用错
- **坏味道**：重复代码、错误处理缺失、命名误导

而且它不是只看 diff 表面——它会**主动读完整文件、搜索代码库上下文**再下结论，所以误报比直接丢给通用 AI 少很多（官方基准测试：准确率更高、token 消耗只有约 1/9）。

## 典型使用场景

| 场景 | 命令 |
|---|---|
| 提交代码前自查一遍 | `ocr review` |
| 审查同事的 PR / 分支改动 | `ocr review --from main --to 他的分支` |
| 接手一个不熟悉的项目，快速摸底 | `ocr scan` |
| 接进 CI，每次提交自动审查 | GitHub Actions / GitLab CI |

## 它**不能**干什么（避免误会）

- ❌ 不生成测试用例（它是审查代码，不是写测试）
- ❌ 不运行代码、不执行测试
- ❌ 不管代码格式/风格（那是 linter 的活）
- ❌ 不能替代人工审查，是帮你提前过滤掉低级问题


我之前帮你启动的那个**还在运行**，所以现在直接打开 **http://localhost:5483** 就能用。

以后想自己启动，指令如下（PowerShell）：

## 方式一：前台启动（最简单）

```powershell
ocr viewer
```

- 自动打开浏览器，地址 `http://localhost:5483`
- 终端窗口要一直开着，`Ctrl+C` 停止

## 方式二：真·后台启动（关终端也不停）

```powershell
Start-Process ocr -ArgumentList "viewer","--open=never" -WindowStyle Hidden
```

- 无窗口后台运行，然后浏览器手动打开 `http://localhost:5483`
- 停止后台查看器：

```powershell
Stop-Process -Name ocr
```

⚠️ 注意：`Stop-Process -Name ocr` 会结束**所有** ocr 进程，如果当时正在跑审查也会一起被杀掉。

## 常用变体

```powershell
ocr viewer --addr :3000      # 换端口（比如 5483 被占用时）
ocr viewer --open=never      # 不自动弹浏览器，只打印 URL
```

## 让 Agent 看到报告的几种方式

### 1️⃣ 直接读本地文件（刚才已经做到）

OCR 的会话数据就在 `C:\Users\zhiyan\.opencodereview\sessions\`，任何能读文件的 Agent（包括我）都能直接解析。

**以后你只要对我说"读一下 ocr-report.json，帮我修复 critical 问题"就行了。**

### 2️⃣ 运行时直接输出给 Agent（官方推荐）

```bash
# 输出 JSON 文件
ocr review --format json --output result.json

# agent 专用模式：无交互 UI，stdout 纯 JSON
ocr review --format json --audience agent > result.json
```

### 3️⃣ 深度集成（让 Agent 自己驱动审查）

| 方式 | 说明 |
|---|---|
| **Agent Skill** | OCR 提供可移植的 `open-code-review` skill，装进支持 skill 的 Agent（DSH 就支持），Agent 就能按标准流程发起审查、读取结果 |
| **委托模式** | `ocr delegate preview` / `ocr delegate rule <文件>` —— OCR 只负责选文件和解析规则，**由宿主 Agent 用自己的模型执行审查**，不需要 OCR 的 API Key |
| **MCP 服务器** | OCR 自带 MCP server，可以配进 DSH 的 MCP 连接，我就能直接调用它的审查工具 |

