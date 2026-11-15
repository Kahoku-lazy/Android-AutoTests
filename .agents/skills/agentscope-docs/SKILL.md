---
name: agentscope-docs
description: >-
  Use when answering anything about the AgentScope framework — 2.x API, tutorials,
  Agent/SOP/Middleware/MCP/RAG/Realtime/Workspace, deployment, or "官方文档怎么说" —
  and when an answer must be grounded in the official docs instead of memory.
  Pins docs to the installed agentscope version, prefers the docs MCP server
  (search_agent_scope / query_docs_filesystem_agent_scope) over guessing, and cites
  page URLs. Project-local skill for Android-AutoTests, whose engines/agents runs on
  AgentScope.
---

# AgentScope 官方文档查询（本仓库）

本技能服务 **Android-AutoTests**：`engines/agents/` 整套角色、SOP、中间件、RAG、实时语音都建在 AgentScope 之上，
所以「框架到底怎么设计的」必须查官方文档，不能凭记忆或只看包内 docstring。

## 何时用

- 问 AgentScope 的**概念/设计**：Agent 装配、Context 压缩、SOP、Middleware、Permission、Workspace、Pipeline、A2A
- 问**具体 API 怎么写**：`MCPClient`、`Toolkit(mcps=)`、`GoalPipeline`、`ReActConfig`、`list_models()`
- 要**核对**仓库里的用法是不是官方姿势（例如 SOP 该不该替自研重试）
- 需要**按版本**回答（我们锁 `agentscope>=2.0.9`，站点同时挂着 2.0.2 ~ 2.0.12dev）

## 何时不用

- 只是读本仓库代码 → 用 `engines-docstring-check` 的 `read`
- 装包、跑测试、改代码 → 直接做，不必查文档
- 问 AgentScope 的**社区八卦/发布新闻** → 用 web_search，不是本技能

## 铁律：版本先对齐

```bash
python -c "import agentscope; print(agentscope.__version__)"
```

- 文档路径带版本：`/zh/versions/2.0.9/...`、`/en/versions/2.0.9/...`
- **1.x 与 2.x 的 API 不混用**（站点 `others/change-log` 是迁移说明）
- 回答里写明「这是 2.0.9 文档的说法」；版本不一致时明确提示
- 新项目参考 `stable`，存量项目按**已安装版本**

## 三条通道（按优先级）

### ① 文档 MCP 服务（首选，本机已配好）

DSH 已注册 `agentscope-docs`，直接调用这三个工具：

| 工具 | 用途 |
|---|---|
| `mcp__agentscope-docs__search_agent_scope` | 语义检索，支持 `version` / `language` 过滤 |
| `mcp__agentscope-docs__query_docs_filesystem_agent_scope` | 在文档虚拟文件系统上跑只读 shell（`rg` / `tree` / `ls` / `cat` / `head` / `jq` …） |
| `mcp__agentscope-docs__submit_feedback` | 发现文档有错时上报（别拿它代替回答） |

**关键事实（踩过）**：

- **没有 `get_page` 工具**——读页面就是 `cat /path/page.mdx`；URL 路径 + `.mdx` 就是文件路径
- 虚拟文件系统 **stateless**：每次调用工作目录回到 `/`，`cd` 不跨调用；要么用绝对路径，要么 `cd /x && ls`
- 单次输出 **30KB 截断**，大页用 `rg -C` 或 `head -N` 分段读
- **路径不要猜**：先 `tree` / `ls` / `rg -il` 发现真实路径；猜错只说明猜错，不代表没文档

### ② 本技能脚本（没配 MCP 的环境，或想批量跑）

```bash
cd .agents/skills/agentscope-docs
python -m scripts.docs_mcp tools
python -m scripts.docs_mcp search "SOP 执行者 验证者" --language zh --version 2.0.9
python -m scripts.docs_mcp tree /zh/versions/2.0.9/building-blocks -L 1
python -m scripts.docs_mcp rg "tool_result_limit" /
python -m scripts.docs_mcp cat /zh/versions/2.0.9/building-blocks/model/overview.mdx
python -m scripts.docs_mcp page https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/sop
```

**只用标准库**（`urllib`），不依赖 httpx/requests——本机 Python 站点包出问题时它照样能跑。端点可用 `AGENTSCOPE_DOCS_MCP` 覆盖。

### ③ 纯网页（已知 URL）

```
https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/sop.md
```

页 URL 后加 `.md` 拿纯 Markdown，比 HTML 干净。不确定路径时先看 `https://docs.agentscope.io/llms.txt`。

## 标准流程

1. **定版本**：读已安装 `agentscope.__version__`，确定用哪个 `/versions/<v>/`
2. **定位**：`search_agent_scope`（概念型）或 `rg -il`（精确关键词）
3. **读全文**：`cat <返回路径>.mdx`，或 `web_fetch` 该页 `.md`
4. **引用**：给出去掉 `.mdx` 的 URL，并标明版本

## 文档地图（2.0.9 中文站点）

| 前缀 | 内容 |
|---|---|
| `/zh/versions/<v>/building-blocks/agent/` | Agent 概述、配置、运行、中断、人机交互 |
| `/zh/versions/<v>/building-blocks/model/` | 凭证与模型卡、LLM、TTS、Embedding |
| `/zh/versions/<v>/building-blocks/context/` | 压缩、卸载、环境感知 |
| `/zh/versions/<v>/building-blocks/tool/` | Python 工具、MCP、Skill、元工具 |
| `/zh/versions/<v>/building-blocks/sop.mdx` | 标准作业流程（步骤 + 验收） |
| `/zh/versions/<v>/building-blocks/middleware.mdx` | 中间件 |
| `/zh/versions/<v>/building-blocks/pipeline/` | 目标流水线、团队流水线 |
| `/zh/versions/<v>/building-blocks/permission-system/` | 权限模式、规则、工具内置检查 |
| `/zh/versions/<v>/building-blocks/workspace/` | 工作区、资源管理、MCP 网关 |
| `/zh/versions/<v>/building-blocks/realtime/` | 实时语音、S2S |
| `/zh/versions/<v>/deploy/` | 服务化：多租户、SOP 服务、RAG 服务、渠道、Hub |
| `/openapi/en/versions/<v>/deploy/openapi.json` | 服务端接口 schema |

## 输出纪律

- **结论先行**：先一句话回答，再展开
- **标版本**：说清是 2.0.9 还是 2.0.11 的说法
- **给链接**：引用到的每一页都给官方 URL
- **分清来源**：文档原文 / 包内 docstring / 我的推断，三者不要混着说
- **不夸大**：没查到的就说没查到，不要用先验知识补全

## 常见坑

| 现象 | 原因 | 处理 |
|---|---|---|
| `curl` / `Invoke-WebRequest` 打 MCP 端点失败 | schannel 凭证错误 | 用本技能脚本（标准库）或原生 MCP 工具 |
| 中文输出乱码 | 控制台 GBK | 脚本已 `reconfigure(utf-8)`；自己写时加 `PYTHONIOENCODING=utf-8` |
| `search` 返回片段不是全文 | 它只给命中段 | 拿 `Page` 路径去 `cat` |
| `search` 结果混着多个版本 | 默认不过滤 | 传 `version`，或按 `Page` 里的版本挑 |
| `cat` 报文件不存在 | 路径猜错 | `rg -il "关键词" /` 反查真实路径 |
