<div align="center">

# 🐾 Android-AutoTests

**AI 驱动的 Android UI 自动化测试平台**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0.3-orange.svg)](https://docs.agentscope.io/versions/2.0.3/zh/)
![Theme](https://img.shields.io/badge/theme-Doodle%20Craft-f5a623.svg)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## 📖 项目简介

> 为 **Android 测试工程师**打造的 **AI 驱动的 UI 自动化测试平台**，将元素定位、用例编排、执行调度、报告输出整合为**自然语言驱动的全流程闭环**。

### 价值主张

| 维度 | 传统方式 | Android-AutoTests |
|------|---------|-------------------|
| **元素定位** | 手写 XPath / UI Automator Viewer | 实时截图 + 点击自动生成 8 种 XPath，所见即所得 |
| **用例创建** | 代码编写 / 录制回放 | 拖拽编排 29 种原子步骤（UI/API/Web），或 AI 自然语言生成 |
| **测试执行** | 手动或 CI 脚本触发 | 一键执行 + 循环压测 + TREP v1.0 实时监控 |
| **结果分析** | 翻日志文件 | 在线报告 + 失败步骤级诊断 + 仪表盘趋势图 |
| **AI 协作** | 无 | 自然语言驱动全流程：需求→元素→用例→执行→报告 |

### 目标用户

| 角色 | 核心需求 | 使用频率 |
|------|----------|:--:|
| **测试工程师**（主要） | 快速定位元素 → 编排步骤 → 批量回归 → 专业报告 | 每日 |
| **产品经理**（次要） | 一键执行冒烟用例、查看通过率和趋势 | 每周 |
| **QA 负责人**（次要） | 多设备并行、执行历史审计、质量趋势 | 每周 |

### 产品边界

**✅ 本期范围**：Android 8.0+ UI 自动化 · USB + WiFi ADB · JWT 认证 · AI 自然语言生成用例 · 29 种原子步骤类型（UI/API/Web）· SQLite/MySQL · 在线报告

**❌ 非本期**：iOS 设备 · 设备云租用 · 多团队隔离 · OAuth/SSO · AI 自主修复失败用例 · 分布式集群

---

## 🏗️ 架构概览

```
Vue 前端 :5173  ──HTTP/WS──→  Django :8766  ──ORM──→  SQLite/MySQL
       │                           │
       └──SSE──→  AgentScope（进程内运行于 Django）
                      │
                      └── 同进程调用 Django ORM（17 平台 Tool + ChromaDB RAG）

Django ──uiautomator2──→  Android 设备
```

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Vue 3.4 + Vite + Element Plus | 10 个前端模块，Doodle Craft 手绘主题 |
| 后端 | Django 4.2 + Daphne + Channels | 11 个 App，纯 API，JWT 鉴权 |
| AI 引擎 | AgentScope 2.0（Django 进程内）+ Redis | 17 平台 Tool，ReAct 智能体编排，ChromaDB 知识库 |
| 设备控制 | uiautomator2 + ADB | UI dump、8 种 XPath、OCR、2fps 截图流 |
| 数据 | SQLite (开发) / MySQL (生产) + Redis | 32 张业务表，9 组前缀 |

### 模块地图

| 模块 | 数据表 | 核心能力 |
|------|--------|---------|
| **设备管理** | `dp_` (2表) | USB/WiFi 连接 · 锁定/释放 · FIFO 排队 · 心跳超时 |
| **设备检查器** | `di_` (1表) | 实时截图流 · UI dump · 8 种 XPath · OCR 快照 |
| **元素定位** | `el_` (8表) | 页面/元素库 · Web 元素组 · API 端点组 · 页面跳转流 |
| **用例管理** | `cm_` (2表) | 29 种步骤 · 拖拽编排 · 目录树 · YAML 导入导出 |
| **执行引擎** | `tr_` (4表) | asyncio 异步 · TREP v1.0 监控 · 循环压测 · 中途停止 |
| **测试报告** | `rg_` (2表) | CSV/Markdown/JSON · 步骤级诊断 · HTML 在线预览 |
| **AI 助手** | `ai_` (7表) | SSE 流式对话 · 17 平台 Tool · HITL 确认 · 共享工具箱 · ChromaDB RAG |
| **评测中心** | `ev_` (4表) | 题库管理 · 智能出题 · 评测运行 · 人工评分 |
| **仪表盘** | 无（聚合） | ECharts 趋势图 · KPI 卡片 · 实时统计 |
| **工作流工作台** | `wf_` (2表) | JSON 持久化 · 目录管理 · VueFlow 页面流编排 |

---

## 🚀 环境配置

### 前置依赖

| 依赖 | 版本要求 | 检查命令 |
|------|---------|---------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Redis | 6.0+ | `redis-cli ping` |
| ADB | 任意 | `adb version` |

### 安装

```bash
git clone https://github.com/your-org/Android-AutoTests.git
cd Android-AutoTests

# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# 数据库初始化
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User;
User.objects.create_superuser('admin','admin@local','admin123')
if not User.objects.filter(username='admin').exists() else None
"

# 知识库初始化（AI 助手 RAG，首次运行）
python manage.py init_knowledge_base
```

### 启动

```bash
python run.py start      # 一键启动 Django + AgentScope + Vite
python run.py status     # 查看服务状态
python run.py logs       # 查看日志
```

### 访问地址

#### 本地开发（`python run.py start`）

| 服务 | 地址 | 说明 |
|------|------|------|
| 🏠 前端 | `http://localhost:5173` | Vite 热重载，改代码秒刷新 |
| ⚙️ 管理后台 | `http://localhost:8766/admin/` | Django Admin（admin/admin123） |
| 🔌 后端 API | `http://localhost:8766/api/` | REST JSON |
| 🤖 AI 引擎 | Django 进程内运行 | AgentScope 已集成，无独立端口 |

> 本地端口可通过环境变量 `SERVER_PORT` 自定义，默认为 `8766`；前端端口固定为 `5173`。

---

## 🤖 AI Agent 自动配置环境

将以下提示词发送给 Claude Code（或其他 AI 编码助手），Agent 将自动完成环境配置：

````text
请帮我配置 Android-AutoTests 项目的开发环境。按以下步骤执行：

1. 检查前置依赖：python --version, node --version, redis-cli ping, adb version
   如有缺失，提示我安装后再继续。

2. 安装后端依赖：pip install -r requirements.txt

3. 安装前端依赖：cd frontend && npm install && cd ..

4. 初始化数据库：
   python manage.py migrate
   python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@local','admin123') if not User.objects.filter(username='admin').exists() else None"

5. 初始化知识库：python manage.py init_knowledge_base

6. 检查 Redis 是否运行，如果未运行则启动：redis-server --daemonize yes

7. 启动全部服务：python run.py start

8. 验证服务状态：python run.py status
   期望 3 个服务全部 ONLINE：Redis / Django backend / Vue frontend

9. 健康检查：
   curl -s http://localhost:8766/api/ | python -m json.tool
   curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

10. 如果任何步骤失败，分析日志并修复：
    tail -20 logs/backend.log
    tail -20 logs/frontend.log

完成后告诉我各服务状态和访问地址。
````

---

## 📚 参考文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求大纲 | `dev_docs/02-PRD需求/需求大纲.md` | 项目定位 · 用户 · 状态机 · 模块边界 |
| 子模块 PRD（9 份） | `dev_docs/02-PRD需求/PRD-0*.md` | 各模块详细功能规格 |
| 开发验收清单 | `dev_docs/DEVELOPMENT_CHECKLIST.md` | AI 开发结果唯一验收守门员 |
| 项目架构 | `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` | 架构总纲 · 11 App 全景 · 设计决策 |
| 技术栈参考 | `dev_docs/03-设计与架构/技术栈参考.md` | 技术选型 · 命名统一标准 |
| 文档编号对照 | `dev_docs/文档编号对照表.md` | ARCH/PRD/API 编号唯一真相源 |
| AI 助手指令 | `CLAUDE.md` | 行为准则 · 模块防火墙 · 项目工具 · 关键约定 |

### 外部引用

| 项目 | 链接 | 说明 |
|------|------|------|
| AgentScope 2.0 | https://docs.agentscope.io/versions/2.0.3/zh/ | AI 引擎框架 |
| animejs | https://animejs.com/documentation/ | 动画引擎 |
| TestHub Platform | https://github.com/chenjigang4167/testhub_platform | 架构参考 |
