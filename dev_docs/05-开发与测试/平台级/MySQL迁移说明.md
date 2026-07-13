# MySQL 数据库迁移说明

**迁移日期**: 2026-07-02
**MySQL 版本**: 8.4.4 LTS (via scoop)
**数据库**: android_autotests (utf8mb4)

---

## 1. 环境信息

### MySQL 安装路径
```
C:\Users\zhiyan\scoop\apps\mysql-lts\current\
```

### 数据目录
```
C:\Users\zhiyan\scoop\apps\mysql-lts\current\data\
```

### 配置文件
```
C:\Users\zhiyan\scoop\apps\mysql-lts\current\my.ini
```

### 连接信息
| 项 | 值 |
|----|-----|
| Host | 127.0.0.1 |
| Port | 3306 |
| User | root |
| Password | autotests2026 |
| Database | android_autotests |
| Charset | utf8mb4 |

---

## 2. 启动方式

### 方式 A: 命令行启动（当前使用，不需管理员权限）

```bash
# 后台启动 MySQL
mysqld --console &

# 验证
mysqladmin ping -u root -pautotests2026
# 应输出: mysqld is alive

# 停止
mysqladmin -u root -pautotests2026 shutdown
```

### 方式 B: 注册为 Windows 服务（需管理员权限）

```bash
# 注册服务（只需一次，以管理员运行）
mysqld --install MySQL --defaults-file="C:\Users\zhiyan\scoop\apps\mysql-lts\current\my.ini"

# 启动 / 停止
net start MySQL
net stop MySQL

# 删除服务
sc delete MySQL
```

---

## 3. 以 MySQL 模式启动 Django

### 启动命令

```bash
cd D:\Kahoku\Android-AutoTests

# 设置环境变量（PowerShell）
$env:DB_ENGINE="mysql"
$env:DB_NAME="android_autotests"
$env:DB_USER="root"
$env:DB_PASSWORD="autotests2026"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:PYTHONUTF8="1"

# 启动 Daphne
daphne -p 8765 -b 0.0.0.0 config.asgi:application
```

### CMD 批处理方式

```cmd
set DB_ENGINE=mysql
set DB_NAME=android_autotests
set DB_USER=root
set DB_PASSWORD=autotests2026
set DB_HOST=127.0.0.1
set DB_PORT=3306
set PYTHONUTF8=1
daphne -p 8765 -b 0.0.0.0 config.asgi:application
```

### 回退到 SQLite（如需）

不设置上述环境变量，直接启动即可（默认 DB_ENGINE=sqlite）：
```bash
daphne -p 8765 -b 0.0.0.0 config.asgi:application
```

---

## 4. 迁移记录

### 数据量对比
| 指标 | SQLite (迁移前) | MySQL (迁移后) |
|------|-----------------|----------------|
| 文件大小 | 447 MB | 0.88 MB |
| 表数量 | 28 | 28 |
| 总行数 | 197 | 197 |

> SQLite 的 446 MB 主要是空闲页膨胀，实际数据不到 1 MB。

### 迁移的数据
- auth_user: 2 条 (admin, Aeron)
- ai_agents: 4 条
- ai_conversations: 4 条
- ai_messages: 16 条
- ai_tools: 3 条
- dp_devices: 2 条
- dp_device_locks: 2 条
- el_pages: 3 条
- el_elements: 3 条
- cm_test_cases: 1 条
- cm_test_definitions: 2 条

### 备份文件
- SQLite 原始备份: `data/app.db.backup.20260702_112339` (447 MB)
- 导出的 JSON 数据: `data_migration.json` (25 KB)

---

## 5. 代码变更

### apps/element_locator/models.py
- `UniqueConstraint` 从 `(page, resource_id, text_val, bounds)` 改为 `(page, resource_id, bounds)`
- **原因**: MySQL utf8mb4 下索引上限 3072 字节，`text_val` max_length=2000 导致组合索引达 10808 字节
- **影响**: 去重精度略降（bounds 坐标已能唯一标识同页元素），不影响业务逻辑

### apps/element_locator/migrations/0001_initial.py
- 同步修改 UniqueConstraint 字段列表

---

## 6. 常用管理命令

```bash
# 备份 MySQL
mysqldump -u root -pautotests2026 android_autotests > backup.sql

# 恢复 MySQL
mysql -u root -pautotests2026 android_autotests < backup.sql

# 查看表大小
mysql -u root -pautotests2026 -e "
SELECT table_name, 
       ROUND(data_length/1024/1024, 2) AS data_mb,
       ROUND(index_length/1024/1024, 2) AS index_mb
FROM information_schema.TABLES 
WHERE table_schema = 'android_autotests' 
ORDER BY data_length DESC;"

# 进入 MySQL 控制台
mysql -u root -pautotests2026 android_autotests
```

---

## 7. 注意事项

1. **MySQL 非持久化运行**: 当前以 `mysqld --console` 方式启动，重启电脑后需重新启动
2. **PYTHONUTF8=1**: 处理 emoji 等 4 字节字符时必须设置
3. **Django 服务需重启**: 当前 8765 端口的 Daphne 仍连接 SQLite，需停止后以 MySQL 环境变量重启
4. **SQLite 文件保留**: `data/app.db` 未删除，可随时回退
