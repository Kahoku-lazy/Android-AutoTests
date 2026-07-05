<div align="center">

# 🐾 Android-AutoTests

**AI 驱动的 Android UI 自动化测试平台**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0.3-orange.svg)](https://docs.agentscope.io/versions/2.0.3/zh/)
[![Theme](https://img.shields.io/badge/theme-animal--island--vue-teal.svg)](https://github.com/guokaigdg/animal-island-ui)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## 📖 项目简介

Android-AutoTests 是一个 AI 驱动的 Android UI 自动化测试平台。通过**可视化元素定位**将手机实时截图与 XPath 自动生成结合，通过 **AgentScope 2.0 智能体**将自然语言指令转化为平台操作，实现从元素发现到报告输出的全流程闭环。

> 架构参考：[TestHub Platform](https://github.com/chenjigang4167/testhub_platform) · AI 引擎：[AgentScope](https://docs.agentscope.io/versions/2.0.3/zh/building-blocks/message-and-event) · AI 主题：[animal-island-ui](https://github.com/guokaigdg/animal-island-ui) · 动画：[animejs](https://animejs.com/documentation/)

---

## ✨ 核心特性

### 📱 可视化元素定位
- **实时截图流**：WebSocket 推送手机画面（≥2fps，延迟 ≤500ms）
- **UI 层级抓取**：一键 dump 完整 UI 树，结构化存储
- **8 种 XPath 自动生成**：resource-id / text / content-desc / class / index / combined / wildcard，按匹配数升序排列
- **截图叠加层交互**：右键重叠元素菜单，点击候选 XPath 高亮

### 📋 测试用例工程
- **14 种原子步骤**：click / wait / verify_text / sleep / kill_app / start_app / restart_app / retry_click / log 等
- **拖拽编排** + **XPath 接入** + **YAML 导入导出**

### 🔧 设备资源池
- USB + WiFi 双连接 · 锁定/释放/排队 · 超时自动释放 · 在线/离线/忙碌三态

### ▶️ 异步执行引擎
- asyncio 后台执行 · run_id 立即返回 · WebSocket 6 种实时推送 · 循环压测 · 中途停止

### 📊 测试报告
- CSV / Markdown / JSON 三种格式 · 失败详情含步骤级诊断

### 🤖 AI 智能助手（AgentScope 2.0）
- **ReAct 推理**：思考→工具调用→观察→再思考
- **14 个自定义 Tool**：封装全部 5 个业务模块 API
- **SSE 流式对话**：逐字实时推送，AgentScope 不可用时自动降级
- **Agent Team 编队**：Leader 派发 5 种 Worker（inspector / writer / operator / executor / reporter）
- **Cron 定时任务** + **知识库 RAG**（ChromaDB · 32 篇文档）
- **动物森友会主题**：AI 模块独立暖木色调视觉

### 🔐 平台基础
- **JWT 统一认证**：Django + AgentScope 共享密钥 · access + refresh 双 token
- **一键启停**：`python run.py start/stop/restart/status/logs`
- **Jazzmin 管理后台**：cosmo 主题 · 18 张表注册
- **24 个自定义 SVG 图标** · **animejs 动效** · **ECharts 图表**

---

## 🏗️ 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | [Vue](https://vuejs.org/) 3 + Vite + Element Plus | 3.4 / 5.4 / 2.7 |
| AI 模块主题 | [animal-island-vue](https://github.com/guokaigdg/animal-island-ui) | 0.2 |
| 状态管理 | Pinia | 2.1 |
| 动画 | [animejs](https://animejs.com/documentation/) | 4.5 |
| 后端框架 | [Django](https://www.djangoproject.com/) | 4.2 |
| ASGI | Daphne + Django Channels | 4.0 |
| 设备控制 | uiautomator2 + ADB | 3.0 |
| AI 引擎 | [AgentScope](https://docs.agentscope.io/versions/2.0.3/zh/) + FastAPI + Redis | 2.0.3 |
| 向量库 | ChromaDB | 1.5 |

```
┌──────────────────────────────────────────────────────────┐
│ Vue 3 :5173                                              │
│   proxy: /api → :8765   /agentscope → :8000              │
│   AI 模块: animal-island-vue 动森主题                     │
├───────────────────┬──────────────────────────────────────┤
│ Django :8765       │ AgentScope :8000                    │
│ 6 App · 37 端点    │ 14 Tool · 5 Worker · RAG            │
│ SQLite / MySQL     │ Redis                               │
└───────────────────┴──────────────────────────────────────┘
         │                        │
         └──────── uiautomator2 ──┘
                      │
                 Android 设备
```

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/your-org/Android-AutoTests.git
cd Android-AutoTests

pip install -r requirements.txt          # 后端依赖
cd frontend && npm install && cd ..      # 前端依赖
python manage.py migrate                 # 数据库初始化
python manage.py shell -c \              # 创建管理员
  "from django.contrib.auth.models import User; \
   User.objects.create_superuser('admin','admin@local','admin123') \
   if not User.objects.filter(username='admin').exists() else None"
python agentscope_service/rag/init_kb.py # 知识库初始化
```

### 启动

```bash
python run.py start      # 一键启动 Django + AgentScope + Vite
python run.py status     # 查看状态
python run.py logs       # 查看日志
```

| 服务 | 地址 | 账号 |
|------|------|------|
| 前端 | http://localhost:5173 | admin / admin123 |
| Django API | http://localhost:8765 | — |
| AgentScope AI | http://localhost:8000/docs | — |
| Django Admin | http://localhost:8765/admin/ | admin / admin123 |
| 接口文档 | http://localhost:8765/api/docs.html | — |

---

## 📁 项目结构

```
Android-AutoTests/
├── run.py                          # 一键启停
├── run_agentscope.py               # AgentScope 启动
├── config/                         # Django 配置 (settings/urls/asgi)
├── gateway/                        # JWT 中间件 + WS 路由
├── shared/auth/                    # JWT 签发/验证
├── apps/                           # 6 个业务 App
│   ├── device_pool/                #   设备管理 (5 端点)
│   ├── element_locator/            #   元素定位 (11 端点)
│   ├── case_manager/               #   测试用例 (8 端点)
│   ├── test_runner/                #   执行引擎 (4 端点)
│   ├── report_generator/           #   测试报告 (2 端点)
│   └── ai_assistant/               #   AI 助手 (13 端点)
├── agentscope_service/             # AgentScope AI 服务
│   ├── tools/ (14 Tool) · teams/ (5 Worker) · rag/ (ChromaDB)
├── models/                         # 共享 Dataclass (StepType 14种)
├── frontend/src/                   # Vue 3 前端
│   ├── views/LoginView.vue         #   平台登录页
│   ├── shared/                     #   公共组件/图标/API客户端
│   └── modules/ (7个)              #   业务模块 (含 ai-assistant 动森主题)
├── data/ · logs/                   # 数据与日志
└── AI开发项目文档管理/              # 架构/PRD/测试方案
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| `AI开发项目文档管理/01-技术架构/项目技术架构/当前实现架构方案.md` | 架构方案（含 Mermaid 图） |
| `AI开发项目文档管理/01-技术架构/代码Review规则.md` | 30 项 Review 检查清单 |
| `AI开发项目文档管理/01-技术架构/命名统一标准.md` | 全项目命名权威来源 |
| `AI开发项目文档管理/02-PRD需求/实际需求文档.md` | 总需求（8 模块） |
| `AI开发项目文档管理/02-PRD需求/子PRD/` | 6 份模块详细规格 |
| `AI开发项目文档管理/04-测试方案/平台测试方案.md` | 测试计划（~130 条用例） |
