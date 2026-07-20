---
name: env-credentials-and-config
description: Where to find admin passwords, device serials, port numbers, DB engine — info NOT in code
metadata:
  type: reference
---

# 环境凭据与配置 — 非代码可读信息

以下信息不在代码中，只能通过特定方式获取：

## 管理员密码

- **存储位置**：Django `auth_user` 表（PBKDF2 加密哈希）
- **创建方式**：`python manage.py createsuperuser`（首次）或通过 Django Admin
- **默认值**：项目初始化脚本使用 `admin` / `admin@local` / `admin123`，但这是初始化脚本的参数，不是硬编码密码
- **AI 获取方式**：无法从代码读取。需询问用户或检查 `.env` 中的 `DJANGO_SUPERUSER_*` 变量

## 设备序列号 (DEVICE_SERIAL)

- **配置位置**：`.env` 文件中的 `DEVICE_SERIAL` 变量
- **获取方式**：
  - `cat .env | grep DEVICE_SERIAL`（如果有 .env 文件）
  - `adb devices`（直接查看已连接设备）
  - `curl http://localhost:8765/api/devices/`（从设备池 API 查询）

## 服务端口号

- **定义位置**：`run.py` 文件顶部的 `PORTS` 字典（redis:6379, backend:8765, agentscope:8000, frontend:5173）
- **AI 获取方式**：`Read run.py` 搜索 `PORTS`、或 `python run.py status` 查看运行中端口

## DB_ENGINE

- **配置位置**：`.env` 中的 `DB_ENGINE` 变量，默认值在 `config/settings.py:95`
- **AI 获取方式**：Read `.env` 文件或 Read `config/settings.py` 搜索 `DB_ENGINE`

## 数据库密码

- **配置位置**：`.env` 中的 `DB_PASSWORD` 变量
- **AI 获取方式**：**不可从代码获取。** 检查 `.env` 文件但不打印值；MySQL 用户可通过 `SELECT user,host FROM mysql.user` 查看用户列表
